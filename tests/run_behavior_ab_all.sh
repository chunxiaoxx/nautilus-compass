#!/bin/bash
# Behavior steering A/B · 6 subjects × 20 prompts × judge=kimi-k2.6
# Outputs: paper/results/behavior_ab_<subject>.json + summary table
# n=20 chosen as balance between paired-t-test power and 6-subject CPU budget

# NOTE: NOT using set -e · per-subject failures must not kill remaining subjects
PLUGIN="${PLUGIN:-$HOME/.claude/plugins/nautilus-compass}"
if [ ! -d "$PLUGIN" ]; then
  # allow running from local repo when plugin checkout is absent
  PLUGIN="$(cd "$(dirname "$0")/.."; pwd)"
fi
RESULTS=$PLUGIN/paper/results
mkdir -p "$RESULTS"
LOG_DIR=/c/tmp/nc-eval/ab
mkdir -p "$LOG_DIR"

source "$PLUGIN/scripts/bootstrap_compass_env.sh"
RUN_PYTHON="${PYTHON}"

# === Keys ===
export ARK_API_KEY="b8ed1f14-660b-4422-8da5-f8e2f4af85da"
export GOOGLE_APPLICATION_CREDENTIALS="$HOME/Downloads/chunxiao-vm-260414-de9e73f4697d.json"
export GEMINI_API_KEY=$(grep '^GEMINI_API_KEY=' /c/Users/chunx/Projects/nautilus-v3/.env 2>/dev/null | cut -d= -f2-)
export MINIMAX_API_KEY=$(grep '^MINIMAX_API_KEY=' /c/Users/chunx/quantum-buddha-project/.env | cut -d= -f2-)
export ZMM_MINIMAX_BASE=https://api.minimaxi.com
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

# === Judge: kimi (independent · not in any subject lineup) ===
export ZMM_JUDGE_PROVIDER=ark
export ZMM_JUDGE_MODEL=kimi-k2.6

run_subject() {
    local label="$1"
    local provider="$2"
    local model="$3"
    local n="${4:-20}"
    local log="$LOG_DIR/ab_${label}_$(date +%H%M%S).log"
    echo "============================================="
    echo "  $label  ·  provider=$provider  ·  model=$model  ·  n=$n"
    echo "  log: $log"
    echo "============================================="
    ZMM_SUBJECT_PROVIDER="$provider" ZMM_SUBJECT_MODEL="$model" \
        "$RUN_PYTHON" "$PLUGIN/tests/eval_behavior_ab.py" --n "$n" 2>&1 | tee "$log"
    # archive cache JSON to results/
    latest=$(ls -t "$PLUGIN/.cache/eval_behavior_ab_${provider}"_*.json 2>/dev/null | head -1)
    if [ -n "$latest" ]; then
        cp "$latest" "$RESULTS/behavior_ab_${label}.json"
        echo "  archived → $RESULTS/behavior_ab_${label}.json"
    fi
    echo
}

# === 6 subjects ===
run_subject "gemini-2-5-pro"   "gemini"     "gemini-2.5-pro"          20
run_subject "gemini-2-5-flash" "gemini"     "gemini-2.5-flash"        20
run_subject "minimax-m2-7"     "minimax"    "MiniMax-M2.7-highspeed"  20
run_subject "doubao-seed-2-0"  "ark"        "doubao-seed-2.0-pro"     20
run_subject "deepseek-v3-2"    "ark"        "deepseek-v3.2"           20
run_subject "glm-5-1"          "ark"        "glm-5.1"                 20

echo "============================================="
echo "  ALL 6 SUBJECTS COMPLETE"
echo "  Aggregate JSON files in $RESULTS/"
echo "============================================="
ls -la "$RESULTS/behavior_ab_"*.json 2>/dev/null
