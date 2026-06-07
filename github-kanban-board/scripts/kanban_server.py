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
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
from github import Github
from dateutil.parser import parse as parse_date

# Wee Orchestrator background-task dispatch
AGENTS_CONFIG_PATH = Path(os.environ.get("WEE_AGENTS_CONFIG", "/mnt/nas/Agents/agents.json"))
WEE_API_BASE = os.environ.get("WEE_API_BASE", "https://127.0.0.1:8000")
WEE_API_KEY = os.environ.get("WEE_API_KEY") or os.environ.get("API_SHARED_KEY")


def get_agent_dispatch_config(agent_name: str) -> Dict:
    """Look up an agent's runtime/model/permission settings from agents.json."""
    with open(AGENTS_CONFIG_PATH) as f:
        agents_config = json.load(f)

    for agent in agents_config.get("agents", []):
        if agent.get("name") == agent_name:
            return {
                "runtime": agent.get("primary_runtime", "copilot"),
                "model": agent.get("primary_model", "auto"),
                "permission_mode": agent.get("permissions", {}).get("mode", "restricted"),
            }

    raise ValueError(f"Agent '{agent_name}' not found in agents.json")


def dispatch_background_task(agent_name: str, prompt: str, timeout: int = 3600) -> Dict:
    """Launch a background agent task via the Wee Orchestrator API."""
    if not WEE_API_KEY:
        raise RuntimeError("No Wee Orchestrator API key configured (set WEE_API_KEY)")

    cfg = get_agent_dispatch_config(agent_name)

    payload = {
        "prompt": prompt,
        "agent": agent_name,
        "runtime": cfg["runtime"],
        "model": cfg["model"],
        "permission_mode": cfg["permission_mode"],
        "timeout": timeout,
    }

    response = requests.post(
        f"{WEE_API_BASE}/api/v1/background-tasks",
        json=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer shared_{WEE_API_KEY}",
        },
        verify=False,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()

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

    # A closed issue is always "done" on the board, regardless of status label
    status = "done" if issue.state == "closed" else labels_data["status"]

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
        "status": status,
        "labels": labels_data["all_labels"],
        "created_at": issue.created_at.isoformat(),
        "updated_at": issue.updated_at.isoformat(),
        "assignee": issue.assignee.login if issue.assignee else None,
    }


@app.route("/api/issues", methods=["GET"])
def get_issues():
    """Fetch all issues from repository with optional filtering. Closed issues show as 'done'."""
    try:
        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issues = repo.get_issues(state="all")

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
            "ai-active": [c for c in cards if c["status"] == "ai-active"],
            "pending-review": [c for c in cards if c["status"] == "pending-review"],
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
    """Update issue status or labels."""
    try:
        data = request.json
        new_status = data.get("status")
        new_labels = data.get("labels")

        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)

        if new_status:
            if new_status not in ["todo", "in-progress", "ai-active", "pending-review", "done"]:
                return jsonify({"success": False, "error": "Invalid status"}), 400

            if new_status == "done":
                # "Done" means closed on GitHub - no status label needed
                issue.edit(state="closed")
            else:
                # Reopen if moving out of done/closed
                if issue.state == "closed":
                    issue.edit(state="open")

                # Remove old status labels
                old_labels = [l.name for l in issue.labels if not l.name.startswith("status:")]
                # Add new status label
                updated_labels = old_labels + [f"status:{new_status}"]
                issue.set_labels(*updated_labels)

        elif new_labels:
            # Update with new labels
            issue.set_labels(*new_labels)

        return jsonify({"success": True, "issue": issue_to_dict(issue)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/issues/<int:issue_num>/close", methods=["POST"])
def close_issue(issue_num: int):
    """Close a GitHub issue."""
    try:
        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)
        issue.edit(state="closed")

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
    """Dispatch issue to an agent as a real background task via the Wee Orchestrator API."""
    try:
        data = request.json
        agent_name = data.get("agent", "").strip()

        if not agent_name:
            return jsonify({"success": False, "error": "Agent not specified"}), 400

        repo = GITHUB_CLIENT.get_repo(REPO_NAME)
        issue = repo.get_issue(issue_num)

        # Move the issue to "ai-active" on the board immediately so it shows
        # up in the right column as soon as the agent is dispatched.
        old_labels = [l.name for l in issue.labels if not l.name.startswith("status:")]
        issue.set_labels(*(old_labels + ["status:ai-active"]))

        prompt = (
            f"Work on GitHub issue #{issue_num} in {REPO_NAME} ({issue.html_url}).\n\n"
            f"## STEP 1 — Setup (do this FIRST before any other work)\n\n"
            f"Fetch the current issue:\n"
            f"  gh issue view {issue_num} --repo {REPO_NAME} --json title,body,labels,comments\n\n"
            f"Ensure the 'status:ai-active' label is set (it should already be set, but confirm):\n"
            f"  gh issue edit {issue_num} --repo {REPO_NAME} --add-label 'status:ai-active'\n\n"
            f"## STEP 2 — Do the Work\n\n"
            f"Complete the requested work described in the issue. Post progress comments as you go:\n"
            f"  gh issue comment {issue_num} --repo {REPO_NAME} --body 'Your progress update here'\n\n"
            f"## STEP 3 — Completion (MANDATORY — do not skip or forget this step)\n\n"
            f"When finished (or when you need human input), you MUST do ALL of the following IN ORDER:\n\n"
            f"1. Post a summary comment:\n"
            f"   gh issue comment {issue_num} --repo {REPO_NAME} --body 'Summary of what was done...'\n\n"
            f"2. Swap labels — remove ai-active, add pending-review:\n"
            f"   gh issue edit {issue_num} --repo {REPO_NAME} --remove-label 'status:ai-active' --add-label 'status:pending-review'\n\n"
            f"3. Verify the label swap succeeded:\n"
            f"   gh issue view {issue_num} --repo {REPO_NAME} --json labels\n"
            f"   Confirm 'status:pending-review' is present and 'status:ai-active' is gone.\n\n"
            f"CRITICAL: Step 3 is non-negotiable. The kanban board tracks this via GitHub labels. "
            f"If you complete the work but forget to swap the labels, the card stays stuck in AI Active "
            f"forever and Foster will not know it is ready for review."
        )

        task = dispatch_background_task(agent_name, prompt)

        return jsonify({
            "success": True,
            "agent": agent_name,
            "issue_num": issue_num,
            "issue_title": issue.title,
            "task_id": task.get("task_id"),
            "session_id": task.get("session_id"),
            "message": f"Issue dispatched to {agent_name} (task {task.get('task_id')})"
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
