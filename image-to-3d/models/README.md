# Model Weights

## TripoSR (Primary - Local Inference)

TripoSR model weights are automatically downloaded from Hugging Face on first use.

### Manual Download

If you want to pre-download the weights:

```bash
# Using Hugging Face CLI
pip install huggingface-hub
huggingface-cli download stabilityai/TripoSR --local-dir ./triposr

# Or using Python
python3 -c "
from tsr.system import TSR
model = TSR.from_pretrained('stabilityai/TripoSR',
                            config_name='config.yaml',
                            weight_name='model.ckpt')
print('Model downloaded successfully!')
"
```

### Model Details

| Property | Value |
|----------|-------|
| **Name** | TripoSR |
| **Source** | https://huggingface.co/stabilityai/TripoSR |
| **Size** | ~1.5 GB |
| **License** | MIT |
| **VRAM Required** | ~6 GB |
| **Architecture** | Transformer-based feed-forward reconstruction |

### Cache Location

By default, models are cached at:
- `~/.cache/huggingface/hub/` (Hugging Face default)
- Override with `IMG3D_MODEL_CACHE` environment variable

### GPU Compatibility

| GPU | VRAM | Compatible? | Notes |
|-----|------|-------------|-------|
| RTX 3060 | 12 GB | ✅ Ideal | Primary target |
| RTX 3070 | 8 GB | ✅ Good | |
| RTX 3080 | 10 GB | ✅ Good | |
| RTX 3090 | 24 GB | ✅ Excellent | Room for batch |
| RTX 4060 | 8 GB | ✅ Good | |
| RTX 4070 | 12 GB | ✅ Ideal | |
| RTX 4090 | 24 GB | ✅ Excellent | |
| GTX 1080 | 8 GB | ⚠️ Marginal | Older CUDA |
| No GPU | CPU | ⚠️ Slow | ~30s per image |

## Cloud Models (No Local Download Needed)

Cloud backends (Replicate, Stability AI) don't require local model downloads.
They use API keys to access models hosted in the cloud.

### Replicate (TRELLIS)
- Model: `firtoz/trellis`
- No local weights needed
- Requires: `REPLICATE_API_TOKEN` env var

### Stability AI (SF3D)
- Model: Stable Fast 3D
- No local weights needed
- Requires: `STABILITY_API_KEY` env var
