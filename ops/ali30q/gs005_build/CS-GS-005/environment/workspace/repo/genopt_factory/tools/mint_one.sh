#!/bin/bash
# mint_one.sh — one-command GenOpt income mint with multi-provider producer fallback.
#
# Built 2026-07-07 for quota-restore readiness: all 3 producers were down at build time
# (GPT5.5/qixuw empty-content, Minimax 429, Bailian 429). This auto-selects whichever
# provider recovers first, then runs the full income chain and reports the income delta.
#
# Chain: produce full-solution trajectory (first working provider)
#        -> persist_trajectory_verdict (producer 9000009)
#        -> soul_canonical_verify (reproduce -> PATCH external_verified)
#        -> report income before/after.
#
# Fail-soft: if NO provider produces a valid trajectory, logs and exits 0
# (safe to run from a systemd timer without alarming on a transient quota outage).
#
# Usage: bash mint_one.sh [TASK_DIR]   (default: jssp_la_15x10_v1_001)
set -uo pipefail

TD="${1:-$HOME/genopt_delivery/tasks/jssp_la_15x10_v1_001}"
PRODUCER=9000009
TOOLS="$HOME/genopt_live/tools"
STAMP="$(date +%Y%m%d_%H%M%S)"
TRAJ="$TD/mint_traj_${STAMP}.json"
PLATFORM="http://localhost:8000"

# load secrets (both env files; strip CRLF later per-var)
set -a
[ -f "$HOME/.claude/.cache/.fde_api_secrets.env" ] && source "$HOME/.claude/.cache/.fde_api_secrets.env" 2>/dev/null
[ -f "$HOME/nautilus-v5/.env" ] && source "$HOME/nautilus-v5/.env" 2>/dev/null
set +a

DSN="$(grep -hoE 'postgresql://[^ "'"'"']+nautilus_production' "$HOME/nautilus-v5/.env" | head -1)"
export PGCONNECT_TIMEOUT=8
income_before="$(psql "$DSN" -tAc "SELECT total_income FROM agent_survival WHERE agent_id='$PRODUCER';" 2>/dev/null | tr -d '[:space:]')"
echo "[mint_one] task=$(basename "$TD") producer=$PRODUCER income_before=${income_before:-?}"

strip() { printf '%s' "$1" | tr -d '\r\n'; }

# provider table: name | model | base | key_var
PROVIDERS=(
  "qixuw|gpt-5.5|https://v2.qixuw.com/v1|OPENAI_API_KEY"
  "minimax|MiniMax-M2.7-highspeed|https://api.minimaxi.com/v1|MINIMAX_API_KEY"
  "bailian|qwen3.7-max|${BAILIAN_OPENAI_BASE:-}|BAILIAN_API_KEY"
)

produced=""
# deterministic producer first — quota-free for combinatorial-optimization domains
# (cache/binpack/...): known optimal algorithms, no LLM/quota needed.
if python3 "$TOOLS/deterministic_producer.py" "$TD" "$TRAJ" >"$TD/mint_det_${STAMP}.log" 2>&1; then
  echo "[mint_one] deterministic producer solved it (quota-free)"
  produced="deterministic"
fi

if [ -z "$produced" ]; then
for row in "${PROVIDERS[@]}"; do
  IFS='|' read -r pname pmodel pbase pkeyvar <<< "$row"
  pbase="$(strip "$pbase")"; pkey="$(strip "${!pkeyvar:-}")"
  [ -z "$pbase" ] || [ -z "$pkey" ] && { echo "[mint_one] $pname: no base/key, skip"; continue; }
  echo "[mint_one] try provider=$pname model=$pmodel ..."
  OPENAI_BASE_URL="$pbase" OPENAI_API_KEY="$pkey" \
    timeout 900 python3 "$TOOLS/gpt55_local_runner.py" \
      --task-dir "$TD" --rounds 1 --model "$pmodel" --out "$TRAJ" \
      >"$TD/mint_${pname}_${STAMP}.log" 2>&1
  # valid full-solution trajectory? (best_round_source len>500, gap>0)
  ok="$(python3 - "$TRAJ" <<'PY' 2>/dev/null
import json,sys
try:
    t=json.load(open(sys.argv[1]))
    src=t.get("best_round_source") or t.get("best_solution") or ""
    gap=t.get("gap_closed") or 0
    print("OK" if (len(src)>500 and float(gap or 0)>0) else "BAD")
except Exception:
    print("BAD")
PY
)"
  if [ "$ok" = "OK" ]; then echo "[mint_one] provider=$pname produced valid trajectory"; produced="$pname"; break; fi
  echo "[mint_one] provider=$pname failed/degraded (see mint_${pname}_${STAMP}.log)"; rm -f "$TRAJ"
done
fi

if [ -z "$produced" ]; then
  echo "[mint_one] NO working producer (deterministic unsupported + all LLM providers down). income unchanged=${income_before:-?}. exit 0 (fail-soft)."
  exit 0
fi

echo "[mint_one] persist verdict (producer $PRODUCER) ..."
# FdeVerdict.source is varchar(32) — keep the source string <=32 chars or persist 500s.
SRC="gmint-${produced}"; SRC="${SRC:0:32}"
persist_out="$(python3 "$TOOLS/persist_trajectory_verdict.py" \
  --task-dir "$TD" --trajectory "$TRAJ" --producer-agent-id "$PRODUCER" \
  --source "$SRC" --platform-url "$PLATFORM" 2>&1)"
echo "$persist_out"
verdict_id="$(printf '%s' "$persist_out" | grep -oE 'verdict-genopt-[A-Za-z0-9_.:-]+' | head -1)"
if [ -z "$verdict_id" ]; then echo "[mint_one] could not parse verdict_id; abort."; exit 0; fi
echo "[mint_one] verdict_id=$verdict_id"

echo "[mint_one] canonical verify + PATCH external_verified ..."
python3 "$TOOLS/soul_canonical_verify.py" \
  --task-dir "$TD" --trajectory "$TRAJ" --verdict-id "$verdict_id" --platform-url "$PLATFORM"
vrc=$?
echo "[mint_one] canonical_verify exit=$vrc (0=MATCH+PATCH)"

income_after="$(psql "$DSN" -tAc "SELECT total_income FROM agent_survival WHERE agent_id='$PRODUCER';" 2>/dev/null | tr -d '[:space:]')"
echo "[mint_one] DONE provider=$produced verdict=$verdict_id income ${income_before:-?} -> ${income_after:-?}"
