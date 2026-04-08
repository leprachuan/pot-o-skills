#!/usr/bin/env python3
"""
GitHub Issues TODO provider — reads TODOs from GitHub Issues (fosterbot-home repo)
and merges with flat-file TODOs for a unified view.

Usage:
    from github_todo_provider import GitHubTodoProvider
    provider = GitHubTodoProvider()
    todos = provider.load_todos()          # GitHub Issues + flat files (deduplicated)
    gh_todos = provider.load_github_todos() # GitHub Issues only
"""

import json
import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Optional


class GitHubTodoProvider:
    """Fetch TODOs from GitHub Issues in the fosterbot-home repo."""

    DEFAULT_REPO = "leprachuan/fosterbot-home"
    LABEL_FILTER = "todo"

    def __init__(self, repo: Optional[str] = None):
        self.repo = repo or os.environ.get("TODO_GITHUB_REPO", self.DEFAULT_REPO)

    def _run_gh(self, args: List[str], timeout: int = 30) -> Optional[str]:
        """Run a gh CLI command and return stdout, or None on failure."""
        cmd = ["gh"] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def load_github_todos(self, include_closed: bool = False) -> List[Dict]:
        """Load TODOs from GitHub Issues labelled 'todo'."""
        state = "all" if include_closed else "open"
        raw = self._run_gh([
            "issue", "list",
            "--repo", self.repo,
            "--label", self.LABEL_FILTER,
            "--state", state,
            "--json", "number,title,body,labels,state,createdAt,closedAt,assignees",
            "--limit", "200",
        ])
        if not raw:
            return []

        try:
            issues = json.loads(raw)
        except json.JSONDecodeError:
            return []

        todos = []
        for issue in issues:
            labels = [l["name"] for l in issue.get("labels", [])]
            due = self._extract_due_from_body(issue.get("body", ""))
            completed = issue.get("state", "").upper() == "CLOSED"

            todos.append({
                "id": f"GH-{issue['number']}",
                "description": issue["title"],
                "completed": completed,
                "section": "Completed" if completed else "Active",
                "due": due,
                "labels": [l for l in labels if l != self.LABEL_FILTER],
                "notes": self._extract_notes_from_body(issue.get("body", "")),
                "source": "github",
                "github_number": issue["number"],
                "github_url": f"https://github.com/{self.repo}/issues/{issue['number']}",
            })

        return todos

    def _extract_due_from_body(self, body: str) -> Optional[str]:
        """Extract due date from issue body."""
        if not body:
            return None
        # Match **Due:** date pattern
        m = re.search(r'\*\*Due:\*\*\s*(.+)', body)
        if m:
            return m.group(1).strip()
        # Match DUE: date pattern (raw format)
        m = re.search(r'DUE:\s*(.+)', body)
        if m:
            return m.group(1).strip()
        return None

    def _extract_notes_from_body(self, body: str) -> str:
        """Extract meaningful notes from issue body (skip metadata)."""
        if not body:
            return ""
        lines = []
        for line in body.split("\n"):
            stripped = line.strip()
            # Skip metadata lines
            if any(stripped.startswith(p) for p in [
                "**Migrated", "📅", "**Due:", "**Details:",
                "---", "_Original file:", "<details>", "</details>",
                "<summary>", "```", "DUE:", "LABELS:", "ID:",
            ]):
                continue
            if stripped:
                lines.append(stripped)
        return "\n".join(lines)

    def create_issue(
        self,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        due: Optional[str] = None,
    ) -> Optional[int]:
        """Create a GitHub Issue as a TODO. Returns issue number or None."""
        if labels is None:
            labels = []
        if self.LABEL_FILTER not in labels:
            labels.append(self.LABEL_FILTER)

        body_parts = []
        if due:
            body_parts.append(f"📅 **Due:** {due}")
        if body:
            body_parts.append(body)
        full_body = "\n\n".join(body_parts) if body_parts else ""

        raw = self._run_gh([
            "issue", "create",
            "--repo", self.repo,
            "--title", title,
            "--body", full_body,
            "--label", ",".join(labels),
        ])
        if raw:
            # gh returns the URL — extract issue number
            m = re.search(r'/issues/(\d+)', raw)
            if m:
                return int(m.group(1))
        return None

    def close_issue(self, issue_number: int) -> bool:
        """Close a GitHub Issue (mark TODO as complete)."""
        result = self._run_gh([
            "issue", "close",
            "--repo", self.repo,
            str(issue_number),
        ])
        return result is not None


class DualSourceTodoManager:
    """
    Unified TODO manager that reads from both GitHub Issues and flat files.
    GitHub Issues are the primary source; flat files are the fallback.
    Deduplication is by title match.
    """

    def __init__(self):
        # Lazy import to avoid circular dependency
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from todo_manager import TodoManager

        self.flat_manager = TodoManager()
        self.github_provider = GitHubTodoProvider()

    def load_all_todos(self, include_completed: bool = False) -> List[Dict]:
        """Load TODOs from both sources, deduplicated by title."""
        # Try GitHub first (primary)
        gh_todos = []
        try:
            gh_todos = self.github_provider.load_github_todos(
                include_closed=include_completed
            )
        except Exception:
            pass

        # Load flat-file TODOs (fallback)
        flat_todos = self.flat_manager.load_todos()
        if not include_completed:
            flat_todos = [t for t in flat_todos if not t["completed"]]

        # Tag flat-file TODOs with source
        for t in flat_todos:
            t["source"] = "flatfile"

        # Deduplicate: GitHub wins on title match
        gh_titles = {t["description"].lower().strip() for t in gh_todos}
        unique_flat = [
            t for t in flat_todos
            if t["description"].lower().strip() not in gh_titles
        ]

        return gh_todos + unique_flat

    def load_active(self) -> List[Dict]:
        """Load only active (non-completed) TODOs from both sources."""
        return [t for t in self.load_all_todos() if not t.get("completed")]

    def summary(self) -> str:
        """Return a human-readable summary of all TODOs."""
        todos = self.load_active()
        if not todos:
            return "No active TODOs"

        gh_count = sum(1 for t in todos if t.get("source") == "github")
        flat_count = sum(1 for t in todos if t.get("source") == "flatfile")

        lines = [f"📋 **{len(todos)} active TODOs** (GitHub: {gh_count}, flat-file: {flat_count})\n"]
        for t in todos:
            tid = t.get("id", "---")
            src = "🐙" if t.get("source") == "github" else "📄"
            line = f"  {src} [{tid}] {t['description']}"
            if t.get("due"):
                line += f" (due {t['due']})"
            lines.append(line)

        return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="GitHub + flat-file TODO provider")
    parser.add_argument(
        "command",
        choices=["list", "github-only", "flat-only", "summary", "create"],
        help="Command to run",
    )
    parser.add_argument("--title", help="Title for create command")
    parser.add_argument("--due", help="Due date for create command")
    parser.add_argument("--labels", help="Comma-separated labels for create command")
    parser.add_argument(
        "--include-completed",
        action="store_true",
        help="Include completed TODOs",
    )
    args = parser.parse_args()

    if args.command == "summary":
        mgr = DualSourceTodoManager()
        print(mgr.summary())

    elif args.command == "list":
        mgr = DualSourceTodoManager()
        todos = mgr.load_all_todos(include_completed=args.include_completed)
        for t in todos:
            src = "GH" if t.get("source") == "github" else "FF"
            check = "✓" if t.get("completed") else "○"
            tid = t.get("id", "---")
            line = f"{check} [{src}:{tid}] {t['description']}"
            if t.get("due"):
                line += f" (due {t['due']})"
            print(line)

    elif args.command == "github-only":
        provider = GitHubTodoProvider()
        todos = provider.load_github_todos(include_closed=args.include_completed)
        for t in todos:
            check = "✓" if t.get("completed") else "○"
            print(f"{check} [GH-{t['github_number']}] {t['description']}")

    elif args.command == "flat-only":
        from todo_manager import TodoManager
        mgr = TodoManager()
        todos = mgr.load_todos()
        if not args.include_completed:
            todos = [t for t in todos if not t["completed"]]
        for t in todos:
            check = "✓" if t.get("completed") else "○"
            tid = t.get("id", "---")
            print(f"{check} [FF:{tid}] {t['description']}")

    elif args.command == "create":
        if not args.title:
            print("Error: --title required for create command")
            exit(1)
        provider = GitHubTodoProvider()
        labels = args.labels.split(",") if args.labels else []
        num = provider.create_issue(args.title, labels=labels, due=args.due)
        if num:
            print(f"✅ Created GitHub Issue #{num}: {args.title}")
        else:
            print("❌ Failed to create GitHub Issue")
            exit(1)
