"""
canvas_functions.py — Gemini function definitions for Live Canvas skill.

Provides function declarations and implementations for use with Gemini's
function calling API. Import this module to get the function declarations
and the execution dispatcher.
"""
import sys
import os
import json
from typing import Any

# Add claude implementation to path
_HERE = os.path.dirname(os.path.abspath(__file__))
_CLAUDE_IMPL = os.path.normpath(os.path.join(_HERE, "../../claude/implementation"))
sys.path.insert(0, _CLAUDE_IMPL)


# ── Gemini function declarations ──────────────────────────────────────────────

CANVAS_FUNCTION_DECLARATIONS = [
    {
        "name": "canvas_render",
        "description": "Push a component tree to the live canvas for display in the browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Canvas session ID"},
                "components": {"type": "string", "description": "JSON-encoded component tree array"},
            },
            "required": ["components"],
        },
    },
    {
        "name": "canvas_render_template",
        "description": "Render a built-in canvas template (progress_board, data_dashboard, config_form, plan_view).",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Canvas session ID"},
                "template_name": {
                    "type": "string",
                    "enum": ["progress_board", "data_dashboard", "config_form", "plan_view"],
                    "description": "Name of the template",
                },
                "template_data": {"type": "string", "description": "JSON-encoded template data dict"},
            },
            "required": ["template_name", "template_data"],
        },
    },
    {
        "name": "canvas_update",
        "description": "Partially update a component node on the canvas by its id.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Canvas session ID"},
                "node_id": {"type": "string", "description": "ID of the component to update"},
                "changes": {"type": "string", "description": "JSON-encoded dict of changes to apply"},
            },
            "required": ["node_id", "changes"],
        },
    },
    {
        "name": "canvas_clear",
        "description": "Clear all components from the canvas.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Canvas session ID"},
            },
        },
    },
    {
        "name": "canvas_open",
        "description": "Open the canvas in the browser (calls xdg-open).",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Canvas session ID"},
            },
        },
    },
    {
        "name": "canvas_wait_for_action",
        "description": "Block until the user clicks a button or submits a form on the canvas.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {"type": "string", "description": "Canvas session ID"},
                "timeout": {"type": "integer", "description": "Max seconds to wait (default 60)", "default": 60},
            },
        },
    },
]


# ── Function executor ──────────────────────────────────────────────────────────

_canvas_instances: dict = {}


def _get_canvas(session_id: str = None):
    from canvas import Canvas
    key = session_id or "default"
    if key not in _canvas_instances:
        _canvas_instances[key] = Canvas(session_id=key)
    return _canvas_instances[key]


def execute_canvas_function(name: str, args: dict) -> Any:
    """Execute a canvas function by name with the given args dict."""
    session_id = args.get("session_id")
    canvas = _get_canvas(session_id)

    if name == "canvas_render":
        components = json.loads(args.get("components", "[]"))
        canvas.render(components)
        return {"status": "ok", "session_id": canvas.session_id}

    elif name == "canvas_render_template":
        template_name = args["template_name"]
        template_data = json.loads(args.get("template_data", "{}"))
        canvas.render_template(template_name, template_data)
        return {"status": "ok", "template": template_name, "session_id": canvas.session_id}

    elif name == "canvas_update":
        canvas.update(args["node_id"], json.loads(args.get("changes", "{}")))
        return {"status": "ok"}

    elif name == "canvas_clear":
        canvas.clear()
        return {"status": "ok"}

    elif name == "canvas_open":
        canvas.open()
        return {"status": "ok", "url": canvas.viewer_url()}

    elif name == "canvas_wait_for_action":
        timeout = int(args.get("timeout", 60))
        action = canvas.wait_for_action(timeout=timeout)
        return action

    else:
        return {"error": f"Unknown function: {name}"}
