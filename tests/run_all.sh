#!/bin/bash
# zenmind-mem 全套基线评估 · 切 embedder 后跑这个就出全部数字
# Usage:
#   ./tests/run_all.sh                       # 用当前 daemon.py EMBEDDER_MODEL
#   ZMM_EMBEDDER_MODEL=BAAI/bge-m3 ./tests/run_all.sh
#   ZMM_EMBEDDER_MODEL=BAAI/bge-small-zh-v1.5 ./tests/run_all.sh    # 切回旧模型对比

set -e
PLUGIN_DIR="$(dirname "$(readlink -f "$0")")/.."
cd "$PLUGIN_DIR"

PYTHON="${PYTHON:-python3}"
MODEL="${ZMM_EMBEDDER_MODEL:-(default in daemon.py)}"

OUT_DIR=".cache/eval-$(date +%Y%m%d-%H%M%S)-$(echo "$MODEL" | tr '/' '_')"
mkdir -p "$OUT_DIR"

echo "==========================================="
echo "  zenmind-mem eval suite"
echo "  embedder: $MODEL"
echo "  output:   $OUT_DIR"
echo "==========================================="

run() {
    local name="$1"; shift
    echo ""
    echo "=== $name ==="
    "$PYTHON" "$@" 2>&1 | tee "$OUT_DIR/$name.log"
}

run "00_selftest"   tests/../selftest.py
run "01_calibrate"  tests/eval_calibrate.py
run "02_drift"      tests/eval_drift.py
run "03_recall"     tests/eval_recall.py

echo ""
echo "==========================================="
echo "  done · 看 $OUT_DIR/*.log"
echo "==========================================="
