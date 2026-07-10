"""TripoSR local inference backend.

Communicates with a local FastAPI inference server running TripoSR
on the GPU (typically RTX 3060). The server runs on port 18795.
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger("image-to-3d.triposr_local")

DEFAULT_SERVER_URL = "http://localhost:18795"


class TripoSRLocalBackend:
    """Local TripoSR inference via FastAPI server."""

    def __init__(self, server_url: Optional[str] = None):
        self.server_url = server_url or os.environ.get("IMG3D_SERVER_URL", DEFAULT_SERVER_URL)
        self.name = "triposr_local"

    def is_available(self) -> bool:
        """Check if the local inference server is running and GPU is available."""
        try:
            resp = requests.get(f"{self.server_url}/health", timeout=5)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                except (ValueError, requests.exceptions.JSONDecodeError):
                    return False
                return data.get("status") == "healthy" and data.get("gpu", {}).get("available", False)
        except (requests.ConnectionError, requests.Timeout, requests.RequestException):
            pass
        return False

    def health_check(self) -> dict:
        """Get detailed health status from the inference server."""
        try:
            resp = requests.get(f"{self.server_url}/health", timeout=5)
            resp.raise_for_status()
            try:
                return resp.json()
            except (ValueError, requests.exceptions.JSONDecodeError):
                return {"status": "unavailable", "error": "Server returned non-JSON response"}
        except Exception as e:
            return {"status": "unavailable", "error": str(e)}

    def convert(
        self,
        image_path: str,
        output_format: str = "glb",
        quality: str = "standard",
        texture_resolution: int = 1024,
        output_dir: str = "/tmp/3d-output",
    ) -> dict:
        """Convert an image to 3D model using local TripoSR server."""
        os.makedirs(output_dir, exist_ok=True)

        quality_settings = {
            "draft": {"mc_resolution": 128, "texture_resolution": 512},
            "standard": {"mc_resolution": 256, "texture_resolution": 1024},
            "high": {"mc_resolution": 512, "texture_resolution": 2048},
        }

        settings = quality_settings.get(quality, quality_settings["standard"])
        settings["texture_resolution"] = texture_resolution

        start_time = time.time()

        with open(image_path, "rb") as f:
            files = {"image": (Path(image_path).name, f, "image/png")}
            data = {
                "format": output_format,
                "mc_resolution": settings["mc_resolution"],
                "texture_resolution": settings["texture_resolution"],
            }

            try:
                resp = requests.post(
                    f"{self.server_url}/api/convert",
                    files=files,
                    data=data,
                    timeout=60,
                )
                resp.raise_for_status()
            except requests.ConnectionError:
                raise RuntimeError(
                    f"Cannot connect to TripoSR server at {self.server_url}. "
                    "Start it with: cd /opt/skills/image-to-3d && python -m core.server"
                )
            except requests.Timeout:
                raise RuntimeError("TripoSR inference timed out (>60s)")

        inference_time_ms = int((time.time() - start_time) * 1000)

        # Save the model file
        stem = Path(image_path).stem
        output_path = os.path.join(output_dir, f"{stem}.{output_format}")

        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            # Server returned JSON with error or download URL
            result = resp.json()
            if not result.get("success", True):
                raise RuntimeError(f"TripoSR conversion failed: {result.get('error', 'unknown')}")
            # If server sends file URL, download it
            if "download_url" in result:
                dl = requests.get(f"{self.server_url}{result['download_url']}", timeout=30)
                dl.raise_for_status()
                with open(output_path, "wb") as f:
                    f.write(dl.content)
        else:
            # Binary response with the model file
            with open(output_path, "wb") as f:
                f.write(resp.content)

        return {
            "success": True,
            "model_path": output_path,
            "format": output_format,
            "backend_used": self.name,
            "inference_time_ms": inference_time_ms,
        }
