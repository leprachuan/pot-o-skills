# Image-to-3D Inference Server API Reference

## Base URL

```
http://localhost:18795
```

## Endpoints

### GET /health

Returns server health status including GPU availability.

**Response:**
```json
{
  "status": "healthy",
  "gpu": {
    "available": true,
    "name": "NVIDIA GeForce RTX 3060",
    "vram_total_mb": 12288,
    "vram_used_mb": 6100,
    "vram_free_mb": 6188
  },
  "model_loaded": true,
  "model_name": "triposr",
  "model_load_time_s": 4.2,
  "uptime_seconds": 3600
}
```

---

### POST /api/convert

Convert an image to a 3D model.

**Request:** `multipart/form-data`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `image` | file | required | Image file (PNG, JPEG, WebP) |
| `format` | string | "glb" | Output format: glb, obj, stl, ply |
| `mc_resolution` | int | 256 | Marching cubes resolution (128/256/512) |
| `texture_resolution` | int | 1024 | Texture resolution (512/1024/2048) |

**Example:**
```bash
curl -X POST http://localhost:18795/api/convert \
  -F "image=@photo.jpg" \
  -F "format=glb" \
  -F "mc_resolution=256" \
  -F "texture_resolution=1024" \
  --output model.glb
```

**Response:** Binary file (the 3D model) with header `X-Inference-Time-Ms`.

**Error Response:**
```json
{
  "success": false,
  "error": "Description of what went wrong"
}
```

---

### GET /api/models

List available models on the server.

**Response:**
```json
{
  "models": [
    {
      "name": "triposr",
      "description": "TripoSR: Fast 3D Object Reconstruction",
      "vram_required_mb": 6000,
      "loaded": true
    }
  ]
}
```

---

### GET /api/output/{job_id}/{filename}

Download a previously generated model file.

**Response:** Binary file or 404 if not found.

---

## Quality Presets

| Preset | MC Resolution | Texture Resolution | Speed | Detail |
|--------|--------------|-------------------|-------|--------|
| draft | 128 | 512 | Fastest | Low |
| standard | 256 | 1024 | Balanced | Medium |
| high | 512 | 2048 | Slowest | High |

## Error Codes

| HTTP Status | Meaning |
|-------------|---------|
| 200 | Success |
| 400 | Bad request (invalid image, parameters) |
| 500 | Server error (inference failed, GPU OOM) |
| 503 | Server unavailable (model not loaded) |
