"""Stability AI cloud backend for image-to-3D conversion.

Uses the Stability AI API (Stable Fast 3D / SF3D) for fast cloud-based
image-to-3D conversion. Requires STABILITY_API_KEY environment variable.
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger("image-to-3d.stability_cloud")

STABILITY_API_BASE = "https://api.stability.ai"
SF3D_ENDPOINT = "/v2beta/3d/stable-fast-3d"


class StabilityCloudBackend:
    """Cloud inference via Stability AI SF3D API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("STABILITY_API_KEY")
        self.name = "stability_cloud"

    def is_available(self) -> bool:
        """Check if Stability AI API is accessible."""
        return bool(self.api_key)

    def health_check(self) -> dict:
        """Get Stability AI backend status."""
        if not self.api_key:
            return {"status": "unavailable", "error": "STABILITY_API_KEY not set"}
        return {"status": "available", "endpoint": "Stability AI SF3D"}

    def convert(
        self,
        image_path: str,
        output_format: str = "glb",
        quality: str = "standard",
        texture_resolution: int = 1024,
        output_dir: str = "/tmp/3d-output",
    ) -> dict:
        """Convert image to 3D via Stability AI SF3D API."""
        if not self.api_key:
            raise RuntimeError(
                "STABILITY_API_KEY not set. "
                "Get your key at https://platform.stability.ai/account/keys"
            )

        os.makedirs(output_dir, exist_ok=True)
        start_time = time.time()

        headers = {"Authorization": f"Bearer {self.api_key}"}

        with open(image_path, "rb") as f:
            files = {"image": (Path(image_path).name, f, "image/png")}
            data = {
                "texture_resolution": str(texture_resolution),
                "foreground_ratio": "0.85",
            }

            try:
                resp = requests.post(
                    f"{STABILITY_API_BASE}{SF3D_ENDPOINT}",
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60,
                )
            except requests.Timeout:
                raise RuntimeError("Stability AI SF3D request timed out")

        if resp.status_code == 402:
            raise RuntimeError("Stability AI: Insufficient credits. Top up at platform.stability.ai")
        resp.raise_for_status()

        inference_time_ms = int((time.time() - start_time) * 1000)

        # Save the GLB output
        stem = Path(image_path).stem
        output_path = os.path.join(output_dir, f"{stem}.glb")

        with open(output_path, "wb") as f:
            f.write(resp.content)

        # Convert if needed
        if output_format != "glb":
            from ..mesh_utils import convert_mesh_format

            output_path = convert_mesh_format(output_path, output_format)

        return {
            "success": True,
            "model_path": output_path,
            "format": output_format,
            "backend_used": self.name,
            "inference_time_ms": inference_time_ms,
        }
