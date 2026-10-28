#!/bin/bash
# mint_auto.sh — autonomous GenOpt income mint: pick first UN-minted candidate task,
# then run the full mint chain via mint_one.sh. Designed to run off-dialog from a
# systemd timer (binding-DONE ③: producer 成 systemd timer 脱离对话框).
#
# Behaviour:
#   * derive task_uid per candidate (Task.md `task_uid:` line, else genopt_<dirname>)
#   * skip any task_uid already external_verified (avoids wasting a producer call
#     re-minting — server enforces once-per-task anyway, this just saves LLM cost)
#   * first un-minted candidate -> mint_one.sh <dir>
#   * fail-soft everywhere: no candidate / all minted / all providers down -> exit 0
#
# When all producers are down (current state 2026-07-07) this exits cleanly having
# done no harm; when quota returns the next timer tick auto-mints. autonomous provenance
# is stamped via mint_one's --source (autonomous-timer-*).
set -uo pipefail

TOOLS="$HOME/genopt_live/tools"
DEL="$HOME/genopt_delivery/tasks"
LIVE="$HOME/genopt_live"

# candidate task dirs (must contain verification/evaluate.py + data/).
# Deterministic-solvable domains (binpack/cache) FIRST — they mint quota-free via
# deterministic_producer, so the timer keeps earning income even with every LLM down.
# Globs pick up newly-generated instances (bin_packing_ffd_v*, cache_lru_v*) automatically.
shopt -s nullglob
CANDIDATES=(
  "$LIVE"/bin_packing_ffd_v* "$LIVE"/cache_lru_v* "$LIVE"/tsp_tsplib_v*
  "$DEL/jssp_la_15x10_v1_001" "$DEL/jssp_la_15x15_v1_001"
)
shopt -u nullglob

DSN="$(grep -hoE 'postgresql://[^ "'"'"']+nautilus_production' "$HOME/nautilus-v5/.env" | head -1)"
export PGCONNECT_TIMEOUT=8
verified="$(psql "$DSN" -tAc "SELECT task_uid FROM fde_verdicts WHERE external_verified=true;" 2>/dev/null)"

derive_uid() {
  # MUST match persist_trajectory_verdict.py: read frontier_eval/delivery_metadata.txt
  # task_uid, else fall back to genopt_<dirname>. (Task.md has no task_uid line.)
  local d="$1" uid="" meta="$d/frontier_eval/delivery_metadata.txt"
  if [ -f "$meta" ]; then
    uid="$(grep -m1 '^task_uid:' "$meta" 2>/dev/null | cut -d: -f2- | tr -d '[:space:]')"
  fi
  [ -z "$uid" ] && uid="genopt_$(basename "$d")"
  printf '%s' "$uid"
}

for d in "${CANDIDATES[@]}"; do
  [ -f "$d/verification/evaluate.py" ] || { echo "[mint_auto] skip $(basename "$d"): no verifier"; continue; }
  uid="$(derive_uid "$d")"
  if printf '%s\n' "$verified" | grep -qxF "$uid"; then
    echo "[mint_auto] skip $(basename "$d"): task_uid=$uid already external_verified"
    continue
  fi
  echo "[mint_auto] selected UN-minted task=$(basename "$d") task_uid=$uid -> mint_one (autonomous)"
  # 标记自治产出:persist 读 AUTONOMOUS=1 → verdict artifacts.autonomous=true(SSOT v4 自治率口径)
  export AUTONOMOUS=1
  exec bash "$TOOLS/mint_one.sh" "$d"
done

echo "[mint_auto] no un-minted candidate available (all minted or none valid). exit 0."
exit 0
