# compass v1.0 · multi-stage Dockerfile
# Status: 2026-05-05 · self-host enterprise deployment

FROM python:3.12-slim AS base

# System deps for cryptography (libssl) + sqlite + curl healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ---- builder stage ----
FROM base AS builder
RUN pip install --no-cache-dir --upgrade pip wheel

COPY pyproject.toml LICENSE README.md ./
COPY *.py ./
COPY sdk/ ./sdk/
COPY tests/ ./tests/
COPY tools/ ./tools/
COPY anchors*.json ./
COPY *.sh ./

# Install with all extras for self-host
RUN pip install --no-cache-dir -e .[modelscope,fast-download,e2ee] && \
    pip install --no-cache-dir 'fastapi[standard]' 'uvicorn[standard]' \
                                python-jose[cryptography] cryptography

# ---- runtime stage (slim) ----
FROM base AS runtime

# Create non-root user
RUN groupadd -r compass && useradd -r -g compass -m -d /home/compass compass

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /app /app

# Data + cache directories owned by compass user
RUN mkdir -p /data /root/.cache && chown -R compass:compass /app /data /root/.cache /home/compass

USER compass

# Default to API server · override via docker-compose `command:`
CMD ["uvicorn", "compass_http_v09:app", "--host", "0.0.0.0", "--port", "8765"]

# Metadata labels
LABEL org.opencontainers.image.title="nautilus-compass"
LABEL org.opencontainers.image.description="Cross-agent memory layer with drift detection · LongMemEval-S 56.6%"
LABEL org.opencontainers.image.version="0.9.0-dev"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/chunxiaoxx/nautilus-compass"
