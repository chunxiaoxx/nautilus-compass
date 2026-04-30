# Nautilus Compass · single-image with both daemon + gateway
# - Container start: launches BGE daemon → waits for ready → starts uvicorn
# - For high-throughput production: split into 2 images (daemon-only + gateway-only)
#   and run gateway as N-replica deployment behind LB

FROM python:3.12-slim

# System deps for sentence-transformers / numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/compass

# Layer 1: deps (cached unless requirements change)
COPY pyproject.toml ./
RUN pip install --no-cache-dir \
    sentence-transformers>=2.7 \
    fastapi>=0.110 uvicorn[standard]>=0.27 \
    modelscope>=1.10

# Layer 2: app code
COPY . /opt/compass/

# Pre-download bge-m3 at build time (≈2.27 GB · skip if you mount a volume instead)
ARG PREDOWNLOAD_MODEL=true
RUN if [ "$PREDOWNLOAD_MODEL" = "true" ]; then \
      python -c "from modelscope import snapshot_download; \
                 snapshot_download('BAAI/bge-m3', cache_dir='/root/.cache/modelscope/hub')"; \
    fi

# Daemon TCP + gateway HTTP
EXPOSE 9876 8765

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONUTF8=1 \
    COMPASS_DAEMON_HOST=127.0.0.1 \
    COMPASS_DAEMON_PORT=9876 \
    COMPASS_DEFAULT_PROJECT=default

# entrypoint: start daemon, wait, then exec gateway
COPY ops/entrypoint.sh /opt/compass/ops/entrypoint.sh
RUN chmod +x /opt/compass/ops/entrypoint.sh

HEALTHCHECK --interval=30s --timeout=5s --start-period=120s --retries=3 \
    CMD curl -fs http://127.0.0.1:8765/readyz || exit 1

ENTRYPOINT ["/opt/compass/ops/entrypoint.sh"]
