#!/usr/bin/env python3
"""Path B 存在性搜索 — 多 SWE-bench-lite instance 跑 2-turn RSI·找任一 Y>X(2026-06-19）。

单道一次撞 ceiling(24102 1/2 持平）或 apply 失败(20049 add-method）·不足以判机制。
本批量脚本扫一组 instance·每道 prep(gold 自检门）+ rsi_swe_loop·汇总:
  任一 turn-2 > turn-1(离散）= RSI 机制存在性证 → 报喜。
  全无梯度/全持平 → probe-backed 负 → 转蒸馏(P1）。

用法:python scripts/rsi_swe_batch.py --ids sympy__sympy-24102,psf__requests-2148 --k 3
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "swe_bench")


def _load(modname, relpath):
    spec = importlib.util.spec_from_file_location(modname, os.path.join(BACKEND, relpath))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _prep(instance_id):
    """跑 prep --gold·回 selfcheck dict(verifier_sound 门）。subprocess 隔离。"""
    out = os.path.join(CACHE, "selfcheck_%s.json" % instance_id)
    log = os.path.join(CACHE, "prep_%s.log" % instance_id)
    with open(log, "w", encoding="utf-8") as lf:
        r = subprocess.run(
            [sys.executable, os.path.join(BACKEND, "scripts", "swe_prep_instance.py"),
             instance_id, "--gold", "--out", out],
            cwd=BACKEND, stdout=lf, stderr=subprocess.STDOUT, timeout=2400)
    if r.returncode != 0 or not os.path.exists(out):
        return None
    try:
        return json.load(open(out, encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", required=True, help="逗号分隔 instance_id")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--model", default="deepseek-v4-pro")
    ap.add_argument("--out", default=os.path.join(CACHE, "rsi_batch_summary.json"))
    a = ap.parse_args()

    loop = _load("rsi_swe_loop", "scripts/rsi_swe_loop.py")
    ids = [s.strip() for s in a.ids.split(",") if s.strip()]
    results = []
    for iid in ids:
        print("\n" + "=" * 60 + "\n[batch] %s — prep+gold" % iid, flush=True)
        sc = _prep(iid)
        if not sc or not sc.get("selfcheck", {}).get("verifier_sound"):
            print("[batch] %s SKIP (verifier not sound / prep fail)" % iid, flush=True)
            results.append({"instance_id": iid, "skipped": True,
                            "reason": "verifier_not_sound_or_prep_fail"})
            continue
        print("[batch] %s — run 2-turn RSI k=%d" % (iid, a.k), flush=True)
        try:
            rep = loop.run(iid, a.model, os.path.join(CACHE, "rsi_%s_batch.json" % iid), k=a.k)
        except Exception as ex:  # noqa: BLE001
            print("[batch] %s run error: %s" % (iid, str(ex)[:200]), flush=True)
            results.append({"instance_id": iid, "error": str(ex)[:300]})
            continue
        results.append({
            "instance_id": iid, "n_f2p": rep["n_f2p"],
            "turn1_passed": rep["turn1_passed"], "turn2_passed": rep["turn2_passed"],
            "turn1_rewards_k": rep.get("turn1_rewards_k"), "turn2_rewards_k": rep.get("turn2_rewards_k"),
            "rsi_proven": rep["rsi_proven"],
        })

    wins = [r for r in results if r.get("rsi_proven")]
    summary = {"n_instances": len(ids), "n_proven": len(wins),
               "any_rsi_proven": bool(wins), "results": results}
    json.dump(summary, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("\n" + "=" * 60)
    print("[batch] DONE · instances=%d · RSI proven on %d" % (len(ids), len(wins)), flush=True)
    for r in results:
        if r.get("skipped"):
            print("  %s: SKIP" % r["instance_id"])
        elif r.get("error"):
            print("  %s: ERROR" % r["instance_id"])
        else:
            print("  %s: X=%s Y=%s proven=%s (t1k=%s t2k=%s)"
                  % (r["instance_id"], r["turn1_passed"], r["turn2_passed"], r["rsi_proven"],
                     r.get("turn1_rewards_k"), r.get("turn2_rewards_k")))
    print("[batch] 写 %s" % a.out, flush=True)
    if wins:
        # ASCII only(Windows GBK 控制台 encode emoji 会崩）
        print("\n[RSI PROVEN] Y>X on: %s" % ", ".join(r["instance_id"] for r in wins), flush=True)


if __name__ == "__main__":
    main()
