#!/usr/bin/env python3
"""
GitHub Kanban Board Server
Fetches GitHub issues and serves them as a kanban board with agent/due-date filtering.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import click
from flask import Flask, jsonify, request
from flask_cors import CORS
from github import Github
from dateutil.parser import parse as parse_date

app = Flask(__name__)
CORS(app)

# Config loading
def load_config():
    """Load configuration from config.json or environment variables."""
    config_path = Path(__file__).parent.parent / "config.json"

    config = {
        "repository": "leprachuan/fosterbot-home",
        "port": 8888,
        "host": "127.0.0.1",
        "default_agents": [],
    }

    if config_path.exists():
        with open(config_path) as f:
            file_config = json.load(f)
            config.update(file_config)

    # Environment variables override config file
    if os.environ.get("KANBAN_REPO"):
        config["repository"] = os.environ.get("KANBAN_REPO")
    if os.environ.get("KANBAN_PORT"):
        config["port"] = int(os.environ.get("KANBAN_PORT"))
    if os.environ.get("KANBAN_HOST"):
        config["host"] = os.environ.get("KANBAN_HOST")

    return config

CONFIG = load_config()

# Global state
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_NAME = CONFIG["repository"]
GITHUB_CLIENT = None


def init_github(token: Optional[str] = None):
    """Initialize GitHub client."""
    global GITHUB_CLIENT
    if not token:
        token = GITHUB_TOKEN
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set")
    GITHUB_CLIENT = Github(token)


def extract_labels_data(labels: List) -> Dict:
    """Extract agent, due date, urgency, and priority from issue labels."""
    data = {
        "agent": None,
        "due_date": None,
        "due_date_str": None,
        "priority": "normal",
        "urgency": "normal",  # urgent or normal
        "status": "todo",
        "all_labels": [label.name for label in labels],
    }

    for label in labels:
        name = label.name.lower()

        # Parse agent: prefix
        if name.startswith("agent:"):
            data["agent"] = name.replace("agent:", "").strip()

        # Parse due: prefix
        elif name.startswith("due:"):
            try:
                due_str = name.replace("due:", "").strip()
                due_date = parse_date(due_str)
                data["due_date"] = due_date.isoformat()
                data["due_date_str"] = due_date.strftime("%Y-%m-%d")
            except:
                pass

        # Parse urgency
        elif name in ["urgent", "urgency:urgent", "urgency:high"]:
            data["urgency"] = "urgent"

        # Parse priority
        elif name in ["priority:critical", "priority:high", "priority:medium", "priority:low"]:
            data["priority"] = name.replace("priority:", "")

        # Parse status
        elif name in ["status:todo", "status:in-progress", "status:ai-active", "status:pending-review", "status:done"]:
            data["status"] = name.replace("status:", "")

    return data


def issue_to_dict(issue) -> Dict:
    """Convert GitHub issue to kanban card dict."""
    labels_data = extract_labels_data(issue.labels)

    return {
        "id": issue.number,
        "title": issue.title,
        "url": issue.html_url,
        "body": issue.body or "",
        "state": issue.state,
        "agent": labels_data["agent"],
        "due_date": labels_data["due_date"],
        "due_date_str": labels_data["due_date_str"],
        "priority": labels_data["priority"],
        "urgency": labels_data["urgency"],
        "status": labels_data["status"],
        "labels": labels_data["all_labels"],
        "created_at": issue.created_at.isoformat(),
        "updated_at": issue.updated_at.isoformat(),
        "assignee": issue.assignee.login if issue.assignee else None,
    }


@app.route("/api/issues", methods=["GET"])
def get_issues():
    """Fetch all open issues from repository with optional filtering."""
    try:
        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issues = repo.get_issues(state="open")

        cards = [issue_to_dict(issue) for issue in issues]

        # Apply filters
        date_from = request.args.get("date_from")  # YYYY-MM-DD
        date_to = request.args.get("date_to")      # YYYY-MM-DD
        urgency_filter = request.args.get("urgency")  # urgent or normal

        if date_from or date_to:
            filtered_cards = []
            for card in cards:
                if not card["due_date_str"]:
                    continue
                card_date = card["due_date_str"]
                if date_from and card_date < date_from:
                    continue
                if date_to and card_date > date_to:
                    continue
                filtered_cards.append(card)
            cards = filtered_cards

        if urgency_filter:
            cards = [c for c in cards if c["urgency"] == urgency_filter]

        # Group by status (todo, in-progress, done)
        columns = {
            "todo": [c for c in cards if c["status"] == "todo"],
            "in-progress": [c for c in cards if c["status"] == "in-progress"],
            "done": [c for c in cards if c["status"] == "done"],
        }

        # Get unique agents and urgency levels for filtering
        agents = sorted(set(c["agent"] for c in cards if c["agent"]))
        urgencies = sorted(set(c["urgency"] for c in cards))

        return jsonify(
            {
                "success": True,
                "columns": columns,
                "agents": agents,
                "urgencies": urgencies,
                "total": len(cards),
                "filters_applied": bool(date_from or date_to or urgency_filter),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<int:issue_num>", methods=["GET"])
def get_issue(issue_num: int):
    """Fetch a single issue."""
    try:
        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)
        return jsonify({"success": True, "issue": issue_to_dict(issue)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<int:issue_num>/details", methods=["GET"])
def get_issue_details(issue_num: int):
    """Fetch issue details including comments."""
    try:
        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)

        # Get comments
        comments = []
        for comment in issue.get_comments():
            comments.append({
                "author": comment.user.login,
                "avatar": comment.user.avatar_url,
                "created_at": comment.created_at.isoformat(),
                "updated_at": comment.updated_at.isoformat(),
                "body": comment.body,
            })

        issue_data = issue_to_dict(issue)
        issue_data["comments"] = comments
        issue_data["comment_count"] = len(comments)

        return jsonify({"success": True, "issue": issue_data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<int:issue_num>/status", methods=["POST"])
def update_issue_status(issue_num: int):
    """Update issue status by adding/removing status label."""
    try:
        data = request.json
        new_status = data.get("status")  # todo, in-progress, done

        if new_status not in ["todo", "in-progress", "ai-active", "pending-review", "done"]:
            return jsonify({"success": False, "error": "Invalid status"}), 400

        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)

        # Remove old status labels
        old_labels = [l.name for l in issue.labels if not l.name.startswith("status:")]

        # Add new status label
        new_labels = old_labels + [f"status:{new_status}"]

        issue.set_labels(*new_labels)

        return jsonify({"success": True, "issue": issue_to_dict(issue)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<int:issue_num>/comment", methods=["POST"])
def post_comment(issue_num: int):
    """Post a comment to an issue."""
    try:
        data = request.json
        comment_text = data.get("body", "").strip()

        if not comment_text:
            return jsonify({"success": False, "error": "Comment cannot be empty"}), 400

        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)
        comment = issue.create_comment(comment_text)

        return jsonify({
            "success": True,
            "comment": {
                "author": comment.user.login,
                "avatar": comment.user.avatar_url,
                "created_at": comment.created_at.isoformat(),
                "body": comment.body,
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<int:issue_num>/dispatch", methods=["POST"])
def dispatch_issue(issue_num: int):
    """Dispatch issue to an agent (logs the intent)."""
    try:
        data = request.json
        agent_name = data.get("agent", "").strip()

        if not agent_name:
            return jsonify({"success": False, "error": "Agent not specified"}), 400

        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)

        # In a real implementation, you would send this to your agent system
        # For now, we'll log it and return success
        dispatch_message = f"[DISPATCH] Issue #{issue_num} dispatched to agent: {agent_name}\nTitle: {issue.title}\nBody: {issue.body}"

        return jsonify({
            "success": True,
            "agent": agent_name,
            "issue_num": issue_num,
            "issue_title": issue.title,
            "message": f"Issue dispatched to {agent_name}"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/config", methods=["GET"])
def get_config_endpoint():
    """Get server configuration."""
    return jsonify(
        {
            "repo": REPO_NAME,
            "default_agents": CONFIG.get("default_agents", []),
            "port": CONFIG.get("port"),
            "host": CONFIG.get("host"),
        }
    )


@app.route("/", methods=["GET"])
def index():
    """Serve the kanban board HTML."""
    html_path = os.path.join(os.path.dirname(__file__), "..", "assets", "index.html")
    with open(html_path, "r") as f:
        return f.read()


@click.command()
@click.option("--repo", default=None, help="GitHub repository (owner/name)")
@click.option("--port", type=int, default=None, help="Server port")
@click.option("--host", default=None, help="Server host")
@click.option("--token", envvar="GITHUB_TOKEN", help="GitHub API token")
def main(repo: str, port: int, host: str, token: str):
    """Start the kanban board server."""
    global REPO_NAME

    # Use CLI args if provided, otherwise use loaded CONFIG
    REPO_NAME = repo or CONFIG.get("repository")
    final_port = port or CONFIG.get("port", 8888)
    final_host = host or CONFIG.get("host", "127.0.0.1")

    if not token:
        click.echo(
            "Error: GITHUB_TOKEN not set. Set via --token or GITHUB_TOKEN env var",
            err=True,
        )
        return

    init_github(token)

    click.echo(f"🍀 Kanban Board Server")
    click.echo(f"   Repository: {REPO_NAME}")
    click.echo(f"   Listening on http://{final_host}:{final_port}")
    click.echo(f"   Press Ctrl+C to stop")

    app.run(host=final_host, port=final_port, debug=True)


if __name__ == "__main__":
    main()
