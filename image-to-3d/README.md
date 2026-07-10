# Image-to-3D Conversion Skill

Convert any photograph into a textured 3D model (GLB/OBJ/STL) using AI-powered reconstruction.

## Features

- **Single Image → 3D Model** using true volumetric reconstruction (not depth maps)
- **Triple Backend:** Local GPU (TripoSR) + CPU (TripoSR) + Cloud API (Replicate/TRELLIS)
- **Multiple Formats:** GLB, OBJ, STL, PLY
- **3D Canvas Preview:** Auto-opens in the interactive 3D viewer (port 18794)
- **Runtime Agnostic:** Works with Claude, Copilot CLI, and Gemini
- **Automatic Fallback:** GPU → Cloud → CPU (always produces true 3D)

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

| Backend | Speed | Quality | Cost | Requirements |
|---------|-------|---------|------|-------------|
| TripoSR (GPU) | ~1-2s | ★★★★☆ | Free | RTX 3060+ (6GB VRAM) |
| Replicate (cloud) | ~10-30s | ★★★★★ | ~$0.10/model | API token |
| Stability AI (cloud) | ~2s | ★★★★☆ | Credits | API key |
| TripoSR (CPU) | ~2-5min | ★★★★☆ | Free | 8GB+ RAM |

### Backend Selection (auto mode)

1. **GPU server** — fastest, if TripoSR server is running
2. **Cloud API** — fast, if API keys are configured
3. **CPU TripoSR** — slowest but always available, true 3D reconstruction

The CPU backend produces the same quality as GPU — it runs the full TripoSR
neural network model, just on CPU cores instead of GPU. This guarantees
**true volumetric 3D geometry** (not depth-map reliefs) in all environments.

## Requirements

### For Local GPU Inference
- NVIDIA GPU with ≥6GB VRAM (tested on RTX 3060 12GB)
- CUDA 12.x + PyTorch
- TripoSR model weights (~1.5GB, auto-downloaded)

### For Cloud Inference
- `REPLICATE_API_TOKEN` environment variable (for Replicate/TRELLIS)
- `STABILITY_API_KEY` environment variable (for Stability AI/SF3D)

### For CPU Inference (no GPU/API keys needed)
- PyTorch (CPU), transformers, trimesh, einops, omegaconf, rembg, PyMCubes
- 8GB+ available RAM
- TripoSR source + weights (~1.5GB, auto-downloaded from HuggingFace)

### Python Dependencies
```
requests>=2.28.0
Pillow>=9.0.0
trimesh>=4.0.0
numpy>=1.24.0
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
    "/tmp/webui_uploads/8ef8c07e/miqihl4vq4541.jpg",
    output_format="glb",
    quality="standard",
    output_dir="/opt/3DMODELS/snorty_3d_improved",
    preview=True
)
# → True 3D volumetric mesh: 73K vertices, 147K faces, watertight
# → Exports GLB/OBJ/STL ready for 3D printing or CAD
```

## Architecture

```
Image Input → Preprocessing → Backend Selection → Inference → Post-processing → Output
                                     ↓                                              ↓
                          ┌──────────┼──────────┐                              3D Canvas
                          │          │          │                               Preview
                     TripoSR    Replicate   TripoSR
                     (GPU)      (Cloud)      (CPU)
```

## License

MIT — TripoSR and TRELLIS are both MIT-licensed.
