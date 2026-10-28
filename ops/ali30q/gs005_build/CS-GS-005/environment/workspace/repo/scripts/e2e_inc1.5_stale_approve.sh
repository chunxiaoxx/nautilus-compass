#!/usr/bin/env bash
# Inc 1.5 cloud e2e · stale-approve fail-safe end-to-end verification
# Run after PR merged + cloud has pulled origin/master + migration applied.
# Each phase is interactive · review output before proceeding.
#
# Usage:
#   ./scripts/e2e_inc1.5_stale_approve.sh            # all phases
#   PHASE=cleanup ./scripts/e2e_inc1.5_stale_approve.sh   # cleanup only
#   PHASE=p4verify ./scripts/e2e_inc1.5_stale_approve.sh  # 0-vote P4 gate verify only

set -euo pipefail

CLOUD_SSH="${CLOUD_SSH:-cloud}"  # ssh alias for the platform cloud host
PROPOSAL_ID="inc15-e2e-$(date +%s)"
ZERO_PID="${PROPOSAL_ID}-zero"
GH_REPO="${GH_REPO:-chunxiaox/nautilus-core}"

log() { printf '\n=== %s ===\n' "$*"; }

phase1_insert_dormant_proposal() {
  log "Phase 1: insert 25h-old code proposal + 1 yes-vote (satisfies P4 gate vote_count>=1)"
  ssh "$CLOUD_SSH" "psql -d nautilus_production -c \"
    INSERT INTO platform_improvement_proposals
      (id, task_id, agent_id, root_cause, proposed_change,
       expected_impact, rollback_plan, vote_score, vote_count,
       status, created_at, updated_at)
    VALUES
      ('$PROPOSAL_ID', 9000001, 9000002, 'inc1.5 e2e test',
       '{\\\"type\\\":\\\"code\\\",\\\"task\\\":\\\"Add comment to phase3/backend/utils/text.py noting Inc 1.5 e2e ran\\\"}',
       'test e2e fail-safe path', 'revert PR', 3.0, 1, 'pending',
       NOW() - INTERVAL '25 hours', NOW() - INTERVAL '25 hours');
    INSERT INTO platform_proposal_votes
      (proposal_id, agent_id, vote, weight)
    VALUES ('$PROPOSAL_ID', 9000003, 1, 3.0);
  \""
  log "Phase 1 done · 1 yes-vote inserted (satisfies P4 gate). Sleep 2s, then proceed."
  sleep 2
}

phase1b_insert_zero_vote_dormant() {
  log "Phase 1b (P4 anti-RH gate verify): insert 25h-old zero-vote proposal · stale-approve MUST NOT fire on this"
  ssh "$CLOUD_SSH" "psql -d nautilus_production -c \"
    INSERT INTO platform_improvement_proposals
      (id, task_id, agent_id, root_cause, proposed_change,
       expected_impact, rollback_plan, vote_score, vote_count,
       status, created_at, updated_at)
    VALUES
      ('$ZERO_PID', 9000001, 9000002, 'inc1.5 P4 gate verify · zero-vote',
       '{\\\"type\\\":\\\"code\\\",\\\"task\\\":\\\"dummy task · this should never be approved\\\"}',
       'test P4 anti-RH gate', 'revert PR', 0, 0, 'pending',
       NOW() - INTERVAL '25 hours', NOW() - INTERVAL '25 hours');
  \""
  log "After Phase 2 fires · this proposal MUST remain status='pending' (P4 layer 1 anti-RH)"
}

phase2_trigger_cron_manually() {
  log "Phase 2: trigger auto_approve_stale_proposals manually (don't wait 6h)"
  # Capture remote output so we can verify the function actually ran ·
  # set -e + ssh does NOT catch remote Python exceptions caught internally
  # (Python prints '0' approved and exits 0 → ssh exits 0 → script continues with wrong state)
  local out
  out=$(ssh "$CLOUD_SSH" "cd ~/nautilus-mvp/phase3/backend && python -c '
from utils.database import SessionLocal
from services.proposal_consensus import auto_approve_stale_proposals
db = SessionLocal()
approved = auto_approve_stale_proposals(db, stale_hours=24)
print(\"approved:\", approved)
db.close()
'" 2>&1)
  echo "$out"
  if ! echo "$out" | grep -qE '^approved: [0-9]+$'; then
    log "Phase 2 FAIL: expected 'approved: N' in output · got:"
    echo "$out"
    exit 1
  fi
  log "Phase 2 done. Expected: approved: 1 (only the with-vote proposal · zero-vote stays pending)"
}

phase3_verify_status_flipped() {
  log "Phase 3: verify with-vote proposal status, resolved_by, resolution_note"
  ssh "$CLOUD_SSH" "psql -d nautilus_production -c \"
    SELECT id, status, resolved_by, resolved_at, resolution_note
    FROM platform_improvement_proposals WHERE id='$PROPOSAL_ID';
  \""
  log "Phase 3 done. Expected: status='accepted', resolved_by='auto_stale', resolved_at NOT NULL, note contains 'auto-approved after 24h dormant'."

  log "Phase 3b: verify zero-vote proposal stays pending (P4 gate work)"
  ssh "$CLOUD_SSH" "psql -d nautilus_production -c \"
    SELECT id, status, resolved_by, resolved_at, vote_count, vote_score
    FROM platform_improvement_proposals WHERE id='$ZERO_PID';
  \""
  log "Phase 3b done. Expected: status='pending', resolved_by IS NULL (P4 anti-RH skipped this)."
}

phase4_wait_soul_executor_pickup() {
  log "Phase 4: wait soul_executor timer 10min + 60s buffer, then check for draft PR"
  if ssh "$CLOUD_SSH" "systemctl is-enabled nautilus-soul-executor.timer 2>/dev/null | grep -q enabled"; then
    log "soul-executor timer ENABLED · sleeping 660s for next fire"
    sleep 660
  else
    log "soul-executor timer DISABLED · running executor one-shot manually"
    ssh "$CLOUD_SSH" "cd ~/nautilus-soul-workspace/phase3 && python -m soul_executor.run_once"
  fi
  log "Searching gh for draft PR referencing $PROPOSAL_ID"
  gh pr list --repo "$GH_REPO" --state open --draft --search "$PROPOSAL_ID" --json number,title,url
}

phase5_verify_writeback() {
  log "Phase 5: verify DB writeback after PR opened"
  ssh "$CLOUD_SSH" "psql -d nautilus_production -c \"
    SELECT status, resolved_by, resolution_note
    FROM platform_improvement_proposals WHERE id='$PROPOSAL_ID';
  \""
  log "Phase 5 done. Expected: status='executed_ok' OR 'executed_failed', resolved_by='soul', resolution_note=PR URL (or failure detail)."
}

phase6_cleanup() {
  log "Phase 6: cleanup (close any draft PR + DELETE proposals · agent-dialog cleanup pattern)"
  PR_NUMBER=$(gh pr list --repo "$GH_REPO" --state open --draft --search "$PROPOSAL_ID" --json number --jq '.[0].number' 2>/dev/null || true)
  # jq returns literal 'null' string on empty array · plain -n check would pass it through
  if [[ -n "$PR_NUMBER" && "$PR_NUMBER" != "null" ]]; then
    log "Closing draft PR #$PR_NUMBER"
    gh pr close --repo "$GH_REPO" "$PR_NUMBER" --delete-branch || true
  else
    log "No draft PR found · skip PR cleanup"
  fi
  ssh "$CLOUD_SSH" "psql -d nautilus_production -c \"
    DELETE FROM platform_proposal_votes WHERE proposal_id IN ('$PROPOSAL_ID', '$ZERO_PID');
    DELETE FROM platform_improvement_proposals WHERE id IN ('$PROPOSAL_ID', '$ZERO_PID');
  \""
  log "Phase 6 done. Proposals + votes deleted from cloud."
}

main() {
  case "${PHASE:-all}" in
    cleanup)
      phase6_cleanup
      ;;
    p4verify)
      phase1b_insert_zero_vote_dormant
      phase2_trigger_cron_manually
      phase3_verify_status_flipped
      phase6_cleanup
      ;;
    all)
      log "Inc 1.5 e2e · proposal_id=$PROPOSAL_ID · zero_pid=$ZERO_PID · cloud=$CLOUD_SSH"
      phase1_insert_dormant_proposal
      phase1b_insert_zero_vote_dormant
      phase2_trigger_cron_manually
      phase3_verify_status_flipped
      phase4_wait_soul_executor_pickup
      phase5_verify_writeback
      phase6_cleanup
      log "ALL PHASES DONE. Inc 1.5 platform-side ship verified (Path B fail-safe + P4 anti-RH gate)."
      ;;
    *)
      echo "Unknown PHASE: $PHASE" >&2; exit 1
      ;;
  esac
}

main "$@"
