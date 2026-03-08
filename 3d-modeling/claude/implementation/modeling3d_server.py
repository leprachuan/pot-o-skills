"""
3D Modeling Server — HTTP + WebSocket server for the 3D Modeling Canvas skill.
Port: 18794  |  WS path: /ws?session=SESSION_ID
Auto-stops after 30 minutes of no active WebSocket connections.
"""
import asyncio
import json
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from websockets.asyncio.server import serve, ServerConnection
from websockets.http11 import Request, Response
from websockets.datastructures import Headers

PORT = 18794
ASSETS_DIR = Path(__file__).parent.parent.parent / "assets" / "3d-viewer"
INACTIVITY_TIMEOUT = 30 * 60

MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript",
    ".mjs": "application/javascript",
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
            "scene": None,
            "connections": set(),
            "action_watchers": set(),
            "pending_actions": [],
        }
    return sessions[session_id]


async def _broadcast(session: dict, skip_conn, message: dict):
    for conn in list(session["connections"]):
        if conn is not skip_conn:
            try:
                await conn.send(json.dumps(message))
            except Exception:
                session["connections"].discard(conn)
                session["action_watchers"].discard(conn)


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
    path = request.path
    if path.startswith("/ws"):
        return None  # Let websockets handle WS upgrade

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
    parsed = urlparse(websocket.request.path)
    params = parse_qs(parsed.query)
    session_id = params.get("session", ["default"])[0]

    session = get_session(session_id)
    session["connections"].add(websocket)
    active_ws_connections.add(websocket)
    last_activity[0] = time.time()

    # Restore last scene for reconnecting browsers
    if session["scene"] is not None:
        try:
            await websocket.send(json.dumps({
                "type": "restore",
                "scene": session["scene"],
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

            if msg_type == "render_scene":
                session["scene"] = data.get("scene", {})
                await _broadcast(session, websocket, {
                    "type": "render_scene",
                    "scene": session["scene"],
                    "session_id": session_id,
                })

            elif msg_type == "add_object":
                obj = data.get("object", {})
                if session["scene"] is None:
                    session["scene"] = {"objects": []}
                session["scene"].setdefault("objects", []).append(obj)
                await _broadcast(session, websocket, {
                    "type": "add_object",
                    "object": obj,
                })

            elif msg_type == "transform":
                obj_id = data.get("obj_id")
                if session["scene"] and obj_id:
                    for obj in session["scene"].get("objects", []):
                        if obj.get("id") == obj_id:
                            if "position" in data:
                                obj["position"] = data["position"]
                            if "rotation" in data:
                                obj["rotation"] = data["rotation"]
                            if "scale" in data:
                                obj["scale"] = data["scale"]
                            break
                await _broadcast(session, websocket, {
                    "type": "transform",
                    "obj_id": obj_id,
                    "position": data.get("position"),
                    "rotation": data.get("rotation"),
                    "scale": data.get("scale"),
                })

            elif msg_type == "set_camera":
                if session["scene"] is None:
                    session["scene"] = {}
                session["scene"]["camera"] = data.get("camera", {})
                await _broadcast(session, websocket, {
                    "type": "set_camera",
                    "camera": session["scene"]["camera"],
                })

            elif msg_type == "set_title":
                if session["scene"] is None:
                    session["scene"] = {}
                session["scene"]["title"] = data.get("title", "")
                await _broadcast(session, websocket, {
                    "type": "set_title",
                    "title": session["scene"]["title"],
                })

            elif msg_type == "export":
                # Agent requests browser to trigger download
                await _broadcast(session, websocket, {
                    "type": "export",
                    "format": data.get("format", "stl"),
                })

            elif msg_type == "clear":
                session["scene"] = {"objects": []}
                await _broadcast(session, websocket, {
                    "type": "clear",
                    "session_id": session_id,
                })

            elif msg_type == "action":
                # Browser button click — queue and notify agent watchers
                session["pending_actions"].append(data)
                for watcher in list(session["action_watchers"]):
                    try:
                        await watcher.send(json.dumps(data))
                    except Exception:
                        session["action_watchers"].discard(watcher)

            elif msg_type == "subscribe_actions":
                session["action_watchers"].add(websocket)
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
    while not stop_event.is_set():
        await asyncio.sleep(60)
        if not active_ws_connections:
            if time.time() - last_activity[0] > INACTIVITY_TIMEOUT:
                stop_event.set()


async def main():
    import contextlib
    stop_event = asyncio.Event()
    asyncio.create_task(_inactivity_monitor(stop_event))

    async with contextlib.AsyncExitStack() as stack:
        await stack.enter_async_context(
            serve(handler, "0.0.0.0", PORT, process_request=process_request)
        )
        print(f"3D Modeling server listening on http://0.0.0.0:{PORT}", flush=True)
        await stop_event.wait()

    print("3D Modeling server stopped (inactivity timeout).", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
