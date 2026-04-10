#!/usr/bin/env python3
"""
Core TODO management - handles individual TODO files in ACTIVE/ and COMPLETED/ directories.
Each TODO is a separate file, with filename as the description.
"""

import json
import os
import random
import re
import string
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

GITHUB_REPO = os.environ.get("TODO_GITHUB_REPO", "leprachuan/fosterbot-home")
GITHUB_LABEL = "todo"


class TodoManager:
    """Manage TODOs stored as individual files in ACTIVE/ and COMPLETED/ directories."""

    def __init__(self):
        """Initialize TodoManager with configurable TODO directory path."""
        # Priority 1: agents.json todo_dir for the current agent
        todo_dir = self._get_todo_dir_from_agents_json()

        # Priority 2: TODO_DIR environment variable
        if not todo_dir:
            todo_dir = os.environ.get("TODO_DIR", "")

        if todo_dir:
            self.todo_dir = Path(todo_dir)
        else:
            # Auto-detect standard locations
            possible_locations = [
                Path("/opt/fosterbot-home/TODOs"),                          # flipkey-cli (LXC container)
                Path.home() / "PycharmProjects" / "notes_and_code" / "TODOs",  # MacBook
                Path.home() / "Documents" / "TODOs",
                Path.home() / "TODOs",
            ]
            for loc in possible_locations:
                if loc.exists():
                    self.todo_dir = loc
                    break
            else:
                # Default to first location
                self.todo_dir = possible_locations[0]

        # Create directories if they don't exist
        self.active_dir = self.todo_dir / "ACTIVE"
        self.completed_dir = self.todo_dir / "COMPLETED"
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.completed_dir.mkdir(parents=True, exist_ok=True)

        self._github_repo = os.environ.get("TODO_GITHUB_REPO", GITHUB_REPO)
        self._github_label = GITHUB_LABEL

    # --- GitHub Issues helpers ---

    def _run_gh(self, args: List[str], timeout: int = 30) -> Optional[str]:
        """Run gh CLI and return stdout or None on failure."""
        try:
            r = subprocess.run(["gh"] + args, capture_output=True, text=True, timeout=timeout)
            return r.stdout.strip() if r.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    def _extract_due_from_body(self, body: str) -> Optional[str]:
        """Extract due date string from GitHub Issue body."""
        if not body:
            return None
        for pattern in [r"\*\*Due:\*\*\s*(.+)", r"DUE:\s*(.+)"]:
            m = re.search(pattern, body)
            if m:
                return m.group(1).strip().split("\n")[0].strip()
        return None

    def _load_from_github(self, include_completed: bool = True) -> Optional[List[Dict]]:
        """Load TODOs from GitHub Issues. Returns list of dicts or None on failure."""
        state = "all" if include_completed else "open"
        raw = self._run_gh([
            "issue", "list", "--repo", self._github_repo,
            "--label", self._github_label, "--state", state,
            "--json", "number,title,body,labels,state,createdAt,closedAt",
            "--limit", "200",
        ])
        if not raw:
            return None
        try:
            issues = json.loads(raw)
        except json.JSONDecodeError:
            return None

        todos = []
        for issue in issues:
            labels = [l["name"] for l in issue.get("labels", []) if l["name"] != self._github_label]
            completed = issue.get("state", "").upper() == "CLOSED"
            body = issue.get("body", "") or ""
            notes_lines = []
            for line in body.split("\n"):
                s = line.strip()
                if s and not any(s.startswith(p) for p in [
                    "**Migrated", "📅", "**Due:", "DUE:", "LABELS:", "ID:",
                    "---", "_Original file:", "<details>", "</details>",
                    "<summary>", "```",
                ]):
                    notes_lines.append(s)

            todos.append({
                "id": f"GH-{issue['number']}",
                "description": issue["title"],
                "completed": completed,
                "section": "Completed" if completed else "Active",
                "due": self._extract_due_from_body(body),
                "labels": labels,
                "notes": "\n".join(notes_lines),
                "source": "github",
                "github_number": issue["number"],
            })
        return todos

    def _get_todo_dir_from_agents_json(self) -> str:
        """Look up todo_dir from agents.json for the current AGENT_NAME. Fails silently."""
        import json
        agent_name = os.environ.get("AGENT_NAME", "")
        if not agent_name:
            return ""

        agents_json_paths = [
            os.environ.get("AGENTS_JSON", ""),
            "/opt/n8n-copilot-shim-dev/agents.json",
            "/opt/n8n-copilot-shim/agents.json",
            "/opt/agents.json",
        ]

        for path in agents_json_paths:
            if not path:
                continue
            try:
                with open(path) as f:
                    data = json.load(f)
                for agent in data.get("agents", []):
                    if agent.get("name") == agent_name:
                        return agent.get("todo_dir", "")
            except (OSError, json.JSONDecodeError, KeyError):
                continue

        return ""

    # --- ID generation and resolution ---

    def _generate_id(self) -> str:
        """Generate a unique T + 4 lowercase-alphanumeric ID."""
        existing = self._get_all_ids()
        chars = string.ascii_lowercase + string.digits
        for _ in range(100):
            new_id = "T" + "".join(random.choices(chars, k=4))
            if new_id not in existing:
                return new_id
        raise RuntimeError("Failed to generate unique TODO ID")

    def _get_all_ids(self) -> set:
        """Scan all TODO files and return set of existing IDs."""
        ids = set()
        for directory in [self.active_dir, self.completed_dir]:
            if directory.exists():
                for f in directory.iterdir():
                    if f.is_file():
                        # Check filename prefix first (new format)
                        m = re.match(r'^\[(T[a-z0-9]{4})\] ', f.name)
                        if m:
                            ids.add(m.group(1))
                            continue
                        # Fall back to file content (legacy format)
                        first_line = f.read_text().split("\n", 1)[0]
                        m = re.match(r"^ID:\s*(T[a-z0-9]{4})$", first_line)
                        if m:
                            ids.add(m.group(1))
        return ids

    def _find_by_id(
        self, todo_id: str
    ) -> Optional[Tuple[Path, bool]]:
        """Find a TODO file by ID. Returns (path, completed) or None."""
        todo_id = todo_id if todo_id[0] == "T" else "T" + todo_id[1:]
        prefix = f"[{todo_id}] "
        for directory, completed in [
            (self.active_dir, False),
            (self.completed_dir, True),
        ]:
            if not directory.exists():
                continue
            for f in directory.iterdir():
                if f.is_file():
                    # Check filename prefix first (new format)
                    if f.name.lower().startswith(prefix.lower()):
                        return (f, completed)
                    # Fall back to file content (legacy format)
                    first_line = f.read_text().split("\n", 1)[0]
                    m = re.match(r"^ID:\s*(T[a-z0-9]{4})$", first_line)
                    if m and m.group(1) == todo_id:
                        return (f, completed)
        return None

    def _is_todo_id(self, s: str) -> bool:
        """Check if a string looks like a TODO ID (T + 4 alphanumeric)."""
        return bool(re.match(r"^T[a-z0-9]{4}$", s, re.IGNORECASE))

    def resolve_active(self, identifier: str) -> Optional[Path]:
        """Resolve an ID or description to an active TODO file path."""
        if self._is_todo_id(identifier):
            result = self._find_by_id(identifier.lower())
            if result and not result[1]:
                return result[0]
            return None
        # Exact match (legacy filenames without prefix)
        exact = self.active_dir / identifier
        if exact.exists():
            return exact
        # Search for [Txxx] prefixed filename matching the description
        for f in self.active_dir.iterdir():
            if f.is_file():
                m = re.match(r'^\[T[a-z0-9]{4}\] (.+)$', f.name)
                if m and m.group(1) == identifier:
                    return f
        return None

    def resolve_any(
        self, identifier: str
    ) -> Optional[Tuple[Path, bool]]:
        """Resolve an ID or description to any TODO. Returns (path, completed)."""
        if self._is_todo_id(identifier):
            return self._find_by_id(identifier.lower())
        for directory, completed in [
            (self.active_dir, False),
            (self.completed_dir, True),
        ]:
            # Exact match (legacy filenames without prefix)
            f = directory / identifier
            if f.exists():
                return (f, completed)
            # Search for [Txxx] prefixed filename
            for f in directory.iterdir():
                if f.is_file():
                    m = re.match(r'^\[T[a-z0-9]{4}\] (.+)$', f.name)
                    if m and m.group(1) == identifier:
                        return (f, completed)
        return None

    def get_id_for_todo(self, description: str) -> Optional[str]:
        """Get the ID of a TODO by its description."""
        for directory in [self.active_dir, self.completed_dir]:
            f = directory / description
            if f.exists():
                first_line = f.read_text().split("\n", 1)[0]
                m = re.match(r"^ID:\s*(T[a-z0-9]{4})$", first_line)
                if m:
                    return m.group(1)
        return None

    def backfill_ids(self) -> List[Tuple[str, str]]:
        """Assign IDs to all TODOs that don't have one, and rename files to [ID] format.
        Returns [(original_desc, id)]."""
        assigned = []
        for directory in [self.active_dir, self.completed_dir]:
            if not directory.exists():
                continue
            for f in sorted(directory.iterdir()):
                if not f.is_file():
                    continue
                name = f.name
                # Already has [Txxx] prefix in filename — skip
                if re.match(r'^\[T[a-z0-9]{4}\] ', name):
                    continue
                content = f.read_text()
                first_line = content.split("\n", 1)[0]
                id_match = re.match(r"^ID:\s*(T[a-z0-9]{4})$", first_line)
                if id_match:
                    # Has ID in content but not in filename — rename to add prefix
                    todo_id = id_match.group(1)
                else:
                    # No ID anywhere — generate one and write to content
                    todo_id = self._generate_id()
                    content = f"ID: {todo_id}\n{content}"
                    f.write_text(content)
                new_name = f"[{todo_id}] {name}"
                f.rename(directory / new_name)
                assigned.append((name, todo_id))
        return assigned

    def load_todos(self) -> List[Dict]:
        """Load TODOs. Primary: GitHub Issues. Fallback: flat files."""
        # Try GitHub Issues first
        gh_todos = self._load_from_github()
        if gh_todos is not None:
            return gh_todos

        # Flat-file fallback
        todos = []
        if self.active_dir.exists():
            for todo_file in sorted(self.active_dir.iterdir()):
                if todo_file.is_file():
                    todos.append(self._parse_todo_file(todo_file, completed=False))
        if self.completed_dir.exists():
            for todo_file in sorted(self.completed_dir.iterdir()):
                if todo_file.is_file():
                    todos.append(self._parse_todo_file(todo_file, completed=True))
        return todos

    def _parse_todo_file(self, file_path: Path, completed: bool) -> Dict:
        """Parse a TODO file and extract metadata (supports both WebUI and legacy formats)."""
        name = file_path.name
        # Extract ID and clean description from filename prefix [Txxx] Description
        m = re.match(r'^\[(T[a-z0-9]{4})\] (.+)$', name)
        if m:
            file_id = m.group(1)
            description = m.group(2)
        else:
            file_id = None
            description = name
        content = file_path.read_text().strip() if file_path.exists() else ""

        todo = {
            'id': file_id,
            'description': description,
            'completed': completed,
            'section': 'Completed' if completed else 'Active',
            'due': None,
            'labels': [],
            'notes': '',
        }

        lines = content.split('\n')
        notes_lines = []

        for line in lines:
            line = line.strip()

            # Parse ID: Txxxx (legacy content-based ID — prefer filename-based id)
            if re.match(r'^ID:\s*T[a-z0-9]{4}$', line):
                if todo['id'] is None:
                    todo['id'] = line.replace('ID:', '').strip()
                continue

            # Parse WebUI format: DUE: YYYY-MM-DD HH:MM
            if line.startswith('DUE:'):
                todo['due'] = line.replace('DUE:', '').strip()
            # Parse WebUI format: LABELS: {LABEL1},{LABEL2}
            elif line.startswith('LABELS:'):
                labels_str = line.replace('LABELS:', '').strip()
                label_match = re.search(r'\{([^}]+)\}', labels_str)
                if label_match:
                    todo['labels'] = [l.strip() for l in label_match.group(1).split(',')]
            # Parse DETAILS: or other metadata
            elif line.startswith('DETAILS:'):
                notes_lines.append(line.replace('DETAILS:', '').strip())
            # Legacy format: (due ...)
            elif line.startswith('(due'):
                due_match = re.search(r'\(due ([^\)]+)\)', line)
                if due_match:
                    todo['due'] = due_match.group(1)
            # Legacy format: {LABEL1,LABEL2}
            elif line.startswith('{') and line.endswith('}'):
                label_match = re.search(r'\{([^}]+)\}', line)
                if label_match:
                    todo['labels'] = [l.strip() for l in label_match.group(1).split(',')]
            # Collect remaining lines as notes
            elif line and not line.startswith('ITEMS') and not line.startswith('RESEARCH'):
                notes_lines.append(line)

        # Join remaining lines as notes
        if notes_lines:
            todo['notes'] = '\n'.join(notes_lines)

        return todo

    def add_todo(self, description: str, due: Optional[str] = None, labels: Optional[List[str]] = None, notes: Optional[str] = None) -> str:
        """Add a new TODO. Primary: GitHub Issue. Fallback: flat file. Returns the assigned ID."""
        # Try GitHub Issue first
        body_parts = []
        if due:
            due_str = due.strip()
            if " " not in due_str:
                due_str = f"{due_str} 10:00"
            body_parts.append(f"📅 **Due:** {due_str}")
        if notes:
            body_parts.append(notes)
        body = "\n\n".join(body_parts)

        gh_labels = list(labels or []) + [self._github_label]
        result = self._run_gh([
            "issue", "create", "--repo", self._github_repo,
            "--title", description, "--body", body,
            "--label", ",".join(gh_labels),
        ])
        if result:
            m = re.search(r"/issues/(\d+)", result)
            if m:
                return f"GH-{m.group(1)}"

        # Flat-file fallback
        new_id = self._generate_id()
        filename = f"[{new_id}] {description}"
        todo_file = self.active_dir / filename
        content = f"ID: {new_id}\n"
        if due:
            due_str = due.strip()
            if " " not in due_str:
                due_str = f"{due_str} 10:00"
            content += f"DUE: {due_str}\n"
        if labels:
            content += f"LABELS: {{{','.join(labels)}}}\n"
        if notes:
            content += f"\nDETAILS: {notes}\n"
        todo_file.write_text(content.strip())
        return new_id

    def reschedule_todo(self, identifier: str, new_due: str) -> bool:
        """Update the due date of an ACTIVE todo. Accepts ID or description."""
        active_file = self.resolve_active(identifier)
        if not active_file:
            return False
        content = active_file.read_text()
        # Replace existing due date in any format with new DUE: format
        if re.search(r'DUE:\s*\S+', content):
            content = re.sub(r'DUE:\s*\S+', f"DUE: {new_due}", content)
        elif re.search(r'\(due [^)]+\)', content):
            content = re.sub(r'\(due [^)]+\)', f"DUE: {new_due}", content)
        else:
            # No existing due date — prepend it
            content = f"DUE: {new_due}\n" + content
        active_file.write_text(content)
        return True

    def update_todo(self, identifier: str, new_due: Optional[str] = None, new_notes: Optional[str] = None) -> bool:
        """Update due date and/or notes of an ACTIVE todo. Accepts ID or description."""
        active_file = self.resolve_active(identifier)
        if not active_file:
            return False
        content = active_file.read_text()
        # Preserve labels
        labels = []
        label_match = re.search(r'\{([^}]+)\}', content)
        if label_match:
            labels = [l.strip() for l in label_match.group(1).split(',')]
        # Rebuild file from scratch using DUE:/LABELS: format
        new_content = ""
        # Preserve ID line
        id_match = re.match(r'^(ID:\s*T[a-z0-9]{4})\n', content)
        if id_match:
            new_content += id_match.group(1) + "\n"
        if new_due:
            new_content += f"DUE: {new_due}\n"
        else:
            # Keep existing due date in new format
            existing = re.search(r'DUE:\s*(\S+)', content) or re.search(r'\(due ([^)]+)\)', content)
            if existing:
                new_content += f"DUE: {existing.group(1)}\n"
        if labels:
            new_content += f"LABELS: {{{','.join(labels)}}}\n"
        if new_notes is not None:
            if new_notes.strip():
                new_content += new_notes.strip() + "\n"
        else:
            # Keep existing notes (lines that aren't metadata)
            for line in content.splitlines():
                stripped = line.strip()
                if (re.match(r'^ID:\s*T[a-z0-9]{4}$', stripped) or
                        re.match(r'\(due [^)]+\)', stripped) or
                        re.match(r'\{[^}]+\}', stripped) or
                        re.match(r'DUE:\s*\S+', stripped) or
                        re.match(r'LABELS:\s*\S+', stripped)):
                    continue
                new_content += line + "\n"
        active_file.write_text(new_content.strip())
        return True

    def append_note(self, identifier: str, note: str) -> bool:
        """Append a timestamped progress note to an ACTIVE todo. Accepts ID or description."""
        active_file = self.resolve_active(identifier)
        if not active_file:
            return False
        content = active_file.read_text().rstrip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        content += f"\n[{timestamp}] {note}"
        active_file.write_text(content + "\n")
        return True

    def complete_todo(self, identifier: str) -> bool:
        """Complete a TODO. Primary: close GitHub Issue. Fallback: move flat file."""
        # If it's a GitHub ID (GH-NNN), close the issue directly
        gh_match = re.match(r"^GH-(\d+)$", identifier, re.IGNORECASE)
        if gh_match:
            return self._run_gh([
                "issue", "close", "--repo", self._github_repo, gh_match.group(1)
            ]) is not None

        # Search GitHub Issues by title match
        gh_todos = self._load_from_github(include_completed=False)
        if gh_todos:
            for t in gh_todos:
                if t["description"].lower() == identifier.lower():
                    return self._run_gh([
                        "issue", "close", "--repo", self._github_repo,
                        str(t["github_number"])
                    ]) is not None

        # Flat-file fallback
        active_file = self.resolve_active(identifier)
        if active_file:
            content = active_file.read_text().rstrip()
            completed_date = datetime.now().strftime("%Y-%m-%d")
            content = content + f"\n\nCOMPLETED: {completed_date}\n"
            completed_file = self.completed_dir / active_file.name
            completed_file.write_text(content)
            active_file.unlink()
            return True
        return False

    def remove_todo(self, identifier: str) -> bool:
        """Remove a TODO file. Accepts ID or description."""
        result = self.resolve_any(identifier)
        if result:
            result[0].unlink()
            return True
        return False

    def get_upcoming(self) -> List[Dict]:
        """Get TODOs due soon (not completed, with due date in future)."""
        todos = self.load_todos()
        upcoming = []
        now = datetime.now()

        for todo in todos:
            if todo['completed']:
                continue
            if not todo['due']:
                continue

            try:
                due_dt = datetime.fromisoformat(todo['due'].split()[0])
                if due_dt > now:
                    upcoming.append(todo)
            except (ValueError, IndexError):
                pass

        return sorted(upcoming, key=lambda t: t['due'])

    def get_overdue(self) -> List[Dict]:
        """Get overdue TODOs (not completed, with due date in past)."""
        todos = self.load_todos()
        overdue = []
        now = datetime.now()

        for todo in todos:
            if todo['completed']:
                continue
            if not todo['due']:
                continue

            try:
                due_dt = datetime.fromisoformat(todo['due'].split()[0])
                if due_dt <= now:
                    overdue.append(todo)
            except (ValueError, IndexError):
                pass

        return sorted(overdue, key=lambda t: t['due'])
