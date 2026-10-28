#!/usr/bin/env bash
# T2 P0 + V7 M10 + P0.4-fix · auto-merge proposals + REAL ledger/helix/tool_call hook
source /etc/nautilus/secrets.env
# V7 M10 · 真 merge worktree branch → master · 不只翻 PG status.
# P0.4-fix · merge 后真 INSERT platform_nau_ledger + helix_blocks + agent_tool_calls · trigger 真关 stake.
# Runs every 15 min via cron. Mints 50 NAU per merge + closes stake.

set -euo pipefail
LOG=/var/log/proposal-auto-merge.log
TS=$(date -Iseconds)
REPO=/home/ubuntu/nautilus-v5
SANDBOX_ROOT=/tmp/v7-sandbox
REWARD=50

PSQL="psql -h localhost -U nautilus_user -d nautilus_production"

# ── Step 1 · pick mergeable rows ──
PICK_SQL=$(cat <<'SQLEOF'
SELECT id, stake_id, proposer_agent_id, filepath
FROM platform_proposal_reviews
WHERE status='pending'
  AND approve_count >= 2
  AND timelock_until IS NOT NULL
  AND timelock_until <= NOW()
ORDER BY id
LIMIT 20;
SQLEOF
)

ROWS=$($PSQL -At -F "|" -c "$PICK_SQL" 2>>"$LOG" || true)

if [[ -z "$ROWS" ]]; then
  echo "$TS no_mergeable" >> "$LOG"
  exit 0
fi

MERGED_OK=0
MERGED_FAIL=0

while IFS='|' read -r ID STAKE_ID PROPOSER FILEPATH; do
  [[ -z "$ID" ]] && continue

  SAFE_AGENT=$(printf '%s' "$PROPOSER" | tr -c 'A-Za-z0-9_-' '_' | cut -c1-64)
  SAFE_STAKE=$(printf '%s' "$STAKE_ID" | tr -c 'A-Za-z0-9_-' '_' | cut -c1-64)
  WT_DIR="$SANDBOX_ROOT/${SAFE_AGENT}-${SAFE_STAKE}"
  BRANCH="v7-sandbox/${SAFE_AGENT}-${SAFE_STAKE}"

  if [[ ! -d "$WT_DIR/.git" ]] && [[ ! -f "$WT_DIR/.git" ]]; then
    echo "$TS merge_skip id=$ID stake=$STAKE_ID reason=no_worktree wt=$WT_DIR" >> "$LOG"
    $PSQL -c "UPDATE platform_proposal_reviews SET status='stale' WHERE id=$ID" \
      >/dev/null 2>>"$LOG" || true
    MERGED_FAIL=$((MERGED_FAIL+1))
    continue
  fi

  # Real merge · branch → master
  if git -C "$REPO" merge --no-ff -m "v7-m10 auto-merge proposal #$ID stake=$STAKE_ID" "$BRANCH" >/dev/null 2>>"$LOG"; then
    MERGE_SHA=$(git -C "$REPO" rev-parse --short HEAD 2>>"$LOG" || echo "unknown")

    # ── P0.4-fix · 真 PG 闭环 in single transaction ──
    # 用 psql variable 安全注入 · 防 SQL injection
    if $PSQL -v ON_ERROR_STOP=1 \
        -v "v_id=$ID" \
        -v "v_stake_id=$STAKE_ID" \
        -v "v_proposer=$PROPOSER" \
        -v "v_merge_sha=$MERGE_SHA" \
        -v "v_reward=$REWARD" \
        -f /usr/local/bin/proposal-auto-merge.post.sql \
        >/dev/null 2>>"$LOG"; then
      git -C "$REPO" worktree remove --force "$WT_DIR" >/dev/null 2>>"$LOG" || true
      git -C "$REPO" branch -D "$BRANCH" >/dev/null 2>>"$LOG" || true
      echo "$TS merge_ok id=$ID stake=$STAKE_ID branch=$BRANCH master=$MERGE_SHA · ledger+helix+tool_call written" >> "$LOG"
      MERGED_OK=$((MERGED_OK+1))
    else
      echo "$TS merge_post_sql_fail id=$ID stake=$STAKE_ID · git merged but PG bookkeeping failed · check log" >> "$LOG"
      MERGED_FAIL=$((MERGED_FAIL+1))
    fi
  else
    echo "$TS merge_fail id=$ID stake=$STAKE_ID branch=$BRANCH · git_merge_returned_nonzero" >> "$LOG"
    git -C "$REPO" merge --abort >/dev/null 2>>"$LOG" || true
    $PSQL -c "UPDATE platform_proposal_reviews SET status='conflict' WHERE id=$ID" \
      >/dev/null 2>>"$LOG" || true
    MERGED_FAIL=$((MERGED_FAIL+1))
  fi
done <<< "$ROWS"

echo "$TS summary merged_ok=$MERGED_OK merged_fail=$MERGED_FAIL" >> "$LOG"
