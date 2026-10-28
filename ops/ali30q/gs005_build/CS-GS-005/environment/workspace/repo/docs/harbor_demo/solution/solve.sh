#!/usr/bin/env bash
set -euo pipefail

# 将 golden.patch 应用到 /workspace
# 注意：cd 路径必须与 Dockerfile WORKDIR 一致
cd /workspace

patch -p1 < /solution/golden.patch
