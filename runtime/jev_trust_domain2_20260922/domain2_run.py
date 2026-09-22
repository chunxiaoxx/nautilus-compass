# -*- coding: utf-8 -*-
"""jev-trust 域 2 实弹:code-patch-behavior(v5 修复判定切片)。

协议见 PROTOCOL.md。生成函数对(patch 前后),机械执行两版取真值,
PyPI jev-trust 0.1.0 跑会话,工件全落本目录。
"""
import hashlib
import json
import random
import sys
import time
from pathlib import Path

from jev_trust import TrustedJev

SEED = 20260922
N_PER = 20
OUT = Path(__file__).parent
KEY = Path.home() / ".claude" / ".cache" / "typesafe_api_key.env"

rng = random.Random(SEED)


def gen_pairs():
    items = []
    for i in range(N_PER):  # 1 off-by-one
        n = rng.randint(2, 6)
        before = f"def f(n):\n    return [x*2 for x in range(n)]\n"
        moved = rng.random() < 0.6
        after = before.replace("range(n)", "range(n+1)") if moved else before
        args = (n,)
        items.append(("offbyone", f"ob{i:03d}", before, after, args))
    for i in range(N_PER):  # 2 boundary
        t = rng.randint(5, 20)
        before = f"def f(x):\n    if x > {t}:\n        return 'big'\n    return 'small'\n"
        tightened = rng.random() < 0.6
        after = before.replace(f"x > {t}", f"x >= {t}") if tightened else before
        args = (t if rng.random() < 0.6 else t + rng.randint(1, 3),)
        items.append(("boundary", f"bd{i:03d}", before, after, args))
    for i in range(N_PER):  # 3 none-vs-zero
        before = "def f(a, b):\n    if b != 0:\n        return a / b\n    return None\n"
        switch = rng.random() < 0.6
        after = before.replace("if b != 0:", "if b:") if switch else before
        b = rng.choice([0, 2, None])
        items.append(("nonecheck", f"nc{i:03d}", before, after, (8, b)))
    for i in range(N_PER):  # 4 dict default
        d = {"a": 1, "b": 2}
        before = "def f(d, k):\n    return d[k]\n"
        got = rng.random() < 0.6
        after = before.replace("d[k]", "d.get(k, 0)") if got else before
        k = rng.choice(["a", "b", "zz"])
        items.append(("default", f"df{i:03d}", before, after, (d, k)))
    for i in range(N_PER):  # 5 type conversion
        before = "def f(x, s):\n    return str(x) + s\n"
        drop = rng.random() < 0.6
        after = before.replace("str(x) + s", "x + s") if drop else before
        if rng.random() < 0.5:
            args = (rng.randint(0, 99), "-items")
        else:
            args = (repr(rng.choice(["1", "7", "42"])), "-items")
        items.append(("typeconv", f"tc{i:03d}", before, after, args))
    for i in range(N_PER):  # 6 pure rename (behavior identical)
        before = "def f(vals):\n    total = 0\n    for v in vals:\n        total += v\n    return total\n"
        after = "def f(items):\n    s = 0\n    for it in items:\n        s += it\n    return s\n"
        vals = [rng.randint(-5, 9) for _ in range(rng.randint(3, 7))]
        items.append(("rename", f"rn{i:03d}", before, after, (vals,)))
    return items


def run_one(src, args):
    ns = {}
    exec(src, ns)
    try:
        out = ns["f"](*args)
        return ("ok", repr(out))
    except Exception as e:
        return ("exc", type(e).__name__)


def truth_of(item):
    _, _, before, after, args = item
    r1 = run_one(before, args)
    r2 = run_one(after, args)
    # both must at least run (generator guarantees); behavior change iff differ
    return 1 if r1 != r2 else 0, r1, r2


def main():
    items = gen_pairs()
    ds = []
    for it in items:
        t, r1, r2 = truth_of(it)
        ds.append({"pattern": it[0], "qid": it[1],
                   "state": {"code_before": it[2], "code_after": it[3],
                             "call_args": json.dumps(it[4], default=str)},
                   "truth": t, "before_result": r1, "after_result": r2})
    # sanity: both versions must be executable (no generator crashes leak as truth)
    for r in ds:
        for pair in ("before_result", "after_result"):
            assert r[pair][0] in ("ok", "exc"), r
    src_json = json.dumps(ds, ensure_ascii=False, sort_keys=True)
    (OUT / "decision_set.json").write_text(src_json, encoding="utf-8", newline="\n")
    sha = hashlib.sha256(src_json.encode("utf-8")).hexdigest()
    pos = sum(r["truth"] for r in ds)
    print(f"decision set: n={len(ds)} positive={pos} sha256={sha[:16]}")

    api_key = KEY.read_text(encoding="utf-8").strip().split("=", 1)[1]
    jev = TrustedJev(api_key=api_key, domain="code-patch-behavior",
                     log_path=str(OUT / "session.jsonl"))
    errors = 0
    t0 = time.time()
    for n, r in enumerate(ds):
        qid = r["qid"]
        q = {"type": "noul",
             "instructions": "Here are two versions of a Python function (before and after a patch) and the exact arguments of one call. Does the patch change this call's behavior (different return value, or different exception)? Answer strictly from Python semantics."}
        state = {"code_before": r["state"]["code_before"],
                 "code_after": r["state"]["code_after"],
                 "call": "f" + r["state"]["call_args"]}
        try:
            res = jev.decide(state, {qid: q})[qid]
            jev.record_outcome(qid, r["truth"])
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
