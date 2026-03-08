"""TripoSR CPU backend for true 3D reconstruction.

Runs the TripoSR model directly on CPU for volumetric 3D mesh generation.
Slower than GPU (~2-5 min) but produces true 3D geometry, not depth reliefs.
"""

import os
import sys
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional

import numpy as np
import torch
import trimesh
from PIL import Image

logger = logging.getLogger("image-to-3d.triposr_cpu")

TRIPOSR_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "models", "TripoSR")
DEFAULT_MODEL_ID = "stabilityai/TripoSR"


class TripoSRCPUBackend:
    """Direct TripoSR inference on CPU for true volumetric 3D generation."""

    def __init__(self, model_id: Optional[str] = None, chunk_size: int = 4096):
        self.model_id = model_id or DEFAULT_MODEL_ID
        self.chunk_size = chunk_size
        self.name = "triposr_cpu"
        self._model = None
        self._rembg_session = None

    def is_available(self) -> bool:
        """Check if TripoSR can run on CPU."""
        try:
            if not os.path.isdir(TRIPOSR_DIR):
                return False
            tsr_init = os.path.join(TRIPOSR_DIR, "tsr", "system.py")
            return os.path.exists(tsr_init)
        except Exception:
            return False

    def health_check(self) -> dict:
        """Get TripoSR CPU backend status."""
        if not self.is_available():
            return {"status": "unavailable", "error": "TripoSR source not found"}
        return {
            "status": "available",
            "device": "cpu",
            "model": self.model_id,
            "note": "CPU inference is slower (~2-5 min) but produces true 3D models",
        }

    def _load_model(self):
        """Lazy-load the TripoSR model."""
        if self._model is not None:
            return

        logger.info("Loading TripoSR model on CPU (this may take a minute)...")
        start = time.time()

        # Add TripoSR to path so its modules can import each other
        if TRIPOSR_DIR not in sys.path:
            sys.path.insert(0, TRIPOSR_DIR)

        from tsr.system import TSR

        self._model = TSR.from_pretrained(
            self.model_id, config_name="config.yaml", weight_name="model.ckpt"
        )
        self._model.renderer.set_chunk_size(self.chunk_size)
        self._model.to("cpu")
        self._model.eval()

        elapsed = time.time() - start
        logger.info(f"TripoSR model loaded in {elapsed:.1f}s")

    def _prepare_image(self, image_path: str, foreground_ratio: float = 0.85) -> Image.Image:
        """Preprocess image: remove background and resize foreground."""
        import rembg
        from tsr.utils import remove_background, resize_foreground

        image = Image.open(image_path)

        if self._rembg_session is None:
            self._rembg_session = rembg.new_session()

        image = remove_background(image, self._rembg_session)
        image = resize_foreground(image, foreground_ratio)
        image_arr = np.array(image).astype(np.float32) / 255.0
        # Composite onto gray background (TripoSR expects this)
        image_arr = image_arr[:, :, :3] * image_arr[:, :, 3:4] + (1 - image_arr[:, :, 3:4]) * 0.5
        return Image.fromarray((image_arr * 255.0).astype(np.uint8))

    def convert(
        self,
        image_path: str,
        output_format: str = "glb",
        quality: str = "standard",
        texture_resolution: int = 1024,
        output_dir: str = "/tmp/3d-output",
    ) -> dict:
        """Convert image to true 3D model using TripoSR on CPU."""
        os.makedirs(output_dir, exist_ok=True)
        start_time = time.time()

        quality_settings = {
            "draft": {"mc_resolution": 128, "bake_texture": False},
            "standard": {"mc_resolution": 256, "bake_texture": True},
            "high": {"mc_resolution": 256, "bake_texture": True},
        }
        settings = quality_settings.get(quality, quality_settings["standard"])

        # Load model
        logger.info("Step 1/4: Loading model...")
        self._load_model()
        model_load_time = time.time() - start_time

        # Preprocess image
        logger.info("Step 2/4: Preprocessing image (background removal)...")
        preprocess_start = time.time()
        processed_image = self._prepare_image(image_path)

        # Save preprocessed image for reference
        processed_path = os.path.join(output_dir, "input_processed.png")
        processed_image.save(processed_path)
        preprocess_time = time.time() - preprocess_start

        # Run inference
        logger.info("Step 3/4: Running TripoSR inference on CPU (this takes 1-3 minutes)...")
        inference_start = time.time()

        with torch.no_grad():
            scene_codes = self._model([processed_image], device="cpu")

        inference_time = time.time() - inference_start
        logger.info(f"Inference completed in {inference_time:.1f}s")

        # Extract mesh
        logger.info("Step 4/4: Extracting 3D mesh...")
        mesh_start = time.time()

        has_vertex_color = not settings["bake_texture"]
        meshes = self._model.extract_mesh(
            scene_codes,
            has_vertex_color=True,  # Always get vertex colors
            resolution=settings["mc_resolution"],
        )
        mesh = meshes[0]
        mesh_time = time.time() - mesh_start
        logger.info(f"Mesh extracted: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")

        # Bake texture if requested
        texture_path = None
        if settings["bake_texture"]:
            try:
                logger.info("Baking texture atlas...")
                texture_path = self._bake_texture(
                    mesh, scene_codes[0], texture_resolution, output_dir
                )
            except Exception as e:
                logger.warning(f"Texture baking failed, using vertex colors: {e}")

        # Save mesh in requested format
        stem = Path(image_path).stem
        output_path = os.path.join(output_dir, f"{stem}.{output_format}")

        if output_format == "glb":
            mesh.export(output_path, file_type="glb")
        elif output_format == "obj":
            mesh.export(output_path, file_type="obj")
        elif output_format == "stl":
            mesh.export(output_path, file_type="stl")
        elif output_format == "ply":
            mesh.export(output_path, file_type="ply")
        else:
            mesh.export(output_path)

        total_time = time.time() - start_time

        result = {
            "success": True,
            "model_path": output_path,
            "format": output_format,
            "backend_used": self.name,
            "inference_time_ms": int(inference_time * 1000),
            "timing": {
                "model_load_seconds": round(model_load_time, 2),
                "preprocess_seconds": round(preprocess_time, 2),
                "inference_seconds": round(inference_time, 2),
                "mesh_extraction_seconds": round(mesh_time, 2),
                "total_seconds": round(total_time, 2),
            },
            "mesh_stats": {
                "vertices": len(mesh.vertices),
                "faces": len(mesh.faces),
                "is_watertight": bool(mesh.is_watertight),
                "is_volume": bool(mesh.is_volume),
            },
        }

        if texture_path:
            result["texture_path"] = texture_path

        return result

    def _bake_texture(self, mesh, scene_code, resolution, output_dir):
        """Bake texture atlas for the mesh."""
        import xatlas
        from tsr.bake_texture import bake_texture

        bake_output = bake_texture(mesh, self._model, scene_code, resolution)

        # Export texture
        texture_path = os.path.join(output_dir, "texture.png")
        texture_img = Image.fromarray(
            (bake_output["colors"] * 255.0).astype(np.uint8)
        ).transpose(Image.FLIP_TOP_BOTTOM)
        texture_img.save(texture_path)

        # Re-export mesh with UV mapping
        import xatlas
        uv_mesh_path = os.path.join(output_dir, "mesh_textured.obj")
        xatlas.export(
            uv_mesh_path,
            mesh.vertices[bake_output["vmapping"]],
            bake_output["indices"],
            bake_output["uvs"],
            mesh.vertex_normals[bake_output["vmapping"]],
        )

        return texture_path
