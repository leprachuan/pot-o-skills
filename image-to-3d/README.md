# Image-to-3D Conversion Skill

Convert any photograph into a textured 3D model (GLB/OBJ/STL) using AI-powered reconstruction.

## Features

- **Single Image → 3D Model** in 1–2 seconds (local) or 10–30 seconds (cloud)
- **Dual Backend:** Local GPU (TripoSR) + Cloud API (Replicate/TRELLIS)
- **Multiple Formats:** GLB, OBJ, STL, PLY
- **3D Canvas Preview:** Auto-opens in the interactive 3D viewer (port 18794)
- **Runtime Agnostic:** Works with Claude, Copilot CLI, and Gemini
- **Automatic Fallback:** Cloud backup when local GPU unavailable

## Quick Start

```python
import sys
sys.path.insert(0, '/opt/skills/image-to-3d/claude/implementation')
from image_to_3d import ImageTo3D

converter = ImageTo3D()
result = converter.convert("photo.jpg")
print(f"3D model: {result['model_path']}")
```

## Backends

| Backend | Speed | Quality | Cost | GPU Required |
|---------|-------|---------|------|-------------|
| TripoSR (local) | ~1-2s | ★★★★☆ | Free | ✅ RTX 3060+ |
| Replicate (cloud) | ~10-30s | ★★★★★ | ~$0.10/model | ❌ |
| Stability AI (cloud) | ~2s | ★★★★☆ | Credits | ❌ |

## Requirements

### For Local Inference
- NVIDIA GPU with ≥6GB VRAM (tested on RTX 3060 12GB)
- CUDA 12.x + PyTorch
- TripoSR model weights (~1.5GB, auto-downloaded)

### For Cloud Inference
- `REPLICATE_API_TOKEN` environment variable (for Replicate/TRELLIS)
- `STABILITY_API_KEY` environment variable (for Stability AI/SF3D)

### Python Dependencies
```
requests>=2.28.0
Pillow>=9.0.0
trimesh>=4.0.0
numpy>=1.24.0
```

## Docker Deployment

```bash
cd docker/
docker compose up -d
# Server available at http://localhost:18795
```

## API Examples

### Convert with automatic backend selection
```python
result = converter.convert("photo.jpg", quality="standard")
```

### Force cloud for highest quality
```python
result = converter.convert("photo.jpg", backend="cloud", quality="high")
```

### Generate STL for 3D printing
```python
result = converter.convert("object.png", output_format="stl")
```

### Batch conversion
```python
results = converter.batch_convert(
    ["img1.jpg", "img2.jpg", "img3.jpg"],
    output_format="glb"
)
```

## Example: Snorty Mascot

```python
result = converter.convert(
    "/opt/n8n-copilot-shim/snorty_final.png",
    output_format="glb",
    quality="standard",
    preview=True
)
# → Opens 3D Snorty in the browser canvas
```

## Inference Server

The local backend uses a FastAPI server:

```bash
# Direct start
cd /opt/skills/image-to-3d
python -m core.server

# With Docker
cd docker && docker compose up -d
```

### Server Endpoints
- `GET /health` — Server health + GPU status
- `POST /api/convert` — Convert image to 3D
- `GET /api/models` — List available models

## Architecture

```
Image Input → Preprocessing → Backend Selection → Inference → Post-processing → Output
                                    ↓                                              ↓
                              ┌─────┴─────┐                                  3D Canvas
                              │           │                                  Preview
                         TripoSR    Replicate
                         (Local)    (Cloud)
```

## License

MIT — TripoSR and TRELLIS are both MIT-licensed.
