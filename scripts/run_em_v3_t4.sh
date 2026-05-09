#!/usr/bin/env bash
# Wrapper to launch a v3 EverMemBench run on T4.
# Activates the conda env that has FlagEmbedding + sentence_transformers,
# requires DEEPSEEK_API_KEY in env, runs the patched evermembench_bge.py
# with per-question JSONL persistence.
#
# Usage on T4:
#   export DEEPSEEK_API_KEY=sk-...
#   bash run_em_v3_t4.sh
#
# Output:
#   ~/em_bge_v3.log              · stdout/stderr (progress)
#   ~/em_bge_v3_per_question.jsonl · one record per QA · 500 lines
#
# ETA: ~5.6h on T4 · ~$3 in DeepSeek API tokens.
set -euo pipefail

if [[ -z "${DEEPSEEK_API_KEY:-}" ]]; then
    echo "ERR · set DEEPSEEK_API_KEY before running" >&2
    exit 2
fi

# shellcheck disable=SC1091
source /home/ubuntu/mf/bin/activate c

cd /home/ubuntu

# Sanity: the patched runner must have JSONL persistence wired in.
if ! grep -q "JSONL_OUT.write" /home/ubuntu/evermembench_bge.py; then
    echo "ERR · runner not patched · run patch_evermembench_persist.py first" >&2
    exit 3
fi

# Wire the JSONL output path explicitly so this run's data is named after v3.
sed -i 's|/home/ubuntu/em_bge_v2_per_question.jsonl|/home/ubuntu/em_bge_v3_per_question.jsonl|' \
    /home/ubuntu/evermembench_bge.py || true

LOG=/home/ubuntu/em_bge_v3.log
echo "$(date -Iseconds) · launching v3 run · log=$LOG"

# Background nohup so the run survives ssh disconnect.
nohup python -u /home/ubuntu/evermembench_bge.py > "$LOG" 2>&1 < /dev/null &
PID=$!
echo "PID=$PID · tail $LOG to follow"
disown
