"""Main converter orchestrator for image-to-3D conversion.

Manages backend selection, image preprocessing, conversion,
post-processing, and optional 3D Canvas preview.
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import Optional

from .image_utils import validate_image, preprocess_image, download_image
from .mesh_utils import get_mesh_metadata, convert_mesh_format
from .backends.triposr_local import TripoSRLocalBackend
from .backends.replicate_cloud import ReplicateCloudBackend
from .backends.stability_cloud import StabilityCloudBackend

logger = logging.getLogger("image-to-3d.converter")


class ImageTo3DConverter:
    """Orchestrates image-to-3D conversion across multiple backends."""

    def __init__(self, backend: str = "auto"):
        self.preferred_backend = backend
        self.backends = {
            "triposr_local": TripoSRLocalBackend(),
            "replicate_cloud": ReplicateCloudBackend(),
            "stability_cloud": StabilityCloudBackend(),
        }

    def convert(
        self,
        image: str,
        output_format: str = "glb",
        quality: str = "standard",
        texture_resolution: int = 1024,
        output_dir: str = "/tmp/3d-output",
        preview: bool = True,
        remove_background: bool = True,
        backend: Optional[str] = None,
    ) -> dict:
        """Convert an image to a 3D model.

        Args:
            image: File path or URL to the input image.
            output_format: Output format (glb, obj, stl, ply).
            quality: Quality preset (draft, standard, high).
            texture_resolution: Texture resolution in pixels.
            output_dir: Directory to save the output.
            preview: Whether to open result in 3D Canvas.
            remove_background: Whether to auto-remove background.
            backend: Override backend selection (local, cloud, auto).

        Returns:
            Dict with success status, model path, metadata, etc.
        """
        start_time = time.time()
        os.makedirs(output_dir, exist_ok=True)

        # Handle URL inputs
        if image.startswith(("http://", "https://")):
            url_filename = Path(image.split("?")[0]).name or "download.png"
            image = download_image(image, os.path.join(output_dir, f"input_{url_filename}"))

        # Validate input image
        validation = validate_image(image)
        if not validation["valid"]:
            return {"success": False, "error": validation["error"]}

        logger.info(
            f"Converting {image} ({validation['width']}x{validation['height']}) "
            f"→ {output_format} (quality={quality})"
        )

        # Preprocess image
        preprocessed = preprocess_image(
            image,
            target_size=512 if quality == "draft" else 1024 if quality == "high" else 512,
            remove_background=remove_background,
        )

        # Select backend
        backend_name = self._select_backend(backend or self.preferred_backend, quality)
        selected_backend = self.backends.get(backend_name)

        if selected_backend is None:
            return {"success": False, "error": f"Backend not found: {backend_name}"}

        logger.info(f"Using backend: {backend_name}")

        # Run conversion
        try:
            result = selected_backend.convert(
                image_path=preprocessed,
                output_format=output_format,
                quality=quality,
                texture_resolution=texture_resolution,
                output_dir=output_dir,
            )
        except RuntimeError as e:
            # Try fallback if auto mode
            if (backend or self.preferred_backend) == "auto" and backend_name == "triposr_local":
                logger.warning(f"Local backend failed ({e}), trying cloud fallback...")
                fallback = self._get_cloud_fallback()
                if fallback:
                    result = fallback.convert(
                        image_path=preprocessed,
                        output_format=output_format,
                        quality=quality,
                        texture_resolution=texture_resolution,
                        output_dir=output_dir,
                    )
                else:
                    return {"success": False, "error": str(e), "fallback_attempted": True}
            else:
                return {"success": False, "error": str(e)}

        # Get mesh metadata
        if result.get("success") and result.get("model_path"):
            metadata = get_mesh_metadata(result["model_path"])
            result["metadata"] = metadata

        # Open preview in 3D Canvas
        if preview and result.get("success"):
            preview_url = self._open_preview(result["model_path"])
            if preview_url:
                result["preview_url"] = preview_url

        total_time_ms = int((time.time() - start_time) * 1000)
        result["total_time_ms"] = total_time_ms

        return result

    def health_check(self) -> dict:
        """Check health of all backends."""
        statuses = {}
        for name, backend in self.backends.items():
            statuses[name] = backend.health_check()
        return {"backends": statuses}

    def list_backends(self) -> list:
        """List all available backends with their status."""
        result = []
        for name, backend in self.backends.items():
            result.append(
                {
                    "name": name,
                    "available": backend.is_available(),
                    "type": "local" if "local" in name else "cloud",
                }
            )
        return result

    def _select_backend(self, preference: str, quality: str) -> str:
        """Select the best backend based on preference and quality."""
        if preference == "local":
            return "triposr_local"

        if preference == "cloud":
            return self._get_cloud_backend_name()

        # Auto mode
        if quality == "high":
            cloud = self._get_cloud_backend_name()
            if self.backends[cloud].is_available():
                return cloud

        # Try local first
        if self.backends["triposr_local"].is_available():
            return "triposr_local"

        # Fall back to cloud
        return self._get_cloud_backend_name()

    def _get_cloud_backend_name(self) -> str:
        """Get the best available cloud backend name."""
        if self.backends["replicate_cloud"].is_available():
            return "replicate_cloud"
        if self.backends["stability_cloud"].is_available():
            return "stability_cloud"
        return "replicate_cloud"  # default even if unavailable

    def _get_cloud_fallback(self):
        """Get a cloud backend for fallback."""
        for name in ["replicate_cloud", "stability_cloud"]:
            backend = self.backends[name]
            if backend.is_available():
                return backend
        return None

    def _open_preview(self, model_path: str) -> Optional[str]:
        """Open the generated model in the 3D Canvas."""
        try:
            import sys

            sys.path.insert(0, "/opt/skills/3d-modeling/claude/implementation")
            from modeling3d import Canvas3D

            session_id = f"img3d-{uuid.uuid4().hex[:8]}"
            canvas = Canvas3D(session_id=session_id)

            canvas.render_scene(
                {
                    "title": f"Image-to-3D: {Path(model_path).stem}",
                    "objects": [
                        {
                            "type": "imported_glb",
                            "path": model_path,
                            "position": [0, 0, 0],
                        }
                    ],
                    "grid": True,
                    "autoRotate": True,
                    "camera": {"position": [30, 20, 30]},
                }
            )

            preview_url = f"http://localhost:18794?session={session_id}"
            logger.info(f"3D Canvas preview: {preview_url}")
            return preview_url
        except Exception as e:
            logger.debug(f"Could not open 3D Canvas preview: {e}")
            return None
