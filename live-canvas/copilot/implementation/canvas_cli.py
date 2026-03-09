"""
canvas_cli.py — Copilot CLI wrapper for Live Canvas skill.
Provides a command-line interface to push renders and templates to the canvas.

Usage:
    python3 canvas_cli.py render --session abc123 --components '[...]'
    python3 canvas_cli.py template --session abc123 --name progress_board --data '{...}'
    python3 canvas_cli.py update --session abc123 --node-id step-1 --changes '{"status":"done"}'
    python3 canvas_cli.py clear --session abc123
    python3 canvas_cli.py open --session abc123
    python3 canvas_cli.py wait-action --session abc123 --timeout 60
"""
import sys
import os
import json
import argparse

# Add claude implementation to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_CLAUDE_IMPL = os.path.normpath(os.path.join(_HERE, "../../claude/implementation"))
sys.path.insert(0, _CLAUDE_IMPL)

from canvas import Canvas


def main():
    parser = argparse.ArgumentParser(description="Live Canvas CLI")
    parser.add_argument("command", choices=["render", "template", "update", "clear", "open", "wait-action"])
    parser.add_argument("--session", default=None, help="Session ID (auto-generated if not given)")
    parser.add_argument("--components", default=None, help="JSON component tree (for render)")
    parser.add_argument("--name", default=None, help="Template name (for template)")
    parser.add_argument("--data", default=None, help="JSON template data (for template)")
    parser.add_argument("--node-id", default=None, help="Node ID (for update)")
    parser.add_argument("--changes", default=None, help="JSON changes (for update)")
    parser.add_argument("--timeout", type=int, default=60, help="Timeout in seconds (for wait-action)")

    args = parser.parse_args()

    canvas = Canvas(session_id=args.session)

    if args.command == "render":
        components = json.loads(args.components or "[]")
        canvas.render(components)
        print(f"Rendered {len(components)} components to session {canvas.session_id}")

    elif args.command == "template":
        if not args.name:
            print("ERROR: --name required for template command", file=sys.stderr)
            sys.exit(1)
        data = json.loads(args.data or "{}")
        canvas.render_template(args.name, data)
        print(f"Rendered template '{args.name}' to session {canvas.session_id}")

    elif args.command == "update":
        if not args.node_id:
            print("ERROR: --node-id required for update command", file=sys.stderr)
            sys.exit(1)
        changes = json.loads(args.changes or "{}")
        canvas.update(args.node_id, changes)
        print(f"Updated node '{args.node_id}'")

    elif args.command == "clear":
        canvas.clear()
        print(f"Cleared canvas session {canvas.session_id}")

    elif args.command == "open":
        canvas.open()
        print(f"Opened canvas: {canvas.viewer_url()}")

    elif args.command == "wait-action":
        print(f"Waiting for user action (timeout: {args.timeout}s)…", flush=True)
        action = canvas.wait_for_action(timeout=args.timeout)
        print(json.dumps(action, indent=2))


if __name__ == "__main__":
    main()
