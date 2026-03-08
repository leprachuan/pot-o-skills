"""Replicate cloud backend for image-to-3D conversion.

Uses the Replicate API to run TRELLIS or other image-to-3D models
in the cloud. Requires REPLICATE_API_TOKEN environment variable.
"""

import os
import time
import logging
import requests
from pathlib import Path
from typing import Optional

logger = logging.getLogger("image-to-3d.replicate_cloud")

REPLICATE_API_BASE = "https://api.replicate.com/v1"
DEFAULT_MODEL = "firtoz/trellis"
DEFAULT_MODEL_VERSION = None  # use latest


class ReplicateCloudBackend:
    """Cloud inference via Replicate API (TRELLIS model)."""

    def __init__(self, api_token: Optional[str] = None, model: Optional[str] = None):
        self.api_token = api_token or os.environ.get("REPLICATE_API_TOKEN")
        self.model = model or DEFAULT_MODEL
        self.name = "replicate_cloud"

    def is_available(self) -> bool:
        """Check if Replicate API is accessible."""
        if not self.api_token:
            return False
        try:
            resp = requests.get(
                f"{REPLICATE_API_BASE}/models/{self.model}",
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def health_check(self) -> dict:
        """Get Replicate backend status."""
        if not self.api_token:
            return {"status": "unavailable", "error": "REPLICATE_API_TOKEN not set"}
        try:
            resp = requests.get(
                f"{REPLICATE_API_BASE}/models/{self.model}",
                headers={"Authorization": f"Bearer {self.api_token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "available",
                    "model": self.model,
                    "description": data.get("description", ""),
                }
            return {"status": "error", "http_status": resp.status_code}
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
        """Convert image to 3D via Replicate API."""
        if not self.api_token:
            raise RuntimeError(
                "REPLICATE_API_TOKEN not set. "
                "Get your token at https://replicate.com/account/api-tokens"
            )

        os.makedirs(output_dir, exist_ok=True)
        start_time = time.time()

        # Upload image as base64 data URI
        import base64

        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = Path(image_path).suffix.lower().lstrip(".")
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp"}.get(
            ext, "image/png"
        )
        data_uri = f"data:{mime};base64,{image_data}"

        quality_map = {
            "draft": {"simplify": 0.98, "texture_size": 512},
            "standard": {"simplify": 0.95, "texture_size": 1024},
            "high": {"simplify": 0.90, "texture_size": 2048},
        }
        settings = quality_map.get(quality, quality_map["standard"])
        settings["texture_size"] = texture_resolution

        # Create prediction
        payload = {
            "input": {
                "image": data_uri,
                "simplify": settings["simplify"],
                "texture_size": settings["texture_size"],
                "generate_model": True,
            }
        }

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            f"{REPLICATE_API_BASE}/models/{self.model}/predictions",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        prediction = resp.json()

        # Poll for completion
        poll_url = prediction.get("urls", {}).get("get", prediction.get("url"))
        if not poll_url:
            raise RuntimeError("No poll URL in Replicate response")

        max_wait = 180  # 3 minutes
        poll_interval = 3
        elapsed = 0

        while elapsed < max_wait:
            time.sleep(poll_interval)
            elapsed += poll_interval

            resp = requests.get(poll_url, headers=headers, timeout=15)
            resp.raise_for_status()
            status_data = resp.json()

            status = status_data.get("status")
            if status == "succeeded":
                break
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                raise RuntimeError(f"Replicate prediction failed: {error}")
            elif status == "canceled":
                raise RuntimeError("Replicate prediction was canceled")

            logger.debug(f"Replicate status: {status} ({elapsed}s elapsed)")
        else:
            raise RuntimeError(f"Replicate prediction timed out after {max_wait}s")

        inference_time_ms = int((time.time() - start_time) * 1000)

        # Download the output model
        output = status_data.get("output")
        if not output:
            raise RuntimeError("No output in Replicate prediction result")

        # Output can be a URL string or dict with model URLs
        if isinstance(output, str):
            model_url = output
        elif isinstance(output, dict):
            model_url = output.get("model_file") or output.get("mesh") or output.get("glb")
        elif isinstance(output, list) and len(output) > 0:
            model_url = output[0] if isinstance(output[0], str) else output[0].get("model_file", "")
        else:
            raise RuntimeError(f"Unexpected Replicate output format: {type(output)}")

        if not model_url:
            raise RuntimeError("Could not find model file URL in Replicate output")

        # Download the model file
        stem = Path(image_path).stem
        output_path = os.path.join(output_dir, f"{stem}.{output_format}")

        dl_resp = requests.get(model_url, timeout=60)
        dl_resp.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(dl_resp.content)

        # Convert format if needed (Replicate typically outputs GLB)
        if output_format != "glb":
            from ..mesh_utils import convert_mesh_format

            output_path = convert_mesh_format(output_path, output_format)

        return {
            "success": True,
            "model_path": output_path,
            "format": output_format,
            "backend_used": self.name,
            "inference_time_ms": inference_time_ms,
            "replicate_model": self.model,
        }
