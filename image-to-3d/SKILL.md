---
name: image-to-3d
description: "Convert a single photograph into a textured 3D model (GLB/OBJ/STL). Supports local GPU inference via TripoSR (RTX 3060) and cloud inference via Replicate API (TRELLIS). Auto-previews output on the 3D Canvas (port 18794). Use when a user wants to turn a photo, image, or picture into a 3D model, mesh, or printable object."
metadata:
  keywords: [3d, image-to-3d, photo-to-3d, mesh, reconstruction, triposr, trellis, glb, obj, stl, 3dprint, ai, conversion]
  port: 18795
  exports: [glb, obj, stl, ply]
  backends: [triposr_local, replicate_cloud, stability_cloud]
---

# Image-to-3D Conversion Skill 📸→🧊

Convert any photograph into a textured 3D model with a single command. Uses AI-powered
reconstruction (TripoSR locally or TRELLIS via cloud) to generate publication-quality meshes
from a single image.

## When to Use

| Trigger | Example |
|---|---|
| User wants to convert a photo to 3D | "Turn this photo into a 3D model" |
| Creating 3D assets from images | "Make a 3D version of snorty_final.png" |
| Preparing images for 3D printing | "Generate an STL from this picture" |
| Quick 3D prototyping from reference | "Create a 3D mesh from this product photo" |
| Batch image-to-3D conversion | "Convert all images in /tmp/photos/ to GLB" |

## Quick Start

```python
import sys
sys.path.insert(0, '/opt/skills/image-to-3d/claude/implementation')
from image_to_3d import ImageTo3D

converter = ImageTo3D()

# Convert an image to 3D (auto-selects best backend)
result = converter.convert(
    image="/path/to/photo.jpg",
    output_format="glb",
    quality="standard",
    preview=True          # auto-opens in 3D Canvas
)

print(f"Model saved to: {result['model_path']}")
print(f"Vertices: {result['metadata']['vertices']}")
print(f"Time: {result['inference_time_ms']}ms")
```

## API Reference

```python
converter = ImageTo3D(backend="auto")  # "auto", "local", "cloud"

# Core conversion
result = converter.convert(
    image: str,                    # file path or URL
    output_format: str = "glb",    # "glb", "obj", "stl", "ply"
    quality: str = "standard",     # "draft", "standard", "high"
    texture_resolution: int = 1024,# 512, 1024, 2048
    output_dir: str = "/tmp/3d-output",
    preview: bool = True,          # open in 3D Canvas
    remove_background: bool = True # auto-remove background
)

# Check backend availability
status = converter.health_check()

# List available backends
backends = converter.list_backends()
```

### Return Value

```python
{
    "success": True,
    "model_path": "/tmp/3d-output/photo.glb",
    "format": "glb",
    "backend_used": "triposr_local",
    "inference_time_ms": 1850,
    "metadata": {
        "vertices": 45230,
        "faces": 90456,
        "texture_resolution": "1024x1024",
        "file_size_bytes": 8453201
    },
    "preview_url": "http://localhost:18794?session=img3d-abc123"
}
```

## Backends

### Local: TripoSR (Default)
- **GPU:** NVIDIA RTX 3060 12GB (or any CUDA GPU with ≥6GB VRAM)
- **Speed:** ~1–2 seconds per image
- **Quality:** ★★★★☆
- **Cost:** Free (local inference)
- **Setup:** Inference server on port 18795

### Cloud: Replicate (TRELLIS)
- **GPU:** Cloud A100 (managed)
- **Speed:** ~10–30 seconds per image
- **Quality:** ★★★★★
- **Cost:** ~$0.10–$1 per generation
- **Setup:** `REPLICATE_API_TOKEN` environment variable

### Cloud: Stability AI (SF3D)
- **GPU:** Cloud (managed)
- **Speed:** ~2 seconds per image
- **Quality:** ★★★★☆
- **Cost:** Credits-based
- **Setup:** `STABILITY_API_KEY` environment variable

## Backend Selection

| Mode | Behavior |
|------|----------|
| `auto` | Try local GPU first, fall back to cloud |
| `local` | Force local TripoSR (fails if GPU unavailable) |
| `cloud` | Force cloud API (requires API key) |

When `quality="high"`, auto mode prefers cloud (TRELLIS) for best results.

## Output Formats

| Format | Use Case | Textures | 3D Canvas |
|--------|----------|----------|-----------|
| **GLB** | Web, Unity, Unreal, 3D Canvas | ✅ Embedded | ✅ |
| **OBJ** | Blender, Maya, general 3D | ✅ Separate MTL | ✅ |
| **STL** | 3D printing (FDM, SLA) | ❌ | ✅ |
| **PLY** | Point clouds, research | ✅ Vertex colors | ❌ |

## 3D Canvas Integration

Generated models automatically preview in the 3D Canvas (port 18794) when `preview=True`:

```python
result = converter.convert("photo.jpg", preview=True)
# Browser opens with interactive 3D view
# User can rotate, zoom, and export to STL/OBJ/GLB
```

## Examples

### Convert Snorty Mascot to 3D
```python
result = converter.convert(
    image="/opt/n8n-copilot-shim/snorty_final.png",
    output_format="glb",
    quality="standard",
    preview=True
)
# → GLB file with textured 3D Snorty mascot
# → Opens in 3D Canvas for interactive preview
```

### High-Quality Cloud Conversion
```python
result = converter.convert(
    image="https://example.com/product.jpg",
    backend="cloud",
    quality="high",
    texture_resolution=2048,
    output_format="glb"
)
```

### Generate STL for 3D Printing
```python
result = converter.convert(
    image="/path/to/object.png",
    output_format="stl",
    quality="standard"
)
# → STL file ready for slicing in Cura/PrusaSlicer
```

## Inference Server

The local backend uses a FastAPI server (port 18795):

```bash
# Start manually (auto-started by skill when needed)
cd /opt/skills/image-to-3d
python -m core.server

# Health check
curl http://localhost:18795/health

# Convert via API
curl -X POST http://localhost:18795/api/convert \
  -F "image=@photo.jpg" \
  -F "format=glb" \
  -F "quality=standard"
```

## Docker Deployment

```bash
cd /opt/skills/image-to-3d/docker
docker compose up -d

# Server available at http://localhost:18795
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REPLICATE_API_TOKEN` | For cloud | Replicate API key |
| `STABILITY_API_KEY` | For SF3D | Stability AI key |
| `IMG3D_SERVER_PORT` | No | Override server port (default: 18795) |
| `IMG3D_SERVER_HOST` | No | Override server host (default: localhost) |
| `IMG3D_MODEL_CACHE` | No | Model weights cache dir |
| `IMG3D_OUTPUT_DIR` | No | Default output directory |
