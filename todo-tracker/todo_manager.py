#!/usr/bin/env python3
"""
Core TODO management - handles loading, parsing, and saving TODOs.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class TodoManager:
    """Manage TODOs stored in markdown files."""

    def __init__(self):
        """Initialize TodoManager with configurable TODO file path."""
        # Allow TODO_FILE to be set via environment variable
        self.todo_file = Path(os.environ.get("TODO_FILE", ""))

        # If not set, auto-detect
        if not self.todo_file or not self.todo_file.exists():
            possible_locations = [
                Path("/opt/fosterbot-home/TODOs.md"),
                Path.home() / "Documents" / "TODOs.md",
                Path.home() / "TODOs.md",
            ]
            for loc in possible_locations:
                if loc.exists():
                    self.todo_file = loc
                    break
            else:
                # Default to first location
                self.todo_file = possible_locations[0]

    def load_todos(self) -> List[Dict]:
        """Load TODOs from markdown file."""
        if not self.todo_file.exists():
            return []

        todos = []
        content = self.todo_file.read_text()
        lines = content.split('\n')

        current_section = None
        current_todo = None

        for line in lines:
            # Section headers
            if line.startswith('## '):
                current_section = line[3:].strip()
                continue

            # TODO line
            if line.strip().startswith('[ ]') or line.strip().startswith('[X]'):
                if current_todo:
                    todos.append(current_todo)

                completed = line.strip().startswith('[X]')
                text = line.strip()[4:].strip()

                current_todo = {
                    'description': text,
                    'completed': completed,
                    'section': current_section,
                    'notes': '',
                    'due': None,
                }

                # Parse due date and labels
                self._parse_todo_line(text, current_todo)

            # Notes (indented lines under TODOs)
            elif current_todo and line.startswith('    '):
                current_todo['notes'] += line[4:] + '\n'

        if current_todo:
            todos.append(current_todo)

        return todos

    def _parse_todo_line(self, text: str, todo: Dict) -> None:
        """Parse due date and labels from TODO line."""
        # Extract due date: (due YYYY-MM-DD) or (due YYYY-MM-DD HH:MM:SS)
        import re

        due_match = re.search(r'\(due ([^)]+)\)', text)
        if due_match:
            todo['due'] = due_match.group(1)

        # Extract labels: {LABEL1,LABEL2}
        label_match = re.search(r'\{([^}]+)\}', text)
        if label_match:
            todo['labels'] = label_match.group(1).split(',')
        else:
            todo['labels'] = []

    def save_todos(self, todos: List[Dict]) -> None:
        """Save TODOs to markdown file."""
        self.todo_file.parent.mkdir(parents=True, exist_ok=True)

        # Group by section
        sections = {}
        for todo in todos:
            section = todo.get('section', 'Active')
            if section not in sections:
                sections[section] = []
            sections[section].append(todo)

        # Build markdown
        lines = ['# TODOs', '']

        for section in ['Active', 'Completed']:
            if section not in sections:
                continue

            lines.append(f'## {section}')
            lines.append('')

            for todo in sections[section]:
                checkbox = '[X]' if todo.get('completed') else '[ ]'
                desc = todo.get('description', '')
                due = todo.get('due')
                labels = todo.get('labels', [])

                line = f'{checkbox} {desc}'
                if due:
                    line += f' (due {due})'
                if labels:
                    line += f' {{{",".join(labels)}}}'

                lines.append(line)

                if todo.get('notes'):
                    for note_line in todo['notes'].strip().split('\n'):
                        lines.append(f'    {note_line}')

                lines.append('')

        self.todo_file.write_text('\n'.join(lines))

    def add_todo(self, description: str, due: Optional[str] = None, labels: Optional[List[str]] = None, notes: Optional[str] = None) -> None:
        """Add a new TODO."""
        todos = self.load_todos()
        todos.append({
            'description': description,
            'completed': False,
            'section': 'Active',
            'due': due,
            'labels': labels or [],
            'notes': notes or '',
        })
        self.save_todos(todos)

    def complete_todo(self, description: str) -> bool:
        """Mark a TODO as completed."""
        todos = self.load_todos()
        for todo in todos:
            if todo['description'] == description:
                todo['completed'] = True
                todo['section'] = 'Completed'
                self.save_todos(todos)
                return True
        return False

    def remove_todo(self, description: str) -> bool:
        """Remove a TODO."""
        todos = self.load_todos()
        new_todos = [t for t in todos if t['description'] != description]
        if len(new_todos) < len(todos):
            self.save_todos(new_todos)
            return True
        return False

    def get_upcoming(self) -> List[Dict]:
        """Get TODOs due soon."""
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
        """Get overdue TODOs."""
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
