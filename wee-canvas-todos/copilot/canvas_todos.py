#!/usr/bin/env python3
"""
Wee Canvas TODO Viewer — launches an interactive TODO board on Wee Canvas.

Usage:
    python3 canvas_todos.py [--session-id SESSION] [--height HEIGHT] [--once]

Modes:
    Default: Open canvas, refresh every 30s, handle user actions (add/complete/status)
    --once:  Render once and exit (for embedding in other canvas workflows)
"""

import argparse
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Locate the todo-tracker module
_SKILLS_DIRS = [
    "/opt/skills/todo-tracker",
    "/opt/pot-o-skills/todo-tracker",
]
_CANVAS_DIRS = [
    "/opt/n8n-copilot-shim",
    "/opt/n8n-copilot-shim-dev",
]

def _add_paths():
    for d in _SKILLS_DIRS:
        if Path(d).exists():
            sys.path.insert(0, d)
            break
    for d in _CANVAS_DIRS:
        if Path(d).exists():
            sys.path.insert(0, d)
            break

_add_paths()


def load_todos():
    """Load TODOs from dual source (GitHub + flat files)."""
    try:
        from github_todo_provider import DualSourceTodoManager
        dm = DualSourceTodoManager()
        todos = dm.load_all_todos(include_completed=True)
        return todos
    except Exception as e:
        print(f"[WARN] DualSourceTodoManager failed: {e}, falling back to flat files")

    try:
        from todo_manager import TodoManager
        tm = TodoManager()
        todos = tm.load_todos()
        for t in todos:
            t["source"] = "flatfile"
        return todos
    except Exception as e:
        print(f"[ERROR] TodoManager failed: {e}")
        return []


def action_complete(identifier: str):
    """Mark a TODO as complete via CLI."""
    for d in _SKILLS_DIRS:
        cli = Path(d) / "copilot" / "todo_cli.py"
        if cli.exists():
            subprocess.run(
                [sys.executable, str(cli), "complete", identifier],
                capture_output=True,
            )
            return
    print(f"[WARN] Could not find todo_cli.py to complete: {identifier}")


def action_add(description: str, due: str = None, labels: list = None):
    """Add a new TODO via CLI."""
    for d in _SKILLS_DIRS:
        cli = Path(d) / "copilot" / "todo_cli.py"
        if cli.exists():
            cmd = [sys.executable, str(cli), "add", description]
            if due:
                cmd += ["--due", due]
            if labels:
                cmd += ["--labels", ",".join(labels)]
            subprocess.run(cmd, capture_output=True)
            return
    print(f"[WARN] Could not find todo_cli.py to add: {description}")


def action_status(identifier: str, new_status: str):
    """Change TODO status. Maps kanban drops to CLI operations."""
    if new_status in ("completed", "done"):
        action_complete(identifier)
    else:
        print(f"[INFO] Status change to '{new_status}' for {identifier} — not yet implemented in CLI")


def render_todos(canvas, todos: list, height: int = 700) -> str:
    """Push the TODO HTML to the canvas and return the component ID."""
    sys.path.insert(0, str(Path(__file__).parent))
    from todo_html import generate_todo_html

    last_updated = datetime.now().strftime("Updated %H:%M:%S")
    html = generate_todo_html(todos, last_updated=last_updated)
    cid = canvas.push_html(html, height=height, component_id="wee-todos")
    return cid


def run(session_id: str = None, height: int = 700, once: bool = False,
        refresh_interval: int = 30):
    """Main loop: open canvas, render, refresh, handle actions."""
    from canvas import Canvas

    c = Canvas(session_id=session_id)
    c.open()

    print(f"[wee-canvas-todos] Canvas opened: {c.viewer_url()}")
    print(f"[wee-canvas-todos] Session ID: {c.session_id}")

    todos = load_todos()
    render_todos(c, todos, height=height)
    print(f"[wee-canvas-todos] Rendered {len(todos)} TODOs")

    if once:
        print(f"[wee-canvas-todos] --once mode, exiting")
        return c.session_id

    last_render = time.time()
    needs_refresh = False

    while True:
        try:
            # Wait for an action with short timeout to allow periodic refresh
            action = c.wait_for_action(timeout=min(refresh_interval, 10))
            if action and action.get("type") == "action":
                payload = action.get("payload", {})
                act = payload.get("action")
                print(f"[wee-canvas-todos] Action received: {payload}")

                if act == "complete":
                    action_complete(payload.get("id", ""))
                    needs_refresh = True
                elif act == "add":
                    action_add(
                        payload.get("description", ""),
                        due=payload.get("due"),
                        labels=payload.get("labels", []),
                    )
                    needs_refresh = True
                elif act == "status":
                    action_status(payload.get("id", ""), payload.get("status", ""))
                    needs_refresh = True

        except Exception:
            pass

        now = time.time()
        if needs_refresh or (now - last_render) >= refresh_interval:
            todos = load_todos()
            render_todos(c, todos, height=height)
            print(f"[wee-canvas-todos] Refreshed: {len(todos)} TODOs @ {datetime.now().strftime('%H:%M:%S')}")
            last_render = now
            needs_refresh = False

    return c.session_id


def main():
    parser = argparse.ArgumentParser(description="Wee Canvas TODO Viewer")
    parser.add_argument("--session-id", help="Canvas session ID (auto-generated if not set)")
    parser.add_argument("--height", type=int, default=700, help="Canvas iframe height (default: 700)")
    parser.add_argument("--once", action="store_true", help="Render once and exit")
    parser.add_argument("--refresh", type=int, default=30, help="Refresh interval in seconds (default: 30)")
    args = parser.parse_args()

    session_id = run(
        session_id=args.session_id,
        height=args.height,
        once=args.once,
        refresh_interval=args.refresh,
    )
    print(f"[wee-canvas-todos] Done. Session: {session_id}")


if __name__ == "__main__":
    main()
