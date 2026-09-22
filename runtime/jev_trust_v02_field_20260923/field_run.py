# -*- coding: utf-8 -*-
"""v0.2 双极性实测:域 4 抽样 40 题跑 decide_symmetric(协议见 PROTOCOL.md)。"""
import json
import sys
import time
from pathlib import Path

from jev_trust import TrustedJev

OUT = Path(__file__).parent
D3 = Path(__file__).parent.parent / "jev_trust_domain3_20260922"
D4 = Path(__file__).parent.parent / "jev_trust_domain4_20260922"
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"

SPEC_REVIEW = ("You are labeling embodied-robotics telemetry. The data is a sequence of 20 "
               "joint-angle readings (radians) from one joint. Label the sequence "
               "NEEDS_REVIEW if and only if ANY of these holds: "
               "(1) some pair of consecutive readings differs by more than 0.8 in absolute value (spike); "
               "(2) there are 5 or more consecutive identical readings (stuck sensor); "
               "(3) any reading is outside the range [-3.14, 3.14] (limit violation); "
               "(4) |first reading - last reading| > 1.5 AND the sequence is monotonically increasing "
               "or monotonically decreasing overall (drift). "
               "Otherwise label it OK. Answer strictly by applying these four rules to the readings.")
SPEC_OK = ("You are labeling embodied-robotics telemetry. The data is a sequence of 20 "
           "joint-angle readings (radians) from one joint. Label the sequence OK if and "
           "only if ALL of these conditions hold: "
           "(1) every pair of consecutive readings differs by at most 0.8 in absolute value; "
           "(2) there is no run of 5 or more consecutive identical readings; "
           "(3) every reading is within the range [-3.14, 3.14]; "
           "(4) the sequence does NOT drift, that is, NOT (|first reading - last reading| > 1.5 "
           "AND the sequence is monotonically increasing or decreasing overall). "
           "If any condition fails, the sequence is not OK. "
           "Answer strictly by applying these four pass conditions to the readings.")


def pick_sample():
    """50 items: spike-defect 15 (14 missed + 1 caught), stuck-defect 15
    (13 missed + 2 caught), clean 20 (control — d4 got all right)."""
    ds = json.loads((D3 / "decision_set.json").read_text(encoding="utf-8"))
    dec4 = {}
    for line in (D4 / "session.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["kind"] == "call":
            dec4[r["qid"]] = (r["decision"] == "yes")  # yes=OK in domain 4
    rows = []
    for pat, exp_missed in (("spike", 14), ("stuck", 13)):
        cand = [d for d in ds if d["pattern"] == pat and d["truth"] == 1]
        missed = [d for d in cand if dec4[d["qid"]]]
        caught = [d for d in cand if not dec4[d["qid"]]]
        assert len(missed) == exp_missed, (pat, len(missed))
        rows += [(d, f"{pat}-missed") for d in missed]
        rows += [(d, f"{pat}-caught") for d in caught]
    clean = [d for d in ds if d["pattern"] in ("smooth", "noise")][:20]
    rows += [(d, "clean") for d in clean]
    return rows


def main():
    rows = pick_sample()
    assert len(rows) == 50
    api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]
    jev = TrustedJev(api_key=api_key, domain="bipolarity-field-test",
                     log_path=str(OUT / "session.jsonl"))
    (OUT / "sample.json").write_text(
        json.dumps([{"qid": d["qid"], "pattern": d["pattern"], "truth": d["truth"],
                     "group": g} for d, g in rows], ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")

    out_rows = []
    t0 = time.time()
    for n, (d, group) in enumerate(rows):
        qid = d["qid"]
        state = {"joint_readings": d["state"]["joint_readings"]}
        try:
            r = jev.decide_symmetric(state, {qid: {
                "question": {"type": "noul", "instructions": SPEC_REVIEW},
                "opposite": {"type": "noul", "instructions": SPEC_OK}}})[qid]
            # consistent -> decision is on REVIEW polarity (yes=review); truth=1=defect
            sym_dec = r.decision == "yes"
            out_rows.append({"qid": qid, "pattern": d["pattern"], "group": group,
                             "truth": d["truth"], "polarity_consistent": r.polarity_consistent,
                             "sym_decision_says_defect": sym_dec,
                             "conflict": not r.polarity_consistent})
        except Exception as e:
            out_rows.append({"qid": qid, "group": group, "error": str(e)[:120]})
        if (n + 1) % 10 == 0:
            print(f"  {n+1}/50 done")
        time.sleep(0.25)
    print(f"calls done in {time.time()-t0:.0f}s")

    sig = jev.sign_log()
    (OUT / "pubkey.txt").write_text(jev.keys.pub_hex + "\n", encoding="utf-8", newline="\n")
    (OUT / "field_results.json").write_text(
        json.dumps(out_rows, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    # aggregate by group family
    ok_rows = [r for r in out_rows if "error" not in r]
    def agg(label, sub):
        conflicts = sum(1 for r in sub if r["conflict"])
        usable = [r for r in sub if not r["conflict"]]
        correct = sum(1 for r in usable if r["sym_decision_says_defect"] == (r["truth"] == 1))
        print(f"{label}: n={len(sub)} conflicts={conflicts} "
              f"({conflicts/max(1,len(sub))*100:.0f}%) | consistent-decision acc="
              f"{correct}/{len(usable)}")
    agg("ALL", ok_rows)
    agg("HARD (spike+stuck defects)", [r for r in ok_rows if r["group"].endswith("missed") or r["group"].endswith("caught")])
    agg("  missed-in-d4", [r for r in ok_rows if r["group"].endswith("missed")])
    agg("  caught-in-d4", [r for r in ok_rows if r["group"].endswith("caught")])
    agg("CLEAN control", [r for r in ok_rows if r["group"] == "clean"])


if __name__ == "__main__":
    sys.exit(main())
