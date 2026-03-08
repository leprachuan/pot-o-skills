"""Image-to-3D skill implementation for Claude runtime.

This module provides the agent-facing API for converting images to 3D models.
It wraps the core converter with a simple interface.

Usage:
    import sys
    sys.path.insert(0, '/opt/skills/image-to-3d/claude/implementation')
    from image_to_3d import ImageTo3D

    converter = ImageTo3D()
    result = converter.convert("photo.jpg", output_format="glb", preview=True)
"""

import sys
import os
import json
import logging

# Add core module to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.converter import ImageTo3DConverter

logger = logging.getLogger("image-to-3d.claude")


class ImageTo3D:
    """Agent-facing interface for image-to-3D conversion."""

    def __init__(self, backend: str = "auto"):
        """Initialize the converter.

        Args:
            backend: Backend selection mode.
                "auto" - Try local GPU first, fall back to cloud.
                "local" - Force local TripoSR (fails if GPU unavailable).
                "cloud" - Force cloud API (requires API key).
        """
        self.converter = ImageTo3DConverter(backend=backend)

    def convert(
        self,
        image: str,
        output_format: str = "glb",
        quality: str = "standard",
        texture_resolution: int = 1024,
        output_dir: str = "/tmp/3d-output",
        preview: bool = True,
        remove_background: bool = True,
        backend: str = None,
    ) -> dict:
        """Convert an image to a 3D model.

        Args:
            image: Path to image file or URL.
            output_format: Output format - "glb", "obj", "stl", or "ply".
            quality: Quality preset - "draft", "standard", or "high".
            texture_resolution: Texture resolution (512, 1024, 2048).
            output_dir: Directory to save output.
            preview: Whether to open result in 3D Canvas (port 18794).
            remove_background: Whether to auto-remove image background.
            backend: Override backend ("local", "cloud", "auto").

        Returns:
            Dict with keys:
                success (bool): Whether conversion succeeded.
                model_path (str): Path to the generated 3D model file.
                format (str): Output format used.
                backend_used (str): Which backend performed the conversion.
                inference_time_ms (int): Time spent on inference.
                metadata (dict): Mesh metadata (vertices, faces, file_size).
                preview_url (str): 3D Canvas URL if preview=True.
        """
        return self.converter.convert(
            image=image,
            output_format=output_format,
            quality=quality,
            texture_resolution=texture_resolution,
            output_dir=output_dir,
            preview=preview,
            remove_background=remove_background,
            backend=backend,
        )

    def health_check(self) -> dict:
        """Check the health of all inference backends.

        Returns:
            Dict with backend statuses including GPU availability,
            API key status, and model loading state.
        """
        return self.converter.health_check()

    def list_backends(self) -> list:
        """List all available backends and their status.

        Returns:
            List of dicts with name, available, and type for each backend.
        """
        return self.converter.list_backends()

    def batch_convert(
        self,
        images: list,
        output_format: str = "glb",
        quality: str = "standard",
        output_dir: str = "/tmp/3d-output",
    ) -> list:
        """Convert multiple images to 3D models.

        Args:
            images: List of image paths or URLs.
            output_format: Output format for all.
            quality: Quality preset for all.
            output_dir: Directory to save all outputs.

        Returns:
            List of result dicts, one per image.
        """
        results = []
        for i, img in enumerate(images):
            logger.info(f"Batch converting {i+1}/{len(images)}: {img}")
            result = self.convert(
                image=img,
                output_format=output_format,
                quality=quality,
                output_dir=output_dir,
                preview=False,  # don't preview each in batch mode
            )
            results.append(result)
        return results
