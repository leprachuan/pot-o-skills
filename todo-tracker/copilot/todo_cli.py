#!/usr/bin/env python3
"""
TODO CLI for managing TODOs via command line.
All commands accept a TODO ID (e.g. Ta3f7) or the full description.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from todo_manager import TodoManager


def cmd_add(args):
    """Add a new TODO."""
    manager = TodoManager()
    new_id = manager.add_todo(
        description=args.description,
        due=args.due,
        labels=args.labels.split(',') if args.labels else None,
        notes=args.notes,
    )
    print(f"✓ Added [{new_id}]: {args.description}")


def cmd_complete(args):
    """Complete a TODO."""
    manager = TodoManager()
    if manager.complete_todo(args.identifier):
        print(f"✓ Completed: {args.identifier}")
    else:
        print(f"✗ TODO not found: {args.identifier}")


def cmd_remove(args):
    """Remove a TODO."""
    manager = TodoManager()
    if manager.remove_todo(args.identifier):
        print(f"✓ Removed: {args.identifier}")
    else:
        print(f"✗ TODO not found: {args.identifier}")


def cmd_list(args):
    """List TODOs from both GitHub Issues and flat files."""
    source = getattr(args, 'source', 'all')
    include_completed = args.filter in ('all', 'completed')

    if source == 'github':
        from github_todo_provider import GitHubTodoProvider
        provider = GitHubTodoProvider()
        todos = provider.load_github_todos(include_closed=include_completed)
    elif source == 'flat':
        manager = TodoManager()
        todos = manager.load_todos()
    else:
        # Dual-source (default)
        try:
            from github_todo_provider import DualSourceTodoManager
            dual = DualSourceTodoManager()
            todos = dual.load_all_todos(include_completed=include_completed)
        except Exception:
            manager = TodoManager()
            todos = manager.load_todos()

    if args.filter == 'active':
        todos = [t for t in todos if not t.get('completed')]
    elif args.filter == 'completed':
        todos = [t for t in todos if t.get('completed')]

    if not todos:
        print("No TODOs")
        return

    for todo in todos:
        checkbox = '✓' if todo.get('completed') else '○'
        tid = todo.get('id') or '-----'
        src_icon = ''
        if todo.get('source') == 'github':
            src_icon = '🐙 '
        elif todo.get('source') == 'flatfile':
            src_icon = '📄 '
        line = f"{checkbox} {src_icon}[{tid}] {todo['description']}"
        if todo.get('due'):
            line += f" (due {todo['due']})"
        if todo.get('labels'):
            line += f" [{','.join(todo['labels'])}]"
        print(line)


def cmd_note(args):
    """Append a progress note to a TODO."""
    manager = TodoManager()
    if manager.append_note(args.identifier, args.note):
        print(f"✓ Note added to: {args.identifier}")
    else:
        print(f"✗ TODO not found: {args.identifier}")


def cmd_upcoming(args):
    """Show upcoming TODOs."""
    manager = TodoManager()
    todos = manager.get_upcoming()

    if not todos:
        print("No upcoming TODOs")
        return

    print("Upcoming TODOs:")
    for todo in todos:
        tid = todo.get('id') or '-----'
        print(f"  • [{tid}] {todo['description']} (due {todo['due']})")


def cmd_overdue(args):
    """Show overdue TODOs."""
    manager = TodoManager()
    todos = manager.get_overdue()

    if not todos:
        print("No overdue TODOs")
        return

    print("Overdue TODOs:")
    for todo in todos:
        tid = todo.get('id') or '-----'
        print(f"  • [{tid}] {todo['description']} (due {todo['due']})")


def cmd_backfill_ids(args):
    """Assign IDs to all TODOs that don't have one yet."""
    manager = TodoManager()
    assigned = manager.backfill_ids()
    if not assigned:
        print("All TODOs already have IDs")
        return
    for desc, tid in assigned:
        print(f"  {tid} ← {desc}")
    print(f"✓ Assigned {len(assigned)} IDs")


def main():
    parser = argparse.ArgumentParser(description='TODO management')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add a TODO')
    add_parser.add_argument('description', help='TODO description')
    add_parser.add_argument('--due', help='Due date in format YYYY-MM-DD (defaults to 10:00 if no time given) or YYYY-MM-DD HH:MM')
    add_parser.add_argument('--labels', help='Labels (comma-separated)')
    add_parser.add_argument('--notes', help='Additional notes')
    add_parser.set_defaults(func=cmd_add)

    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Complete a TODO')
    complete_parser.add_argument('identifier', help='TODO ID (e.g. Ta3f7) or description')
    complete_parser.set_defaults(func=cmd_complete)

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a TODO')
    remove_parser.add_argument('identifier', help='TODO ID (e.g. Ta3f7) or description')
    remove_parser.set_defaults(func=cmd_remove)

    # Note command
    note_parser = subparsers.add_parser('note', help='Append a progress note to a TODO')
    note_parser.add_argument('identifier', help='TODO ID (e.g. Ta3f7) or description')
    note_parser.add_argument('note', help='Progress note to append')
    note_parser.set_defaults(func=cmd_note)

    # List command
    list_parser = subparsers.add_parser('list', help='List TODOs')
    list_parser.add_argument('filter', nargs='?', default='all', choices=['all', 'active', 'completed'])
    list_parser.add_argument('--source', choices=['all', 'github', 'flat'], default='all',
                             help='Source: all (GitHub+flat, default), github, flat')
    list_parser.set_defaults(func=cmd_list)

    # Upcoming command
    upcoming_parser = subparsers.add_parser('upcoming', help='Show upcoming TODOs')
    upcoming_parser.set_defaults(func=cmd_upcoming)

    # Overdue command
    overdue_parser = subparsers.add_parser('overdue', help='Show overdue TODOs')
    overdue_parser.set_defaults(func=cmd_overdue)

    # Backfill IDs command
    backfill_parser = subparsers.add_parser('backfill-ids', help='Assign IDs to TODOs without one')
    backfill_parser.set_defaults(func=cmd_backfill_ids)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
