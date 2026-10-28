#!/usr/bin/env bash
set -euo pipefail
cd /workspace
patch -p1 < /solution/golden.patch
