# -*- coding: utf-8 -*-
"""jev-trust 域 4:OK-first 措辞对照实验(协议见 PROTOCOL.md)。

复用域 3 decision_set(单一变量=措辞),问「Is OK?」,record 传 1-truth。
工件落本目录。
"""
import hashlib
import json
import sys
import time
from pathlib import Path

from jev_trust import TrustedJev

OUT = Path(__file__).parent
DS3 = Path(__file__).parent.parent / "jev_trust_domain3_20260922" / "decision_set.json"
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"

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


def main():
    ds = json.loads(DS3.read_text(encoding="utf-8"))
    raw = DS3.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    n_pos = sum(d["truth"] for d in ds)
    print(f"domain3 decision set reused: n={len(ds)} defects={n_pos} sha256={sha[:16]}")

    api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]
    jev = TrustedJev(api_key=api_key, domain="embodied-qc-labeling-okfirst",
                     log_path=str(OUT / "session.jsonl"))
    errors = 0
    t0 = time.time()
    for n, d in enumerate(ds):
        qid = d["qid"]
        q = {"type": "noul", "instructions": SPEC_OK}
        state = {"joint_readings": d["state"]["joint_readings"]}
        try:
            res = jev.decide(state, {qid: q})[qid]
            # truth: 1=NEEDS_REVIEW; question asks OK -> yes means OK -> truth_ok = 1-truth
            jev.record_outcome(qid, 1 - d["truth"])
            if n < 3 or (n + 1) % 20 == 0:
                print(f"  {n+1}/{len(ds)} {qid} said={res.decision} conf={res.stated_confidence}")
        except Exception as e:
            errors += 1
            print(f"  {n+1}/{len(ds)} {qid} ERROR {str(e)[:100]}")
        time.sleep(0.25)
    print(f"calls done in {time.time()-t0:.0f}s errors={errors}")

    sig = jev.sign_log()
    (OUT / "pubkey.txt").write_text(jev.keys.pub_hex + "\n", encoding="utf-8", newline="\n")
    v = jev.verify_log()
    stats = jev.stats()
    print("verify:", v.detail)
    print("stats:", json.dumps(stats, ensure_ascii=False))

    # paired comparison vs domain 3 (criterion 6/7/8)
    s3_path = DS3.parent / "session.jsonl"
    dec3, dec4 = {}, {}
    for line in s3_path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["kind"] == "call":
            dec3[r["qid"]] = r["decision"]
    for line in (OUT / "session.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["kind"] == "call":
            dec4[r["qid"]] = r["decision"]
    flip_neg = flip_dec = fn4 = fp4 = 0
    for d in ds:
        qid, t = d["qid"], d["truth"]
        said3 = dec3[qid] == "yes"          # domain3 yes = NEEDS_REVIEW
        said4_ok = dec4[qid] == "yes"       # domain4 yes = OK
        if t == 0:  # clean/OK item
            if not said4_ok:
                fp4 += 1
            if said3 and said4_ok:
                flip_neg += 1
        else:       # defect item
            if said4_ok:
                fn4 += 1                    # newly missed: d4 said OK on a defect
            if said3 and not said4_ok:
                flip_dec += 1               # decision flipped AND correctly detected in d4
    print(f"criterion6 false-positives(OK misjudged): {fp4}/60 "
          f"[<=45 H1 | >=55 H0]")
    print(f"criterion7 missed defects: {fn4}/60 [red flag >18]")
    print(f"paired flips: neg-fixed={flip_neg} defect-decision-flips-detected={flip_dec} (newly missed = criterion7 = {fn4})")

    (OUT / "stats.json").write_text(
        json.dumps({**stats, "decision_set": "../jev_trust_domain3_20260922/decision_set.json",
                    "decision_set_sha256": sha, "errors": errors,
                    "log": "session.jsonl", "sig": sig.name,
                    "pubkey": jev.keys.pub_hex, "verify": v.detail,
                    "criterion6_fp_on_clean": f"{fp4}/60",
                    "criterion7_missed_defects": f"{fn4}/60",
                    "criterion8_flips": {"clean_fixed": flip_neg,
                                         "defect_newly_missed": fn4,
                                         "defect_decision_flips_detected_in_d4": flip_dec}},
                   ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
