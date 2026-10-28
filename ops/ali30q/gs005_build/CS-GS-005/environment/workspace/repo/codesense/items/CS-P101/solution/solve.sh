#!/usr/bin/env bash
set -euo pipefail
# CS-P101 金标(甲方demo形态):应用golden.patch到workspace
cd /workspace
patch -p1 < /solution/golden.patch
