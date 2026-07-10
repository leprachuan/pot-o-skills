"""Image preprocessing utilities for image-to-3D conversion."""

import os
import io
import base64
import logging
from pathlib import Path
from typing import Optional, Tuple

from PIL import Image

logger = logging.getLogger("image-to-3d.image_utils")

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
MAX_IMAGE_SIZE_MB = 20
DEFAULT_RESIZE = 512


def validate_image(image_path: str) -> dict:
    """Validate an image file for 3D conversion suitability."""
    path = Path(image_path)

    if not path.exists():
        return {"valid": False, "error": f"File not found: {image_path}"}

    if path.suffix.lower() not in SUPPORTED_FORMATS:
        return {
            "valid": False,
            "error": f"Unsupported format: {path.suffix}. Supported: {', '.join(SUPPORTED_FORMATS)}",
        }

    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_IMAGE_SIZE_MB:
        return {"valid": False, "error": f"File too large: {size_mb:.1f}MB (max {MAX_IMAGE_SIZE_MB}MB)"}

    try:
        with Image.open(path) as img:
            width, height = img.size
            mode = img.mode
    except Exception as e:
        return {"valid": False, "error": f"Cannot open image: {e}"}

    return {
        "valid": True,
        "width": width,
        "height": height,
        "mode": mode,
        "format": path.suffix.lower(),
        "size_mb": round(size_mb, 2),
    }


def preprocess_image(
    image_path: str,
    target_size: int = DEFAULT_RESIZE,
    remove_background: bool = True,
    output_path: Optional[str] = None,
) -> str:
    """Preprocess image for 3D reconstruction.

    - Resize to target dimensions (square)
    - Convert to RGB
    - Optionally remove background (makes white)
    - Save as PNG
    """
    img = Image.open(image_path)

    # Convert to RGB if needed (handle RGBA, L, P modes)
    if img.mode == "RGBA":
        # Composite onto white background
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Resize to square with padding
    img = _resize_and_pad(img, target_size)

    # Save preprocessed image
    if output_path is None:
        base = Path(image_path).stem
        output_path = f"/tmp/3d-output/{base}_preprocessed.png"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, "PNG")
    logger.info(f"Preprocessed image saved to {output_path}")
    return output_path


def _resize_and_pad(img: Image.Image, target_size: int) -> Image.Image:
    """Resize image to target_size×target_size, maintaining aspect ratio with white padding."""
    width, height = img.size
    scale = target_size / max(width, height)
    new_w = int(width * scale)
    new_h = int(height * scale)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # Pad to square
    padded = Image.new("RGB", (target_size, target_size), (255, 255, 255))
    offset_x = (target_size - new_w) // 2
    offset_y = (target_size - new_h) // 2
    padded.paste(img, (offset_x, offset_y))
    return padded


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def download_image(url: str, output_path: str) -> str:
    """Download an image from a URL."""
    import requests

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)

    logger.info(f"Downloaded image from {url} to {output_path}")
    return output_path
