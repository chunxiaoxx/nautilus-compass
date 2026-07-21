#!/bin/bash
# Profile script for repeatable Compass benchmark runs.
# - one-click full run_all
# - manifest + recall/tuning artifact sanity check
# - produces summary.json for downstream comparisons

set -euo pipefail

RUN_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"
REPO_DIR="$(cd "$RUN_DIR/.." && pwd)"
cd "$REPO_DIR"

MODEL="${ZMM_EMBEDDER_MODEL:-(default in daemon.py)}"
PROFILE_DIR=".cache/bench-profile-$(date +%Y%m%d-%H%M%S)-$(echo "$MODEL" | tr '/' '_')"
mkdir -p "$PROFILE_DIR"

echo "[bench_profile] start run_all profile"
echo "[bench_profile] model: $MODEL"
echo "[bench_profile] output: $PROFILE_DIR"

RUN_ALL_OUT_DIR="$PROFILE_DIR" bash tests/run_all.sh > "$PROFILE_DIR/run_all.log" 2>&1
echo "[bench_profile] run_all done"

MANIFEST_PATH="$PROFILE_DIR/eval-manifest.json"
if [ ! -f "$MANIFEST_PATH" ]; then
  echo "[bench_profile] ERROR: manifest missing: $MANIFEST_PATH" >&2
  exit 1
fi

python - <<'PY' "$MANIFEST_PATH"
import json
import os
import sys

manifest_path = sys.argv[1]
with open(manifest_path, "r", encoding="utf-8") as f:
    m = json.load(f)

out_dir = m.get("out_dir")
if not out_dir or not os.path.isdir(out_dir):
    raise SystemExit(2)

steps = m.get("steps", [])
if not steps:
    raise SystemExit(3)

if m.get("overall_exit_code", 0) != 0:
    raise SystemExit(4)

required = {"03_recall", "04_recall_tuning_hint"}
names = {s.get("name") for s in steps}
if not required.issubset(names):
    missing = ", ".join(sorted(required - names))
    raise SystemExit(f"missing steps: {missing}")

recall = next((s for s in steps if s.get("name") == "03_recall"), {})
tune = next((s for s in steps if s.get("name") == "04_recall_tuning_hint"), {})
for item in (recall, tune):
    if item.get("status", 0) != 0:
        raise SystemExit(5)

if not os.path.isfile(recall.get("artifact", "")) or not os.path.isfile(tune.get("artifact", "")):
    raise SystemExit(6)

print("OK", m.get("run_at"), m.get("embedder"))
PY

RECALL_ARTIFACT="$(python - <<'PY' "$MANIFEST_PATH"
import json, sys
m=json.load(open(sys.argv[1], encoding='utf-8'))
for s in m.get("steps", []):
    if s.get("name") == "03_recall":
        print(s.get("artifact", ""))
        break
PY
)"

TUNING_ARTIFACT="$(python - <<'PY' "$MANIFEST_PATH"
import json, sys
m=json.load(open(sys.argv[1], encoding='utf-8'))
for s in m.get("steps", []):
    if s.get("name") == "04_recall_tuning_hint":
        print(s.get("artifact", ""))
        break
PY
)"

PROFILE_HINT_PATH="$PROFILE_DIR/eval_recall_tuning_hint_profile.json"
python ops/eval_recall_tuning_hint.py --artifact "$RECALL_ARTIFACT" --out "$PROFILE_HINT_PATH" > "$PROFILE_DIR/tuning_hint_profile.log" 2>&1

GUARDED_RECALL_ARTIFACT="$PROFILE_DIR/eval_recall_guarded.json"
python tests/eval_recall.py --mode all --signal-policy guarded --out "$GUARDED_RECALL_ARTIFACT" > "$PROFILE_DIR/eval_recall_guarded.log" 2>&1

GUARDED_HINT_ARTIFACT="$PROFILE_DIR/eval_recall_guarded_tuning_hint.json"
python ops/eval_recall_tuning_hint.py --artifact "$GUARDED_RECALL_ARTIFACT" --out "$GUARDED_HINT_ARTIFACT" > "$PROFILE_DIR/eval_recall_guarded_tuning_hint.log" 2>&1

ROUTED_RECALL_ARTIFACT="$PROFILE_DIR/eval_recall_routed.json"
python tests/eval_recall.py --mode all --signal-policy routed --out "$ROUTED_RECALL_ARTIFACT" > "$PROFILE_DIR/eval_recall_routed.log" 2>&1

ROUTED_HINT_ARTIFACT="$PROFILE_DIR/eval_recall_routed_tuning_hint.json"
python ops/eval_recall_tuning_hint.py --artifact "$ROUTED_RECALL_ARTIFACT" --out "$ROUTED_HINT_ARTIFACT" > "$PROFILE_DIR/eval_recall_routed_tuning_hint.log" 2>&1

POLICY_GATE_ARTIFACT="$PROFILE_DIR/recall_policy_gate.json"
python ops/recall_policy_gate.py --raw "$RECALL_ARTIFACT" --guarded "$GUARDED_RECALL_ARTIFACT" --routed "$ROUTED_RECALL_ARTIFACT" --out "$POLICY_GATE_ARTIFACT" > "$PROFILE_DIR/recall_policy_gate.log" 2>&1

POLICY_PREFLIGHT_ARTIFACT="$PROFILE_DIR/recall_policy_preflight.json"
POLICY_RECOMMENDED_DEFAULT="$(python - <<'PY' "$POLICY_GATE_ARTIFACT"
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8")).get("promotion", {}).get("recommended_default", "flat"))
PY
)"
python ops/recall_policy_preflight.py --policy-gate "$POLICY_GATE_ARTIFACT" --target-policy "$POLICY_RECOMMENDED_DEFAULT" --out "$POLICY_PREFLIGHT_ARTIFACT" > "$PROFILE_DIR/recall_policy_preflight.log" 2>&1

python - <<'PY' "$RECALL_ARTIFACT" "$TUNING_ARTIFACT" "$PROFILE_HINT_PATH" "$GUARDED_RECALL_ARTIFACT" "$GUARDED_HINT_ARTIFACT" "$ROUTED_RECALL_ARTIFACT" "$ROUTED_HINT_ARTIFACT" "$POLICY_GATE_ARTIFACT" "$POLICY_PREFLIGHT_ARTIFACT" "$MANIFEST_PATH" "$PROFILE_DIR/summary.json"
import json
import sys
from pathlib import Path

(
    recall_artifact,
    tuning_artifact,
    hint_artifact,
    guarded_recall_artifact,
    guarded_hint_artifact,
    routed_recall_artifact,
    routed_hint_artifact,
    policy_gate_artifact,
    policy_preflight_artifact,
    manifest_path,
    summary_path,
) = map(Path, sys.argv[1:])

rec = json.loads(recall_artifact.read_text(encoding="utf-8"))
hint = json.loads(hint_artifact.read_text(encoding="utf-8"))
guarded = json.loads(guarded_recall_artifact.read_text(encoding="utf-8"))
routed = json.loads(routed_recall_artifact.read_text(encoding="utf-8"))
policy_gate = json.loads(policy_gate_artifact.read_text(encoding="utf-8"))
policy_preflight = json.loads(policy_preflight_artifact.read_text(encoding="utf-8"))
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

summary = {
    "run_at": manifest.get("run_at"),
    "embedder": manifest.get("embedder"),
    "out_dir": manifest.get("out_dir"),
    "n_memories": rec.get("meta", {}).get("n_memories"),
    "result_summary": rec.get("result_summary", {}),
    "raw_recall_artifact": str(recall_artifact),
    "guarded_recall_artifact": str(guarded_recall_artifact),
    "routed_recall_artifact": str(routed_recall_artifact),
    "guarded_result_summary": guarded.get("result_summary", {}),
    "routed_result_summary": routed.get("result_summary", {}),
    "recommendations_count": len(rec.get("recommendations", [])),
    "tuning_risk": hint.get("risk"),
    "tuning_next_actions": len(hint.get("next_actions", [])),
    "policy_gate_artifact": str(policy_gate_artifact),
    "policy_gate": policy_gate.get("gate"),
    "policy_recommended_default": policy_gate.get("promotion", {}).get("recommended_default"),
    "raw_lifecycle_allowed": policy_gate.get("promotion", {}).get("raw_lifecycle_allowed"),
    "policy_preflight_artifact": str(policy_preflight_artifact),
    "policy_preflight": policy_preflight.get("status"),
    "policy_preflight_target": policy_preflight.get("target_policy"),
}
summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print("summary_written", summary_path)
PY

echo "[bench_profile] done"
echo "  manifest: $MANIFEST_PATH"
echo "  summary:  $PROFILE_DIR/summary.json"
