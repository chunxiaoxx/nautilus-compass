"""compass verify V5 SWE candidates · dual-arm (strong vs doubao).

Reads V5's swe_passk_glm_*.jsonl files, runs official swebench harness on both
strong_candidates[0] and doubao_solution, classifies as A-class if:
  - strong resolved (tests pass)
  - doubao unresolved (tests fail)

Output: swe_aclass_fuel_verified_<timestamp>.jsonl with A-class records.
"""
import json, io, os, subprocess, sys, glob
from datetime import datetime
from pathlib import Path

# Config
CANDIDATE_FILES = [
    "/home/ubuntu/swe_passk_glm_nondjango.jsonl",
    "/home/ubuntu/swe_passk_glm_noneasy.jsonl",
    "/home/ubuntu/swe_passk_nondjango.jsonl",
    "/home/ubuntu/swe_passk_noneasy.jsonl",
]
WORK_DIR = "/mnt/datadisk0/swe-rsi"
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
STRONG_PRED = f"/home/ubuntu/compass_verify_strong_{TIMESTAMP}.jsonl"
DOUBAO_PRED = f"/home/ubuntu/compass_verify_doubao_{TIMESTAMP}.jsonl"
STRONG_RUN_ID = f"compass_verify_strong_{TIMESTAMP}"
DOUBAO_RUN_ID = f"compass_verify_doubao_{TIMESTAMP}"
MODEL = "compass-verify"

# Load candidates
candidates = []
for f in CANDIDATE_FILES:
    if not os.path.exists(f):
        print(f"[warn] {f} not found, skipping")
        continue
    for line in io.open(f, encoding="utf-8"):
        if line.strip():
            candidates.append(json.loads(line))

print(f"[compass-verify] loaded {len(candidates)} candidates from {len(CANDIDATE_FILES)} files")

# Build predictions (strong = first candidate, doubao = doubao_solution)
strong_preds = []
doubao_preds = []
for c in candidates:
    task_id = c["task_id"]
    if c.get("strong_candidates") and len(c["strong_candidates"]) > 0:
        strong_preds.append({
            "instance_id": task_id,
            "model_name_or_path": MODEL,
            "model_patch": c["strong_candidates"][0],
        })
    if c.get("doubao_solution"):
        doubao_preds.append({
            "instance_id": task_id,
            "model_name_or_path": MODEL,
            "model_patch": c["doubao_solution"],
        })

print(f"[compass-verify] {len(strong_preds)} strong predictions, {len(doubao_preds)} doubao predictions")

# Write prediction files
with io.open(STRONG_PRED, "w", encoding="utf-8") as f:
    for p in strong_preds:
        f.write(json.dumps(p) + "\n")
with io.open(DOUBAO_PRED, "w", encoding="utf-8") as f:
    for p in doubao_preds:
        f.write(json.dumps(p) + "\n")

print(f"[compass-verify] wrote {STRONG_PRED} and {DOUBAO_PRED}")

# Run official harness (strong arm)
cmd_strong = [
    sys.executable, "-m", "swebench.harness.run_evaluation",
    "--dataset_name", "princeton-nlp/SWE-bench_Lite",
    "--predictions_path", STRONG_PRED,
    "--run_id", STRONG_RUN_ID,
    "--max_workers", "4",
    "--cache_level", "env",
]
print(f"[compass-verify] running STRONG arm:\n  " + " ".join(cmd_strong))
sys.stdout.flush()
rc_strong = subprocess.call(cmd_strong, cwd=WORK_DIR)
print(f"[compass-verify] strong arm rc={rc_strong}")

# Run official harness (doubao arm)
cmd_doubao = [
    sys.executable, "-m", "swebench.harness.run_evaluation",
    "--dataset_name", "princeton-nlp/SWE-bench_Lite",
    "--predictions_path", DOUBAO_PRED,
    "--run_id", DOUBAO_RUN_ID,
    "--max_workers", "4",
    "--cache_level", "env",
]
print(f"[compass-verify] running DOUBAO arm:\n  " + " ".join(cmd_doubao))
sys.stdout.flush()
rc_doubao = subprocess.call(cmd_doubao, cwd=WORK_DIR)
print(f"[compass-verify] doubao arm rc={rc_doubao}")

# Read reports
def read_report(run_id):
    reports = glob.glob(f"{WORK_DIR}/{MODEL}.{run_id}.json") + \
              glob.glob(f"{WORK_DIR}/*{run_id}*.json")
    if not reports:
        return None
    try:
        return json.load(open(reports[0]))
    except Exception as e:
        print(f"[warn] failed to read report {run_id}: {e}")
        return None

strong_report = read_report(STRONG_RUN_ID)
doubao_report = read_report(DOUBAO_RUN_ID)

if not strong_report or not doubao_report:
    print("[compass-verify] ERROR: missing reports")
    sys.exit(1)

# Extract resolved/unresolved sets
strong_resolved = set(strong_report.get("resolved_ids", []))
doubao_resolved = set(doubao_report.get("resolved_ids", []))

print(f"[compass-verify] strong resolved: {len(strong_resolved)} {sorted(strong_resolved)}")
print(f"[compass-verify] doubao resolved: {len(doubao_resolved)} {sorted(doubao_resolved)}")

# Classify A-class: strong resolved AND doubao unresolved
aclass_ids = strong_resolved - doubao_resolved
print(f"[compass-verify] A-class (strong✓ doubao✗): {len(aclass_ids)} {sorted(aclass_ids)}")

# Write A-class fuel records
OUTPUT = f"/home/ubuntu/swe_aclass_fuel_verified_{TIMESTAMP}.jsonl"
aclass_records = []
for c in candidates:
    if c["task_id"] in aclass_ids:
        record = {
            "task_id": c["task_id"],
            "kind": "swe",
            "strong_solution": c["strong_candidates"][0],
            "doubao_solution": c["doubao_solution"],
            "verified_at": TIMESTAMP,
            "verifier": "compass_official_harness",
        }
        aclass_records.append(record)

with io.open(OUTPUT, "w", encoding="utf-8") as f:
    for r in aclass_records:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"[compass-verify] wrote {len(aclass_records)} A-class records to {OUTPUT}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"Total candidates: {len(candidates)}")
print(f"Strong resolved: {len(strong_resolved)}")
print(f"Doubao resolved: {len(doubao_resolved)}")
print(f"A-class (strong✓ doubao✗): {len(aclass_ids)}")
print(f"Output: {OUTPUT}")
print("="*60)
