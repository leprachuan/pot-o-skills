"""FastAPI inference server for local TripoSR image-to-3D conversion.

Run with: python -m core.server
Or: uvicorn core.server:app --host 0.0.0.0 --port 18795

Requires: TripoSR, PyTorch with CUDA, and an NVIDIA GPU.
"""

import os
import io
import sys
import time
import uuid
import logging
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("image-to-3d.server")

# Server configuration
HOST = os.environ.get("IMG3D_SERVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("IMG3D_SERVER_PORT", "18795"))
OUTPUT_DIR = os.environ.get("IMG3D_OUTPUT_DIR", "/tmp/3d-output")
MODEL_CACHE = os.environ.get("IMG3D_MODEL_CACHE", os.path.expanduser("~/.cache/image-to-3d"))

# Global model reference (lazy-loaded)
_model = None
_model_load_time = None


def _check_gpu():
    """Check GPU availability and return info."""
    try:
        import torch

        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_total = torch.cuda.get_device_properties(0).total_mem / (1024**2)
            vram_used = torch.cuda.memory_allocated(0) / (1024**2)
            vram_free = vram_total - vram_used
            return {
                "available": True,
                "name": gpu_name,
                "vram_total_mb": int(vram_total),
                "vram_used_mb": int(vram_used),
                "vram_free_mb": int(vram_free),
            }
    except ImportError:
        pass
    return {"available": False, "error": "PyTorch CUDA not available"}


def _load_model():
    """Lazy-load the TripoSR model."""
    global _model, _model_load_time

    if _model is not None:
        return _model

    logger.info("Loading TripoSR model (this may take a few seconds)...")
    start = time.time()

    try:
        import torch
        from tsr.system import TSR

        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        _model = TSR.from_pretrained(
            "stabilityai/TripoSR",
            config_name="config.yaml",
            weight_name="model.ckpt",
        )
        _model.renderer.set_chunk_size(8192)
        _model.to(device)

        _model_load_time = time.time() - start
        logger.info(f"TripoSR model loaded in {_model_load_time:.1f}s on {device}")
        return _model

    except ImportError as e:
        logger.error(f"TripoSR not installed: {e}")
        logger.error("Install with: pip install tsr torch torchvision")
        raise RuntimeError(f"TripoSR dependencies not installed: {e}")
    except Exception as e:
        logger.error(f"Failed to load TripoSR model: {e}")
        raise


def _run_inference(image_path: str, mc_resolution: int = 256, texture_resolution: int = 1024) -> str:
    """Run TripoSR inference on a single image.

    Returns path to the generated OBJ file.
    """
    import torch
    import numpy as np
    from PIL import Image

    model = _load_model()
    device = next(model.parameters()).device

    # Load and preprocess image
    image = Image.open(image_path).convert("RGB")

    # Run inference
    with torch.no_grad():
        scene_codes = model([image], device=device)

    # Extract mesh
    meshes = model.extract_mesh(scene_codes, resolution=mc_resolution)
    mesh = meshes[0]

    # Save to OBJ
    job_id = uuid.uuid4().hex[:8]
    job_dir = os.path.join(OUTPUT_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    stem = Path(image_path).stem
    obj_path = os.path.join(job_dir, f"{stem}.obj")

    # Export mesh
    mesh.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1]]))

    if texture_resolution > 0:
        import trimesh

        mesh.export(obj_path)
    else:
        mesh.export(obj_path)

    return obj_path


def create_app():
    """Create the FastAPI application."""
    try:
        from fastapi import FastAPI, UploadFile, File, Form
        from fastapi.responses import FileResponse, JSONResponse
    except ImportError:
        logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn")
        raise

    app = FastAPI(
        title="Image-to-3D Inference Server",
        description="Local TripoSR inference server for image-to-3D conversion",
        version="1.0.0",
    )

    @app.get("/health")
    async def health():
        gpu = _check_gpu()
        return {
            "status": "healthy",
            "gpu": gpu,
            "model_loaded": _model is not None,
            "model_name": "triposr",
            "model_load_time_s": round(_model_load_time, 2) if _model_load_time else None,
            "uptime_seconds": int(time.time() - _start_time),
        }

    @app.get("/api/models")
    async def list_models():
        return {
            "models": [
                {
                    "name": "triposr",
                    "description": "TripoSR: Fast 3D Object Reconstruction",
                    "vram_required_mb": 6000,
                    "loaded": _model is not None,
                }
            ]
        }

    @app.post("/api/convert")
    async def convert(
        image: UploadFile = File(...),
        format: str = Form("glb"),
        mc_resolution: int = Form(256),
        texture_resolution: int = Form(1024),
    ):
        # Save uploaded image
        job_id = uuid.uuid4().hex[:8]
        job_dir = os.path.join(OUTPUT_DIR, job_id)
        os.makedirs(job_dir, exist_ok=True)

        input_path = os.path.join(job_dir, f"input_{image.filename}")
        with open(input_path, "wb") as f:
            content = await image.read()
            f.write(content)

        try:
            start = time.time()
            obj_path = _run_inference(input_path, mc_resolution, texture_resolution)
            inference_ms = int((time.time() - start) * 1000)

            # Convert to requested format
            if format != "obj":
                try:
                    import trimesh

                    mesh = trimesh.load(obj_path)
                    output_path = obj_path.replace(".obj", f".{format}")
                    mesh.export(output_path, file_type=format)
                except ImportError:
                    return JSONResponse(
                        {"success": False, "error": "trimesh required for format conversion"},
                        status_code=500,
                    )
            else:
                output_path = obj_path

            return FileResponse(
                output_path,
                media_type="application/octet-stream",
                filename=Path(output_path).name,
                headers={"X-Inference-Time-Ms": str(inference_ms)},
            )

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return JSONResponse({"success": False, "error": str(e)}, status_code=500)

    @app.get("/api/output/{job_id}/{filename}")
    async def download_output(job_id: str, filename: str):
        file_path = os.path.join(OUTPUT_DIR, job_id, filename)
        if not os.path.exists(file_path):
            return JSONResponse({"error": "File not found"}, status_code=404)
        return FileResponse(file_path)

    return app


_start_time = time.time()

# Create the app instance for uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn

    logging.basicConfig(level=logging.INFO)
    logger.info(f"Starting Image-to-3D inference server on {HOST}:{PORT}")
    uvicorn.run("core.server:app", host=HOST, port=PORT, reload=False)
