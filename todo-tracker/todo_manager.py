#!/usr/bin/env python3
"""
Core TODO management - handles individual TODO files in ACTIVE/ and COMPLETED/ directories.
Each TODO is a separate file, with filename as the description.
"""

import os
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


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

    def load_todos(self) -> List[Dict]:
        """Load TODOs from individual files in ACTIVE/ and COMPLETED/ directories."""
        todos = []

        # Load ACTIVE todos
        if self.active_dir.exists():
            for todo_file in sorted(self.active_dir.iterdir()):
                if todo_file.is_file():
                    todos.append(self._parse_todo_file(todo_file, completed=False))

        # Load COMPLETED todos
        if self.completed_dir.exists():
            for todo_file in sorted(self.completed_dir.iterdir()):
                if todo_file.is_file():
                    todos.append(self._parse_todo_file(todo_file, completed=True))

        return todos

    def _parse_todo_file(self, file_path: Path, completed: bool) -> Dict:
        """Parse a TODO file and extract metadata (supports both WebUI and legacy formats)."""
        description = file_path.name
        content = file_path.read_text().strip() if file_path.exists() else ""

        todo = {
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

    def add_todo(self, description: str, due: Optional[str] = None, labels: Optional[List[str]] = None, notes: Optional[str] = None) -> None:
        """Add a new TODO as a file in ACTIVE directory using WebUI format."""
        todo_file = self.active_dir / description
        content = ""

        # WebUI format: DUE: YYYY-MM-DD HH:MM
        if due:
            # Convert various date formats to DUE: YYYY-MM-DD HH:MM format
            due_str = due.strip()
            # If no time provided, default to 10:00
            if ' ' not in due_str:
                due_str = f"{due_str} 10:00"
            content += f"DUE: {due_str}\n"

        # WebUI format: LABELS: {LABEL1},{LABEL2}
        if labels:
            content += f"LABELS: {{{','.join(labels)}}}\n"

        # Add notes/details if provided
        if notes:
            content += f"\nDETAILS: {notes}\n"

        todo_file.write_text(content.strip())

    def reschedule_todo(self, description: str, new_due: str) -> bool:
        """Update the due date of an ACTIVE todo. new_due must be MM/DD/YYYY."""
        active_file = self.active_dir / description
        if not active_file.exists():
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

    def update_todo(self, description: str, new_due: Optional[str] = None, new_notes: Optional[str] = None) -> bool:
        """Update due date and/or notes of an ACTIVE todo. new_due must be MM/DD/YYYY."""
        active_file = self.active_dir / description
        if not active_file.exists():
            return False
        content = active_file.read_text()
        # Preserve labels
        labels = []
        label_match = re.search(r'\{([^}]+)\}', content)
        if label_match:
            labels = [l.strip() for l in label_match.group(1).split(',')]
        # Rebuild file from scratch using DUE:/LABELS: format
        new_content = ""
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
                if (re.match(r'\(due [^)]+\)', stripped) or
                        re.match(r'\{[^}]+\}', stripped) or
                        re.match(r'DUE:\s*\S+', stripped) or
                        re.match(r'LABELS:\s*\S+', stripped)):
                    continue
                new_content += line + "\n"
        active_file.write_text(new_content.strip())
        return True

    def append_note(self, description: str, note: str) -> bool:
        """Append a timestamped progress note to an ACTIVE todo."""
        active_file = self.active_dir / description
        if not active_file.exists():
            return False
        content = active_file.read_text().rstrip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        content += f"\n[{timestamp}] {note}"
        active_file.write_text(content + "\n")
        return True

    def complete_todo(self, description: str) -> bool:
        """Move a TODO from ACTIVE to COMPLETED, stamping completion date."""
        active_file = self.active_dir / description
        if active_file.exists():
            content = active_file.read_text().rstrip()
            completed_date = datetime.now().strftime("%Y-%m-%d")
            content = content + f"\n\nCOMPLETED: {completed_date}\n"
            completed_file = self.completed_dir / description
            completed_file.write_text(content)
            active_file.unlink()
            return True
        return False

    def remove_todo(self, description: str) -> bool:
        """Remove a TODO file."""
        active_file = self.active_dir / description
        completed_file = self.completed_dir / description

        removed = False
        if active_file.exists():
            active_file.unlink()
            removed = True
        if completed_file.exists():
            completed_file.unlink()
            removed = True

        return removed

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
