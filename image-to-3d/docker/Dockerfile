FROM nvidia/cuda:12.2.2-runtime-ubuntu22.04

LABEL maintainer="FosterbotHome"
LABEL description="TripoSR Image-to-3D Inference Server"

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV IMG3D_SERVER_HOST=0.0.0.0
ENV IMG3D_SERVER_PORT=18795
ENV IMG3D_MODEL_CACHE=/app/models

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv git wget \
    libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r requirements.txt

# Install TripoSR dependencies
RUN pip3 install --no-cache-dir \
    torch torchvision --index-url https://download.pytorch.org/whl/cu122 \
    && pip3 install --no-cache-dir \
    fastapi uvicorn \
    tsr trimesh numpy Pillow requests

# Copy application code
COPY core/ /app/core/

# Create output directory
RUN mkdir -p /app/output /app/models

# Pre-download model weights (optional — remove to download on first use)
# RUN python3 -c "from tsr.system import TSR; TSR.from_pretrained('stabilityai/TripoSR')"

EXPOSE 18795

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python3 -c "import requests; r=requests.get('http://localhost:18795/health'); exit(0 if r.ok else 1)" \
    || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
