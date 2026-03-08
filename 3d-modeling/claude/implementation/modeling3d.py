"""
Canvas3D — agent-facing API for the 3D Modeling Canvas skill.

Usage:
    from modeling3d import Canvas3D

    c = Canvas3D()
    c.render_scene({
        "title": "My Model",
        "objects": [
            {"type": "box", "width": 10, "height": 10, "depth": 10,
             "color": "#10b981", "position": [0, 5, 0]},
        ],
        "grid": True,
    })
    c.open()
    action = c.wait_for_action(timeout=300)
"""
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Optional

SERVER_PORT = int(os.environ.get("MODELING3D_PORT", 18794))
SERVER_HOST = os.environ.get("MODELING3D_HOST", "localhost")
SERVER_MODULE = Path(__file__).parent / "modeling3d_server.py"


def _is_server_running() -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", SERVER_PORT))
        s.close()
        return True
    except (ConnectionRefusedError, OSError):
        return False


class Canvas3D:
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self._ensure_server()

    def _ensure_server(self):
        if not _is_server_running():
            subprocess.Popen(
                [sys.executable, str(SERVER_MODULE)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            for _ in range(16):
                time.sleep(0.25)
                if _is_server_running():
                    break

    def _url(self) -> str:
        return f"http://{SERVER_HOST}:{SERVER_PORT}/?session={self.session_id}"

    def open(self):
        """Open the 3D viewer in the default browser."""
        url = self._url()
        print(f"Opening 3D viewer: {url}", flush=True)
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            os.system(f"xdg-open '{url}' &")

    # ── WebSocket helpers ─────────────────────────────────────────────────────

    def _send(self, message: dict):
        """Send a message to the server via a transient WebSocket."""
        asyncio.run(self._async_send(message))

    async def _async_send(self, message: dict):
        try:
            import websockets
            ws_url = f"ws://127.0.0.1:{SERVER_PORT}/ws?session={self.session_id}"
            async with websockets.connect(ws_url) as ws:
                await ws.send(json.dumps(message))
        except Exception as exc:
            print(f"[Canvas3D] send error: {exc}", flush=True)

    # ── Scene control ─────────────────────────────────────────────────────────

    def render_scene(self, scene: dict):
        """Replace the entire scene. Provide title, objects list, camera, etc."""
        self._send({"type": "render_scene", "scene": scene})

    def add_object(self, obj: dict):
        """Append a single 3D object to the current scene."""
        self._send({"type": "add_object", "object": obj})

    def transform(self, obj_id: str, position=None, rotation=None, scale=None):
        """Move, rotate, or scale an object by its id."""
        msg = {"type": "transform", "obj_id": obj_id}
        if position is not None:
            msg["position"] = position
        if rotation is not None:
            msg["rotation"] = rotation
        if scale is not None:
            msg["scale"] = scale
        self._send(msg)

    def set_camera(self, position: list, target: Optional[list] = None):
        """Reposition the camera. position and target are [x, y, z] lists."""
        camera = {"position": position}
        if target is not None:
            camera["target"] = target
        self._send({"type": "set_camera", "camera": camera})

    def set_title(self, title: str):
        """Update the scene title displayed in the viewer header."""
        self._send({"type": "set_title", "title": title})

    def clear(self):
        """Remove all objects from the scene."""
        self._send({"type": "clear"})

    def export(self, fmt: str = "stl"):
        """
        Trigger a file download in the browser.
        fmt: 'stl', 'obj', or 'glb'
        """
        fmt = fmt.lower().strip(".")
        if fmt not in ("stl", "obj", "glb"):
            raise ValueError(f"Unsupported export format: {fmt!r}. Use 'stl', 'obj', or 'glb'.")
        self._send({"type": "export", "format": fmt})

    # ── Action waiting ────────────────────────────────────────────────────────

    def wait_for_action(self, timeout: int = 60) -> dict:
        """
        Block until the user clicks a button in the viewer.
        Returns the action dict or {"type": "timeout"} on timeout.
        """
        return asyncio.run(self._async_wait_for_action(timeout))

    async def _async_wait_for_action(self, timeout: int) -> dict:
        try:
            import websockets
            ws_url = f"ws://127.0.0.1:{SERVER_PORT}/ws?session={self.session_id}"
            async with websockets.connect(ws_url) as ws:
                await ws.send(json.dumps({"type": "subscribe_actions"}))
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    return json.loads(raw)
                except asyncio.TimeoutError:
                    return {"type": "timeout"}
        except Exception as exc:
            return {"type": "error", "error": str(exc)}

    # ── Convenience helpers ───────────────────────────────────────────────────

    def add_box(self, width=10, height=10, depth=10, color="#10b981",
                id=None, position=None, rotation=None, wireframe=False):
        self.add_object({
            "type": "box", "id": id or str(uuid.uuid4())[:6],
            "width": width, "height": height, "depth": depth,
            "color": color, "wireframe": wireframe,
            "position": position or [0, height / 2, 0],
            "rotation": rotation or [0, 0, 0],
        })

    def add_sphere(self, radius=5, color="#3b82f6",
                   id=None, position=None, segments=32):
        self.add_object({
            "type": "sphere", "id": id or str(uuid.uuid4())[:6],
            "radius": radius, "widthSegments": segments, "heightSegments": segments // 2,
            "color": color,
            "position": position or [0, radius, 0],
        })

    def add_cylinder(self, radius_top=5, radius_bottom=5, height=20,
                     color="#f59e0b", id=None, position=None):
        self.add_object({
            "type": "cylinder", "id": id or str(uuid.uuid4())[:6],
            "radiusTop": radius_top, "radiusBottom": radius_bottom, "height": height,
            "radialSegments": 32,
            "color": color,
            "position": position or [0, height / 2, 0],
        })

    def add_cone(self, radius=5, height=15, color="#ef4444",
                 id=None, position=None):
        self.add_object({
            "type": "cone", "id": id or str(uuid.uuid4())[:6],
            "radius": radius, "height": height, "radialSegments": 32,
            "color": color,
            "position": position or [0, height / 2, 0],
        })

    def add_torus(self, radius=8, tube=2, color="#8b5cf6",
                  id=None, position=None):
        self.add_object({
            "type": "torus", "id": id or str(uuid.uuid4())[:6],
            "radius": radius, "tube": tube,
            "radialSegments": 16, "tubularSegments": 100,
            "color": color,
            "position": position or [0, radius, 0],
        })

    def add_plane(self, width=100, height=100, color="#374151",
                  id=None, position=None):
        self.add_object({
            "type": "plane", "id": id or str(uuid.uuid4())[:6],
            "width": width, "height": height,
            "color": color,
            "position": position or [0, 0, 0],
            "rotation": [-90, 0, 0],
        })
