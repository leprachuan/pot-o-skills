#!/bin/bash
set -e

echo "========================================="
echo "Image-to-3D Inference Server"
echo "========================================="
echo "Host: ${IMG3D_SERVER_HOST:-0.0.0.0}"
echo "Port: ${IMG3D_SERVER_PORT:-18795}"
echo "Model Cache: ${IMG3D_MODEL_CACHE:-/app/models}"
echo ""

# Check GPU
python3 -c "
import torch
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB')
else:
    print('WARNING: No GPU detected. Inference will be slow on CPU.')
" 2>/dev/null || echo "WARNING: PyTorch CUDA check failed"

echo ""
echo "Starting server..."

exec python3 -m uvicorn core.server:app \
    --host "${IMG3D_SERVER_HOST:-0.0.0.0}" \
    --port "${IMG3D_SERVER_PORT:-18795}" \
    --workers 1 \
    --log-level info
