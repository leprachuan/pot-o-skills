"""
Canvas Server — HTTP + WebSocket server for Live Canvas skill.
Port: 18793  |  WS path: /ws?session=SESSION_ID
Auto-stops after 30 minutes of no active WebSocket connections.
"""
import asyncio
import json
import ssl
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from websockets.asyncio.server import serve, ServerConnection
from websockets.http11 import Request, Response
from websockets.datastructures import Headers

PORT = 18793
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets" / "canvas-viewer"
INACTIVITY_TIMEOUT = 30 * 60

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript",
    ".css": "text/css",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/x-icon",
}

# Global session state
sessions: dict = {}
active_ws_connections: set = set()
last_activity: list = [time.time()]


def get_session(session_id: str) -> dict:
    if session_id not in sessions:
        sessions[session_id] = {
            "components": [],
            "connections": set(),
            "action_watchers": set(),
            "pending_actions": [],
        }
    return sessions[session_id]


async def _broadcast(session: dict, skip_conn, message: dict):
    """Broadcast message to all connections in session except skip_conn."""
    for conn in list(session["connections"]):
        if conn is not skip_conn:
            try:
                await conn.send(json.dumps(message))
            except Exception:
                session["connections"].discard(conn)
                session["action_watchers"].discard(conn)


def _apply_update(components: list, node_id: str, changes: dict) -> bool:
    """Recursively find component by id and apply changes."""
    for comp in components:
        if isinstance(comp, dict):
            if comp.get("id") == node_id:
                comp.update(changes)
                return True
            for key in ("children", "items", "columns", "steps", "rows", "metrics", "fields"):
                children = comp.get(key, [])
                if isinstance(children, list) and _apply_update(children, node_id, changes):
                    return True
    return False


def _make_response(status: int, reason: str, content: bytes, mime: str) -> Response:
    headers = Headers({
        "Content-Type": mime,
        "Content-Length": str(len(content)),
        "Cache-Control": "no-cache",
        "Access-Control-Allow-Origin": "*",
        "Connection": "close",
    })
    return Response(status, reason, headers, content)


def process_request(connection: ServerConnection, request: Request):
    """Intercept non-WebSocket HTTP requests and serve static files."""
    path = request.path
    if path.startswith("/ws"):
        return None  # Let websockets handle the upgrade

    parsed = urlparse(path)
    file_path = parsed.path.strip("/") or "index.html"
    full_path = ASSETS_DIR / file_path

    if not full_path.exists() or not full_path.is_file():
        full_path = ASSETS_DIR / "index.html"

    if not full_path.exists():
        return _make_response(404, "Not Found", b"Not Found", "text/plain")

    content = full_path.read_bytes()
    mime = MIME_TYPES.get(full_path.suffix.lower(), "application/octet-stream")
    return _make_response(200, "OK", content, mime)


async def handler(websocket: ServerConnection):
    """Handle a WebSocket connection."""
    parsed = urlparse(websocket.request.path)
    params = parse_qs(parsed.query)
    session_id = params.get("session", ["default"])[0]

    session = get_session(session_id)
    session["connections"].add(websocket)
    active_ws_connections.add(websocket)
    last_activity[0] = time.time()

    # Restore last state for new browser connections
    if session["components"]:
        try:
            await websocket.send(json.dumps({
                "type": "restore",
                "components": session["components"],
                "session_id": session_id,
            }))
        except Exception:
            pass

    try:
        async for message in websocket:
            last_activity[0] = time.time()
            try:
                data = json.loads(message)
            except Exception:
                continue

            msg_type = data.get("type")

            if msg_type == "render":
                session["components"] = data.get("components", [])
                await _broadcast(session, websocket, {
                    "type": "render",
                    "components": session["components"],
                    "session_id": session_id,
                })

            elif msg_type == "update":
                node_id = data.get("node_id")
                changes = data.get("changes", {})
                _apply_update(session["components"], node_id, changes)
                await _broadcast(session, websocket, {
                    "type": "update",
                    "node_id": node_id,
                    "changes": changes,
                })

            elif msg_type == "clear":
                session["components"] = []
                await _broadcast(session, websocket, {
                    "type": "clear",
                    "session_id": session_id,
                })

            elif msg_type == "action":
                # User clicked a button — queue it and notify watchers
                session["pending_actions"].append(data)
                for watcher in list(session["action_watchers"]):
                    try:
                        await watcher.send(json.dumps(data))
                    except Exception:
                        session["action_watchers"].discard(watcher)

            elif msg_type == "subscribe_actions":
                # Agent wants to receive next button click
                session["action_watchers"].add(websocket)
                # Flush any already-pending actions
                for action in list(session["pending_actions"]):
                    try:
                        await websocket.send(json.dumps(action))
                    except Exception:
                        break
                session["pending_actions"].clear()

    except Exception:
        pass
    finally:
        session["connections"].discard(websocket)
        session["action_watchers"].discard(websocket)
        active_ws_connections.discard(websocket)
        last_activity[0] = time.time()


async def _inactivity_monitor(stop_event: asyncio.Event):
    """Set stop_event after INACTIVITY_TIMEOUT seconds with no WS connections."""
    while not stop_event.is_set():
        await asyncio.sleep(60)
        if not active_ws_connections:
            if time.time() - last_activity[0] > INACTIVITY_TIMEOUT:
                stop_event.set()


def _load_hosts() -> list[str]:
    """Load bind hosts from canvas_config.json, defaulting to localhost only."""
    config_path = Path(__file__).parent / "canvas_config.json"
    if config_path.exists():
        try:
            cfg = json.loads(config_path.read_text())
            hosts = cfg.get("bind_hosts", ["127.0.0.1"])
            return hosts if hosts else ["127.0.0.1"]
        except Exception:
            pass
    return ["127.0.0.1"]


def _load_tls_context() -> ssl.SSLContext | None:
    """Load optional TLS settings from canvas_config.json."""
    config_path = Path(__file__).parent / "canvas_config.json"
    if not config_path.exists():
        return None

    try:
        cfg = json.loads(config_path.read_text())
    except Exception:
        return None

    tls_cfg = cfg.get("tls", {})
    if not isinstance(tls_cfg, dict) or not tls_cfg.get("enabled"):
        return None

    certfile = tls_cfg.get("certfile")
    keyfile = tls_cfg.get("keyfile")
    if not certfile or not keyfile:
        print("TLS enabled but certfile/keyfile missing in canvas_config.json; starting without TLS.", flush=True)
        return None

    cert_path = Path(certfile).expanduser()
    key_path = Path(keyfile).expanduser()
    if not cert_path.exists() or not key_path.exists():
        print("TLS enabled but certfile/keyfile paths do not exist; starting without TLS.", flush=True)
        return None

    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
        return context
    except Exception as exc:
        print(f"Failed to initialize TLS context: {exc}; starting without TLS.", flush=True)
        return None


async def main():
    import contextlib
    stop_event = asyncio.Event()
    asyncio.create_task(_inactivity_monitor(stop_event))

    hosts = _load_hosts()
    ssl_context = _load_tls_context()
    scheme = "https" if ssl_context else "http"
    async with contextlib.AsyncExitStack() as stack:
        for host in hosts:
            await stack.enter_async_context(
                serve(
                    handler,
                    host,
                    PORT,
                    process_request=process_request,
                    ssl=ssl_context,
                )
            )
            print(f"Canvas server listening on {scheme}://{host}:{PORT}", flush=True)
        await stop_event.wait()

    print("Canvas server stopped (inactivity timeout).", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
