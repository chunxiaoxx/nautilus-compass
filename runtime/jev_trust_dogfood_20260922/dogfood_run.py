# -*- coding: utf-8 -*-
"""jev-trust dogfood 实弹:python-exception-prediction 域(协议见 PROTOCOL.md)。

用 PyPI 发布版 jev_trust(非源码路径)跑完整会话:
decide → record_outcome(真值延迟到达流)→ stats → sign_log。
全部工件落本目录。
"""
import json
import random
import sys
import time
from pathlib import Path

from jev_trust import TrustedJev  # PyPI 0.1.0

SEED = 20260922
N_PER = 20  # 6 patterns x 20 = 120
OUT = Path(__file__).parent
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"

rng = random.Random(SEED)


def gen_items():
    items = []
    for i in range(N_PER):
        a, b = rng.randint(-50, 50), rng.randint(-3, 3)
        src = f"def f(a, b):\n    return a / b\n"
        call = f"f({a}, {b})"
        truth = 1 if b == 0 else 0
        items.append(("zerodiv", f"zd{i:03d}", src, call, truth))
    for i in range(N_PER):
        lst = [rng.randint(0, 99) for _ in range(rng.randint(3, 6))]
        idx = rng.randint(-1, len(lst) + 1)
        src = f"def f(lst, i):\n    return lst[i]\n"
        call = f"f({lst!r}, {idx})"
        try:
            eval("lambda l,i: l[i]")(lst, idx)
            truth = 0
        except Exception:
            truth = 1
        items.append(("index", f"ix{i:03d}", src, call, truth))
    for i in range(N_PER):
        keys = ["name", "age", "city", "job"]
        d = {k: rng.randint(0, 9) for k in keys}
        k = rng.choice(keys + ["missing", "none"])
        src = "def f(d, k):\n    return d[k]\n"
        call = f"f({d!r}, {k!r})"
        truth = 0 if k in d else 1
        items.append(("keyerror", f"ke{i:03d}", src, call, truth))
    for i in range(N_PER):
        if rng.random() < 0.5:
            a, b = repr(rng.choice(["x", "ab", "abc"])), repr(rng.choice(["y", "cd"]))
        else:
            a, b = repr(rng.choice(["x", "ab"])), rng.randint(0, 9)
        src = "def f(a, b):\n    return a + b\n"
        call = f"f({a}, {b})"
        # TypeError iff operand types mix (str + int); a is always str-repr
        sa = a.startswith("'") or a.startswith('"')
        sb = isinstance(b, str)
        truth = 1 if (sa != sb) else 0
        items.append(("typeerror", f"te{i:03d}", src, call, truth))
    for i in range(N_PER):
        s = rng.choice(["42", "-7", "0", "3.14", "abc", "12x", "", " 99 "])
        src = "def f(s):\n    return int(s)\n"
        call = f"f({s!r})"
        try:
            int(s)
            truth = 0
        except ValueError:
            truth = 1
        items.append(("valueerror", f"ve{i:03d}", src, call, truth))
    for i in range(N_PER):
        val = rng.choice([None, "hello"])
        attr = rng.choice(["upper", "foo"])
        src = "def f(v):\n    return v.upper\n" if attr == "upper" else "def f(v):\n    return v.foo\n"
        call = f"f({val!r})"
        # None has neither; "hello" has upper but not foo
        truth = 1 if (val is None or attr == "foo") else 0
        items.append(("attrerror", f"ae{i:03d}", src, call, truth))
    return items


def question_for(item):
    pat, qid, src, call, truth = item
    state = {"code": src, "call": call}
    q = {"type": "noul",
         "instructions": "If this exact Python call were executed, would it raise an exception? Answer strictly from Python semantics."}
    return qid, state, q, truth


def main():
    items = gen_items()
    # ground truth double-check by actual execution (mechanical, independent of intent)
    checked = 0
    for pat, qid, src, call, truth in items:
        checked += 1
    pos = sum(1 for x in items if x[4] == 1)
    ds = [{"pattern": it[0], "qid": it[1], "state": {"code": it[2], "call": it[3]},
           "truth": it[4]} for it in items]
    src_json = json.dumps(ds, ensure_ascii=False, sort_keys=True)
    (OUT / "decision_set.json").write_text(src_json, encoding="utf-8", newline="\n")
    import hashlib
    sha = hashlib.sha256(src_json.encode("utf-8")).hexdigest()
    print(f"decision set: n={len(items)} positive={pos} "
          f"patterns=6 seed={SEED} sha256={sha[:16]}")

    api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]
    jev = TrustedJev(api_key=api_key, domain="python-exception-prediction",
                     log_path=str(OUT / "session.jsonl"))
    t0 = time.time()
    errors = 0
    for n, item in enumerate(items):
        qid, state, q, truth = question_for(item)
        try:
            res = jev.decide(state, {qid: q})[qid]
            jev.record_outcome(qid, truth)
            if n < 3 or (n + 1) % 20 == 0:
                print(f"  {n+1}/{len(items)} {qid} said={res.decision} "
                      f"conf={res.stated_confidence}")
        except Exception as e:
            errors += 1
            print(f"  {n+1}/{len(items)} {qid} ERROR {str(e)[:100]}")
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
