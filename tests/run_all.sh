#!/bin/bash
# nautilus-compass 全套基线评估 · 切 embedder 后跑这个就出全部数字
# Usage:
#   ./tests/run_all.sh                       # 用当前 daemon.py EMBEDDER_MODEL
#   ZMM_EMBEDDER_MODEL=BAAI/bge-m3 ./tests/run_all.sh
#   ZMM_EMBEDDER_MODEL=BAAI/bge-small-zh-v1.5 ./tests/run_all.sh    # 切换旧模型对比

set -e
RUN_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PLUGIN_DIR="${RUN_DIR}/.."
cd "$PLUGIN_DIR"
MODEL="${ZMM_EMBEDDER_MODEL:-(default in daemon.py)}"

bash scripts/bootstrap_compass_env.sh
PYTHON="${PYTHON}"
if [ -n "${PYTHON_VERBOSE:-}" ]; then
  echo "[run_all] using $("$PYTHON" --version 2>&1)"
fi

OUT_DIR=".cache/eval-$(date +%Y%m%d-%H%M%S)-$(echo "$MODEL" | tr '/' '_')"
mkdir -p "$OUT_DIR"

echo "==========================================="
echo "  nautilus-compass eval suite"
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
run "03_recall"     tests/eval_recall.py --mode all --out "$OUT_DIR/eval_recall.json"
run "03_recall_tuning_hint" ops/eval_recall_tuning_hint.py --artifact "$OUT_DIR/eval_recall.json" --out "$OUT_DIR/eval_recall_tuning_hint.json"

MANIFEST_PATH="$OUT_DIR/eval-manifest.json"
cat > "$MANIFEST_PATH" <<EOF
{
  "run_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "embedder": "$MODEL",
  "out_dir": "$OUT_DIR",
  "steps": [
    {"name": "00_selftest", "log": "$OUT_DIR/00_selftest.log"},
    {"name": "01_calibrate", "log": "$OUT_DIR/01_calibrate.log"},
    {"name": "02_drift", "log": "$OUT_DIR/02_drift.log"},
    {
      "name": "03_recall",
      "log": "$OUT_DIR/03_recall.log",
      "artifact": "$OUT_DIR/eval_recall.json"
    },
    {
      "name": "03_recall_tuning_hint",
      "log": "$OUT_DIR/03_recall_tuning_hint.log",
      "artifact": "$OUT_DIR/eval_recall_tuning_hint.json"
    }
  ]
}
EOF
echo ""
echo "manifest: $MANIFEST_PATH"
echo "==========================================="
echo "  done · 看 $OUT_DIR/*.log"
echo "==========================================="
