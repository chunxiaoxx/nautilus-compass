#!/usr/bin/env bash
# income 链批量编排(cloud 端):produce(完整解轨迹)→ persist verdict → canonical verify → PATCH。
# 顺序执行——verifier 计时敏感,并发 CPU 争用会打破 determinism 自检。
# 用法: bash tools/run_income_chain.sh <task_dir1> <task_dir2> ...(相对 ~/genopt_live)
set -u
cd "$(dirname "$0")/.."
set -a; . ~/.claude/.cache/.fde_api_secrets.env 2>/dev/null; set +a
PLATFORM="${PLATFORM:-http://localhost:8000}"
AGENT_ID="${AGENT_ID:-9000009}"
SRC="cloud-genopt-runner-${AGENT_ID}"
STAMP="$(date +%Y%m%d)"

for t in "$@"; do
  echo "=== [$t] start $(date +%H:%M:%S)"
  traj="$t/gpt55_trajectory_cloud_${STAMP}.json"
  if [ ! -f "$traj" ]; then
    python3 tools/gpt55_local_runner.py --task-dir "$t" --rounds 3 --model gpt-5.5 \
        --out "$traj" || { echo "[$t] RUNNER_FAIL"; continue; }
  else
    echo "[$t] trajectory exists, skip produce"
  fi
  out=$(python3 tools/persist_trajectory_verdict.py --task-dir "$t" \
        --trajectory "$(basename "$traj")" --producer-agent-id "$AGENT_ID" \
        --source "$SRC" --platform-url "$PLATFORM" 2>&1) \
      || { echo "[$t] PERSIST_FAIL: $out"; continue; }
  echo "$out"
  vid=$(echo "$out" | grep -oE 'verdict_id=[^ ]+' | head -1 | cut -d= -f2)
  [ -n "$vid" ] || { echo "[$t] NO_VERDICT_ID"; continue; }
  python3 tools/soul_canonical_verify.py --task-dir "$t" --trajectory "$(basename "$traj")" \
      --verdict-id "$vid" --platform-url "$PLATFORM"
  echo "[$t] verify_exit=$? $(date +%H:%M:%S)"
done
echo "=== ALL DONE $(date +%H:%M:%S)"
