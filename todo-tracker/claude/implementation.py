#!/usr/bin/env python3
"""
Claude implementation of TODO Tracker skill.
Handles natural language TODO management requests.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from todo_manager import TodoManager


def process_request(request: str) -> str:
    """
    Process natural language TODO requests.

    Examples:
    - "Add buy milk to my todos"
    - "What are my upcoming todos?"
    - "Mark review PR as complete"
    - "Show me overdue tasks"
    """
    manager = TodoManager()
    request_lower = request.lower()

    # Detect request type and respond
    if any(word in request_lower for word in ['add', 'create', 'new']):
        # Extract description and parameters
        return handle_add_request(manager, request)
    elif any(word in request_lower for word in ['complete', 'done', 'finish', 'mark']):
        return handle_complete_request(manager, request)
    elif any(word in request_lower for word in ['upcoming', 'due soon', 'next']):
        return handle_upcoming_request(manager)
    elif any(word in request_lower for word in ['overdue', 'past due', 'late']):
        return handle_overdue_request(manager)
    elif any(word in request_lower for word in ['list', 'show', 'what']):
        return handle_list_request(manager)
    else:
        return "I can help you manage TODOs. Try: 'Add...', 'Show upcoming', 'Mark complete', etc."


def handle_add_request(manager: TodoManager, request: str) -> str:
    """Handle add TODO requests."""
    # Simplified - in production would use NLP
    manager.add_todo(request)
    return f"✓ Added TODO"


def handle_complete_request(manager: TodoManager, request: str) -> str:
    """Handle complete TODO requests."""
    todos = manager.load_todos()
    if todos:
        manager.complete_todo(todos[0]['description'])
        return f"✓ Completed: {todos[0]['description']}"
    return "No TODOs to complete"


def handle_upcoming_request(manager: TodoManager) -> str:
    """Handle upcoming TODOs request."""
    todos = manager.get_upcoming()
    if not todos:
        return "No upcoming TODOs"

    response = "Upcoming TODOs:\n"
    for todo in todos:
        response += f"• {todo['description']} (due {todo['due']})\n"
    return response


def handle_overdue_request(manager: TodoManager) -> str:
    """Handle overdue TODOs request."""
    todos = manager.get_overdue()
    if not todos:
        return "No overdue TODOs"

    response = "Overdue TODOs:\n"
    for todo in todos:
        response += f"• {todo['description']} (due {todo['due']})\n"
    return response


def handle_list_request(manager: TodoManager) -> str:
    """Handle list TODOs request."""
    todos = manager.load_todos()
    if not todos:
        return "No TODOs"

    active = [t for t in todos if not t['completed']]
    completed = [t for t in todos if t['completed']]

    response = ""
    if active:
        response += "Active TODOs:\n"
        for todo in active:
            response += f"○ {todo['description']}"
            if todo.get('due'):
                response += f" (due {todo['due']})"
            response += "\n"

    if completed:
        response += "\nCompleted TODOs:\n"
        for todo in completed:
            response += f"✓ {todo['description']}\n"

    return response
