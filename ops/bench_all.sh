#!/usr/bin/env bash
# nautilus-compass · bench_all · 全方位基准统一入口
# 用法:
#   bash ops/bench_all.sh l0      # 快层(免 GPU):eval_recall + eval_drift
#   bash ops/bench_all.sh l1 [N]  # 标准层(GPU/云凭据):LongMemEval-S N 题(默认 30)
#   bash ops/bench_all.sh all     # l0 + l1
# 前置:l1 需 .cache/longmem_s.json + 云端凭据;全部层需本地 daemon 已起
# 产出:docs/evidence/bench_scorecard_<ts>.json + /tmp/bench_*.log 原始日志
set -uo pipefail
cd "$(dirname "$0")/.."
LAYER="${1:-l0}"
TS=$(date +%Y%m%d_%H%M%S)
OUT="docs/evidence/bench_scorecard_${TS}.json"
mkdir -p docs/evidence docs/evidence 2>/dev/null
PY="${PYTHON:-python}"
PY="${PY//\\//}"   # Windows 反斜杠在 eval 里会被吞,统一成正斜杠
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*)
    # Windows 固定配方:WindowsApps python3.13 + PYTHONPATH=C:/pylibs(312 无 sentence_transformers)
    PY="python"
    [ -n "${PYTHONPATH:-}" ] || export PYTHONPATH="C:/pylibs"
    ;;
esac

RESULTS=""
run() { # name, cmd
  echo "── [$1] $2"
  if eval "$2" > "/tmp/bench_$1.log" 2>&1; then ST=ok; else ST=FAIL; fi
  RESULTS="$RESULTS{\"name\":\"$1\",\"status\":\"$ST\",\"log\":\"/tmp/bench_$1.log\"},"
  echo "   -> $ST"
}

if [ "$LAYER" = "l0" ] || [ "$LAYER" = "all" ]; then
  run recall "$PY tests/eval_recall.py"
  run drift  "$PY tests/eval_drift.py"
fi
if [ "$LAYER" = "l1" ] || [ "$LAYER" = "all" ]; then
  N="${2:-30}"
  run lme "ZMM_LONGMEMEVAL_PATH=.cache/longmem_s.json $PY tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --subset $N"
fi
[ -n "$RESULTS" ] || { echo "未知层: $LAYER(可用 l0/l1/all)"; exit 1; }

printf '{"ts":"%s","layer":"%s","results":[%s]}\n' \
  "$(date +%Y-%m-%dT%H:%M:%S%z)" "$LAYER" "${RESULTS%,}" > "$OUT"
echo "记分卡: $OUT · 原始日志: /tmp/bench_*.log"
