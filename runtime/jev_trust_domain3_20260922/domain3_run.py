# -*- coding: utf-8 -*-
"""jev-trust 域 3 实弹:embodied-qc-labeling(flywheel 数据标注切片)。

协议见 PROTOCOL.md。生成关节角序列(埋缺陷/负例),机械 verifier 双保险,
PyPI jev-trust 0.1.0 跑会话,工件落本目录。
"""
import hashlib
import json
import math
import random
import sys
import time
from pathlib import Path

from jev_trust import TrustedJev

SEED = 20260922
N = 20  # per pattern, 6 patterns
OUT = Path(__file__).parent
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"

rng = random.Random(SEED)

SPEC = ("You are labeling embodied-robotics telemetry. The data is a sequence of 20 "
        "joint-angle readings (radians) from one joint. Label the sequence "
        "NEEDS_REVIEW if and only if ANY of these holds: "
        "(1) some pair of consecutive readings differs by more than 0.8 in absolute value (spike); "
        "(2) there are 5 or more consecutive identical readings (stuck sensor); "
        "(3) any reading is outside the range [-3.14, 3.14] (limit violation); "
        "(4) |first reading - last reading| > 1.5 AND the sequence is monotonically increasing "
        "or monotonically decreasing overall (drift). "
        "Otherwise label it OK. Answer strictly by applying these four rules to the readings.")


def base_seq():
    a = rng.uniform(-1.0, 1.0)
    ph = rng.uniform(0, math.pi)
    w = rng.uniform(0.15, 0.4)
    return [round(a + 0.4 * math.sin(ph + w * i) + rng.uniform(-0.01, 0.01), 3)
            for i in range(20)]


def gen_items():
    items = []

    def add(pat, pid, seq, planted):
        items.append((pat, pid, seq, planted))

    # spike: 15 planted (amplitude 0.85-1.6, near-threshold included), 5 not
    for i in range(N):
        s = base_seq()
        planted = i < 15
        if planted:
            pos = rng.randint(1, 18)
            amp = rng.choice([rng.uniform(0.85, 1.1), rng.uniform(1.2, 1.6)])
            s[pos] = round(s[pos - 1] + rng.choice([-1, 1]) * amp, 3)
        add("spike", f"sp{i:03d}", s, 1 if planted else 0)
    # stuck: 15 planted (repeat >=5), 5 not (repeat exactly 4 = negative)
    for i in range(N):
        s = base_seq()
        planted = i < 15
        pos = rng.randint(2, 14)
        rep = rng.randint(5, 7) if planted else 4
        for k in range(rep):
            if pos + k < 20:
                s[pos + k] = s[pos]
        add("stuck", f"st{i:03d}", s, 1 if planted else 0)
    # limit: 15 planted (3.15-3.9, near-boundary included), 5 not
    for i in range(N):
        s = base_seq()
        planted = i < 15
        if planted:
            pos = rng.randint(0, 19)
            s[pos] = round(rng.choice([rng.uniform(3.15, 3.3), rng.uniform(3.4, 3.9)])
                           * rng.choice([-1, 1]), 3)
        add("limit", f"lm{i:03d}", s, 1 if planted else 0)
    # drift: 15 planted (linear ramp ending >1.5 away, monotone), 5 not (ramp <1.5)
    for i in range(N):
        planted = i < 15
        total = rng.uniform(1.6, 2.4) if planted else rng.uniform(0.6, 1.3)
        start = rng.uniform(-0.5, 0.5)
        sign = rng.choice([-1, 1])
        s = [round(start + sign * total * k / 19.0, 3) for k in range(20)]
        add("drift", f"dr{i:03d}", s, 1 if planted else 0)
    # smooth / noise: pure negatives
    for i in range(N):
        add("smooth", f"sm{i:03d}", base_seq(), 0)
    for i in range(N):
        s = base_seq()
        s = [round(v + rng.uniform(-0.05, 0.05), 3) for v in s]
        add("noise", f"nz{i:03d}", s, 0)
    return items


def verifier(seq):
    """机械重检四规则(PROTOCOL 规范的独立实现)。"""
    for a, b in zip(seq, seq[1:]):
        if abs(b - a) > 0.8:
            return 1  # spike
    run, best = 1, 1
    for a, b in zip(seq, seq[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    if best >= 5:
        return 1  # stuck
    if any(v < -3.14 or v > 3.14 for v in seq):
        return 1  # limit
    if abs(seq[-1] - seq[0]) > 1.5 and (all(b >= a for a, b in zip(seq, seq[1:]))
                                        or all(b <= a for a, b in zip(seq, seq[1:]))):
        return 1  # drift
    return 0


def main():
    items = gen_items()
    mismatch = [(p, q, v, verifier(s)) for p, q, s, v in items if verifier(s) != v]
    if mismatch:
        print("VERIFIER MISMATCH — generator bug, abort:", mismatch[:3])
        sys.exit(1)
    ds = [{"pattern": p, "qid": q, "state": {"joint_readings": s}, "truth": v}
          for p, q, s, v in items]
    src_json = json.dumps(ds, ensure_ascii=False, sort_keys=True)
    (OUT / "decision_set.json").write_text(src_json, encoding="utf-8", newline="\n")
    sha = hashlib.sha256(src_json.encode("utf-8")).hexdigest()
    pos = sum(d["truth"] for d in ds)
    print(f"decision set: n={len(ds)} positive={pos} sha256={sha[:16]} verifier=clean")

    api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]
    jev = TrustedJev(api_key=api_key, domain="embodied-qc-labeling",
                     log_path=str(OUT / "session.jsonl"))
    errors = 0
    t0 = time.time()
    for n, d in enumerate(ds):
        qid = d["qid"]
        q = {"type": "noul", "instructions": SPEC}
        state = {"joint_readings": d["state"]["joint_readings"]}
        try:
            res = jev.decide(state, {qid: q})[qid]
            jev.record_outcome(qid, d["truth"])
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
    (OUT / "stats.json").write_text(
        json.dumps({**stats, "decision_set_sha256": sha, "errors": errors,
                    "log": "session.jsonl", "sig": sig.name,
                    "pubkey": jev.keys.pub_hex, "verify": v.detail},
                   ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")


if __name__ == "__main__":
    sys.exit(main())
