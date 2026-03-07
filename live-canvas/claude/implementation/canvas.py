"""
Canvas — agent-facing API for the Live Canvas skill.

Usage:
    from canvas import Canvas

    c = Canvas()                              # auto-generates session ID
    c.render_template("progress_board", {...})
    c.open()                                  # opens browser
    action = c.wait_for_action(timeout=60)    # blocks until user clicks
"""
import asyncio
import json
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse, parse_qs

import os

SERVER_PORT = int(os.environ.get("CANVAS_PORT", 18793))
SERVER_HOST = os.environ.get("CANVAS_HOST", "localhost")
SERVER_MODULE = Path(__file__).parent / "canvas_server.py"
WS_BASE = f"ws://{SERVER_HOST}:{SERVER_PORT}/ws"
HTTP_BASE = f"http://{SERVER_HOST}:{SERVER_PORT}"


def _is_server_running() -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", SERVER_PORT))
        s.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False


class Canvas:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._ensure_server()

    # ── Server lifecycle ─────────────────────────────────────────────────────

    def _ensure_server(self):
        """Start canvas_server.py if not already running."""
        if not _is_server_running():
            subprocess.Popen(
                [sys.executable, str(SERVER_MODULE)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # Wait up to 3 seconds for server to start
            for _ in range(12):
                time.sleep(0.25)
                if _is_server_running():
                    break

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _ws_url(self) -> str:
        return f"{WS_BASE}?session={self.session_id}"

    def _send(self, message: dict):
        """Send a single message to the server and close."""
        asyncio.run(self._async_send(message))

    async def _async_send(self, message: dict):
        import websockets
        async with websockets.connect(self._ws_url()) as ws:
            await ws.send(json.dumps(message))

    # ── Public API ────────────────────────────────────────────────────────────

    def render(self, components: list):
        """Push a full component tree to the canvas."""
        self._send({"type": "render", "components": components, "session_id": self.session_id})

    def render_template(self, name: str, data: dict):
        """Render a built-in template. Templates: progress_board, data_dashboard, config_form, plan_view."""
        components = _build_template(name, data)
        self.render(components)

    def update(self, node_id: str, changes: dict):
        """Partially update a component node by its id."""
        self._send({"type": "update", "node_id": node_id, "changes": changes})

    def clear(self):
        """Clear all components from the canvas."""
        self._send({"type": "clear", "session_id": self.session_id})

    def open(self):
        """Open the canvas viewer in the default browser."""
        url = f"{HTTP_BASE}?session={self.session_id}"
        try:
            subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            try:
                subprocess.Popen(["open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except FileNotFoundError:
                print(f"Open in browser: {url}")

    def wait_for_action(self, timeout: int = 60) -> dict:
        """Block until the user clicks a button or submits a form. Returns the action dict."""
        return asyncio.run(self._async_wait_for_action(timeout))

    async def _async_wait_for_action(self, timeout: int) -> dict:
        import websockets

        ws_url = self._ws_url()
        deadline = time.time() + timeout

        async with websockets.connect(ws_url) as ws:
            # Register as an action watcher
            await ws.send(json.dumps({"type": "subscribe_actions", "session_id": self.session_id}))

            while time.time() < deadline:
                remaining = max(1.0, deadline - time.time())
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=min(remaining, 5.0))
                    data = json.loads(raw)
                    if data.get("type") == "action":
                        return data
                except asyncio.TimeoutError:
                    continue
                except Exception:
                    break

        return {"type": "timeout"}


# ── Template builders ────────────────────────────────────────────────────────

def _status_icon(status: str) -> str:
    icons = {"done": "✅", "running": "🔄", "pending": "⏳", "error": "❌", "skip": "⏭️"}
    return icons.get(status, "•")


def _build_template(name: str, data: dict) -> list:
    builders = {
        "progress_board": _tpl_progress_board,
        "data_dashboard": _tpl_data_dashboard,
        "config_form": _tpl_config_form,
        "plan_view": _tpl_plan_view,
    }
    builder = builders.get(name)
    if not builder:
        raise ValueError(f"Unknown template: {name!r}. Available: {list(builders)}")
    return builder(data)


def _tpl_progress_board(data: dict) -> list:
    """
    data = {
        "title": str,
        "steps": [{"name": str, "status": "done"|"running"|"pending"|"error"}],
        "elapsed": str  (optional)
    }
    """
    steps = data.get("steps", [])
    done_count = sum(1 for s in steps if s.get("status") == "done")
    pct = int(done_count / max(len(steps), 1) * 100)

    cols = {"done": [], "running": [], "pending": []}
    for i, step in enumerate(steps):
        status = step.get("status", "pending")
        col_key = status if status in cols else "pending"
        cols[col_key].append({
            "type": "card",
            "id": f"step-{i}",
            "title": f"{_status_icon(status)} {step['name']}",
            "status": status,
        })

    header = [
        {"type": "heading", "level": 2, "text": data.get("title", "Task Progress"), "id": "board-title"},
        {"type": "progress", "label": f"Overall — {done_count}/{len(steps)} steps", "pct": pct, "id": "overall-progress"},
    ]
    if data.get("elapsed"):
        header.append({"type": "text", "text": f"⏱ Elapsed: {data['elapsed']}", "muted": True})

    board = {
        "type": "board",
        "id": "task-board",
        "columns": [
            {"id": "col-done", "title": "✅ Done", "items": cols["done"]},
            {"id": "col-running", "title": "🔄 Running", "items": cols["running"]},
            {"id": "col-pending", "title": "⏳ Pending", "items": cols["pending"]},
        ],
    }
    return header + [board]


def _tpl_data_dashboard(data: dict) -> list:
    """
    data = {
        "title": str,
        "metrics": [{"label": str, "value": str, "trend": "up"|"down"|None}],
        "chart": {"label": str, "labels": [...], "datasets": [...]},  (optional)
        "table": {"headers": [...], "rows": [...]}  (optional)
    }
    """
    components: list = [
        {"type": "heading", "level": 2, "text": data.get("title", "Dashboard")}
    ]

    metrics = data.get("metrics", [])
    if metrics:
        components.append({
            "type": "row",
            "id": "metrics-row",
            "children": [
                {"type": "metric", "id": f"metric-{i}", "label": m["label"], "value": m["value"], "trend": m.get("trend")}
                for i, m in enumerate(metrics)
            ],
        })

    chart = data.get("chart")
    if chart:
        components.append({
            "type": "chart_line",
            "id": "dashboard-chart",
            "label": chart.get("label", "Chart"),
            "labels": chart.get("labels", []),
            "datasets": chart.get("datasets", []),
        })

    table = data.get("table")
    if table:
        components.append({
            "type": "table",
            "id": "dashboard-table",
            "headers": table.get("headers", []),
            "rows": table.get("rows", []),
        })

    return components


def _tpl_config_form(data: dict) -> list:
    """
    data = {
        "title": str,
        "description": str  (optional),
        "fields": [{"name": str, "label": str, "type": "text"|"select"|"checkbox"|"number", "options": [...], "default": ...}],
        "submit_label": str  (default "Submit"),
        "cancel_label": str  (default "Cancel")
    }
    """
    return [
        {"type": "heading", "level": 2, "text": data.get("title", "Configuration")},
        *(
            [{"type": "text", "text": data["description"]}]
            if data.get("description")
            else []
        ),
        {
            "type": "form",
            "id": "config-form",
            "fields": data.get("fields", []),
            "actions": [
                {"type": "button", "label": data.get("cancel_label", "Cancel"), "action_id": "cancel", "variant": "ghost"},
                {"type": "button", "label": data.get("submit_label", "Submit"), "action_id": "submit", "variant": "primary"},
            ],
        },
    ]


def _tpl_plan_view(data: dict) -> list:
    """
    data = {
        "title": str,
        "description": str  (optional),
        "mermaid": str  (Mermaid diagram source),
        "approve_label": str  (default "Approve & Execute"),
        "cancel_label": str  (default "Cancel")
    }
    """
    components: list = [
        {"type": "heading", "level": 2, "text": data.get("title", "Plan Review")},
    ]
    if data.get("description"):
        components.append({"type": "text", "text": data["description"]})

    components.append({
        "type": "flowchart",
        "id": "plan-diagram",
        "content": data.get("mermaid", "flowchart TD\n  A[No diagram provided]"),
    })

    components.append({
        "type": "row",
        "children": [
            {"type": "button", "label": data.get("cancel_label", "Cancel"), "action_id": "cancel", "variant": "danger"},
            {"type": "button", "label": data.get("approve_label", "Approve & Execute"), "action_id": "approve", "variant": "primary"},
        ],
    })
    return components
