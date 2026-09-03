#!/usr/bin/env python
"""Re-judge the 71 judge-disconnect questions (task #40).

Same judge model & prompt as the arm-a runs (imported from the harness, not
reimplemented) so the verdict stays in-protocol; only adds retry with backoff,
because the original failures were connection-layer (403/timeout), not model
verdicts. Answers are reused verbatim -- subjects are NOT re-run.

Writes vtf/_e2e_diag/arm_a_rows_rejudged.json + prints recomputed by-type.
"""
import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))
import eval_longmemeval_accuracy as H  # noqa: E402  (harness: judge + parser)

ROOT = Path(__file__).resolve().parents[1]
ROWS_IN = ROOT / "vtf/_e2e_diag/arm_a_rows_430.json"
RETRY_FILES = sorted((ROOT / "vtf/_e2e_diag").glob("arm_retry_*.log"))
OUT = ROOT / "vtf/_e2e_diag/arm_a_rows_rejudged.json"
DATASET = ROOT / "vtf/_e2e_diag/longmemeval_s"
BACKOFF = [5, 15, 45]


def load_all_rows():
    rows = json.loads(ROWS_IN.read_text(encoding="utf-8"))
    # merge retry shards (newer files win)
    import glob
    cache = Path.home() / ".claude/plugins/nautilus-compass/.cache"
    files = sorted(glob.glob(str(cache / "longmemeval_acc_m3_only_full_*.jsonl")),
                   key=os.path.getmtime)
    for f in files:
        for line in open(f, encoding="utf-8", errors="ignore"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    r = json.loads(line)
                    rows[r["question_id"]] = r
                except json.JSONDecodeError:
                    pass
    return rows


def main():
    rows = load_all_rows()
    ds = {q["question_id"]: q for q in json.loads(DATASET.read_text(encoding="utf-8"))}
    errors = [r for r in rows.values()
              if "JUDGE_ERROR" in str(r.get("judge_raw", ""))]
    print(f"rows={len(rows)} to-rejudge={len(errors)}", flush=True)
    fixed = 0
    for i, r in enumerate(errors):
        q = ds[r["question_id"]]
        truth = q.get("answer") or q.get("gold") or ""
        for wait in (None, *BACKOFF):
            if wait:
                time.sleep(wait)
            try:
                raw = H.call_vertex_gemini(
                    H.JUDGE_MODEL,
                    H.JUDGE_PROMPT_TMPL.format(question=q["question"],
                                               truth=truth,
                                               answer=r["model_answer"]),
                    max_out_tok=2048, is_judge=True).strip().upper()
                r["judge_raw"] = raw
                r["is_correct"] = H._parse_judge(raw)
                fixed += 1
                break
            except Exception as e:  # noqa: BLE001
                r["judge_raw"] = f"[JUDGE_ERROR: {e}]"
                r["is_correct"] = False
        print(f"[{i+1}/{len(errors)}] {r['question_id'][:8]} "
              f"{r.get('judge_raw', '')[:30]}", flush=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    by = defaultdict(lambda: [0, 0])
    for r in rows.values():
        t = r["question_type"]
        by[t][0] += bool(r["is_correct"])
        by[t][1] += 1
    print(f"fixed={fixed}/{len(errors)}")
    for t, (ok, n) in sorted(by.items()):
        print(f"  {t:26s} {ok}/{n} = {ok/n:.3f}")
    print(f"overall: {sum(v[0] for v in by.values())}/{sum(v[1] for v in by.values())} "
          f"= {sum(v[0] for v in by.values())/sum(v[1] for v in by.values()):.3f}")


if __name__ == "__main__":
    main()
