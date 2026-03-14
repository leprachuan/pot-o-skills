#!/usr/bin/env python3
"""
TODO CLI for managing TODOs via command line.
"""

import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from todo_manager import TodoManager


def cmd_add(args):
    """Add a new TODO."""
    manager = TodoManager()
    manager.add_todo(
        description=args.description,
        due=args.due,
        labels=args.labels.split(',') if args.labels else None,
        notes=args.notes,
    )
    print(f"✓ Added: {args.description}")


def cmd_complete(args):
    """Complete a TODO."""
    manager = TodoManager()
    if manager.complete_todo(args.description):
        print(f"✓ Completed: {args.description}")
    else:
        print(f"✗ TODO not found: {args.description}")


def cmd_remove(args):
    """Remove a TODO."""
    manager = TodoManager()
    if manager.remove_todo(args.description):
        print(f"✓ Removed: {args.description}")
    else:
        print(f"✗ TODO not found: {args.description}")


def cmd_list(args):
    """List TODOs."""
    manager = TodoManager()
    todos = manager.load_todos()

    if args.filter == 'active':
        todos = [t for t in todos if not t['completed']]
    elif args.filter == 'completed':
        todos = [t for t in todos if t['completed']]

    if not todos:
        print("No TODOs")
        return

    for todo in todos:
        checkbox = '✓' if todo['completed'] else '○'
        line = f"{checkbox} {todo['description']}"
        if todo.get('due'):
            line += f" (due {todo['due']})"
        if todo.get('labels'):
            line += f" [{','.join(todo['labels'])}]"
        print(line)


def cmd_upcoming(args):
    """Show upcoming TODOs."""
    manager = TodoManager()
    todos = manager.get_upcoming()

    if not todos:
        print("No upcoming TODOs")
        return

    print("Upcoming TODOs:")
    for todo in todos:
        print(f"  • {todo['description']} (due {todo['due']})")


def cmd_overdue(args):
    """Show overdue TODOs."""
    manager = TodoManager()
    todos = manager.get_overdue()

    if not todos:
        print("No overdue TODOs")
        return

    print("Overdue TODOs:")
    for todo in todos:
        print(f"  • {todo['description']} (due {todo['due']})")


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
    complete_parser.add_argument('description', help='TODO description')
    complete_parser.set_defaults(func=cmd_complete)

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a TODO')
    remove_parser.add_argument('description', help='TODO description')
    remove_parser.set_defaults(func=cmd_remove)

    # List command
    list_parser = subparsers.add_parser('list', help='List TODOs')
    list_parser.add_argument('filter', nargs='?', default='all', choices=['all', 'active', 'completed'])
    list_parser.set_defaults(func=cmd_list)

    # Upcoming command
    upcoming_parser = subparsers.add_parser('upcoming', help='Show upcoming TODOs')
    upcoming_parser.set_defaults(func=cmd_upcoming)

    # Overdue command
    overdue_parser = subparsers.add_parser('overdue', help='Show overdue TODOs')
    overdue_parser.set_defaults(func=cmd_overdue)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
