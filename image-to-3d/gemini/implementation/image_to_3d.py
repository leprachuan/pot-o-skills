"""Image-to-3D skill implementation for Gemini runtime.

Provides the same API as Claude/Copilot implementations.

Usage:
    import sys
    sys.path.insert(0, '/opt/skills/image-to-3d/gemini/implementation')
    from image_to_3d import ImageTo3D

    converter = ImageTo3D()
    result = converter.convert("photo.jpg", output_format="glb")
"""

import sys
import os
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.converter import ImageTo3DConverter

logger = logging.getLogger("image-to-3d.gemini")


class ImageTo3D:
    """Gemini runtime interface for image-to-3D conversion."""

    def __init__(self, backend: str = "auto"):
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
        """Convert an image to a 3D model. See Claude implementation for full docs."""
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
        return self.converter.health_check()

    def list_backends(self) -> list:
        return self.converter.list_backends()

    def batch_convert(self, images: list, **kwargs) -> list:
        results = []
        for i, img in enumerate(images):
            logger.info(f"Batch {i+1}/{len(images)}: {img}")
            result = self.convert(image=img, preview=False, **kwargs)
            results.append(result)
        return results
