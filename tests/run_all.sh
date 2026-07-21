#!/bin/bash
# nautilus-compass 全套基线评估 · 切 embedder 后跑这个就出全部数字
# Usage:
#   ./tests/run_all.sh                       # 用当前 daemon.py EMBEDDER_MODEL
#   ZMM_EMBEDDER_MODEL=BAAI/bge-m3 ./tests/run_all.sh
#   ZMM_EMBEDDER_MODEL=BAAI/bge-small-zh-v1.5 ./tests/run_all.sh    # 切换旧模型对比

set -euo pipefail
RUN_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
PLUGIN_DIR="${RUN_DIR}/.."
cd "$PLUGIN_DIR"
MODEL="${ZMM_EMBEDDER_MODEL:-(default in daemon.py)}"

# Source bootstrap so exported PYTHON/COMPASS_ROOT remain visible in this shell.
source scripts/bootstrap_compass_env.sh
PYTHON_BIN="${PYTHON}"
if [ -z "${PYTHON_BIN:-}" ]; then
  echo "[run_all] Error: PYTHON not resolved by bootstrap" >&2
  exit 1
fi

if [ -n "${PYTHON_VERBOSE:-}" ]; then
  echo "[run_all] using $("$PYTHON_BIN" --version 2>&1)"
fi

OUT_DIR="${RUN_ALL_OUT_DIR:-.cache/eval-$(date +%Y%m%d-%H%M%S)-$(echo "$MODEL" | tr '/' '_')}"
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
    local rc=0
    set +e
    "$PYTHON_BIN" "$@" 2>&1 | tee "$OUT_DIR/$name.log"
    rc=${PIPESTATUS[0]}
    set -e
    if [ $rc -ne 0 ]; then
      echo "[run_all] ERROR: $name failed (exit $rc)"
    fi
    return $rc
}

run_step() {
    local step_name="$1"; shift
    local log_file="$OUT_DIR/$step_name.log"
    local artifact="$1"; shift
    local rc

    run "$step_name" "$@"
    rc=$?
    STEP_STATUS["$step_name"]=$rc
    STEP_ARTIFACT["$step_name"]="$artifact"
    STEP_LOG["$step_name"]="$log_file"
    if [ "$rc" -ne 0 ]; then
      FAILED=1
    fi
    return 0
}

MANIFEST_PATH="$OUT_DIR/eval-manifest.json"
declare -A STEP_STATUS=([00_selftest]=0 [01_calibrate]=0 [02_drift]=0 [03_recall]=0 [04_recall_tuning_hint]=0)
declare -A STEP_ARTIFACT=([00_selftest]="" [01_calibrate]="" [02_drift]="" [03_recall]="" [04_recall_tuning_hint]="")
declare -A STEP_LOG=([00_selftest]="" [01_calibrate]="" [02_drift]="" [03_recall]="" [04_recall_tuning_hint]="")
FAILED=0

run_step "00_selftest" "" tests/../selftest.py
run_step "01_calibrate" "" tests/eval_calibrate.py
run_step "02_drift" "" tests/eval_drift.py
run_step "03_recall" "$OUT_DIR/eval_recall.json" tests/eval_recall.py --mode all --out "$OUT_DIR/eval_recall.json"

if [ "${STEP_STATUS[03_recall]}" -eq 0 ]; then
  run_step "04_recall_tuning_hint" "$OUT_DIR/eval_recall_tuning_hint.json" ops/eval_recall_tuning_hint.py --artifact "$OUT_DIR/eval_recall.json" --out "$OUT_DIR/eval_recall_tuning_hint.json"
else
  STEP_STATUS["04_recall_tuning_hint"]=99
  STEP_ARTIFACT["04_recall_tuning_hint"]="$OUT_DIR/eval_recall_tuning_hint.json"
  STEP_LOG["04_recall_tuning_hint"]="$OUT_DIR/04_recall_tuning_hint.log"
  echo "[run_all] skipped 04_recall_tuning_hint because 03_recall failed" | tee "${STEP_LOG[04_recall_tuning_hint]}"
fi

cat > "$MANIFEST_PATH" <<EOF
{
  "run_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "embedder": "$MODEL",
  "out_dir": "$OUT_DIR",
  "overall_exit_code": $FAILED,
  "steps": [
    {"name": "00_selftest", "log": "${STEP_LOG[00_selftest]}", "status": ${STEP_STATUS[00_selftest]}},
    {"name": "01_calibrate", "log": "${STEP_LOG[01_calibrate]}", "status": ${STEP_STATUS[01_calibrate]}},
    {"name": "02_drift", "log": "${STEP_LOG[02_drift]}", "status": ${STEP_STATUS[02_drift]}},
    {"name": "03_recall", "log": "${STEP_LOG[03_recall]}", "artifact": "${STEP_ARTIFACT[03_recall]}", "status": ${STEP_STATUS[03_recall]}},
    {"name": "04_recall_tuning_hint", "log": "${STEP_LOG[04_recall_tuning_hint]}", "artifact": "${STEP_ARTIFACT[04_recall_tuning_hint]}", "status": ${STEP_STATUS[04_recall_tuning_hint]}}
  ]
}
EOF

if [ "$FAILED" -ne 0 ]; then
  echo "[run_all] completed with failures · overall_exit_code=$FAILED"
  echo "manifest: $MANIFEST_PATH"
  exit 1
fi

echo "[run_all] recall artifacts:"
echo "  - $OUT_DIR/eval_recall.json"
echo "  - $OUT_DIR/eval_recall_tuning_hint.json"

echo ""
echo "manifest: $MANIFEST_PATH"
echo "==========================================="
echo "  done · 看 $OUT_DIR/*.log"
echo "==========================================="
