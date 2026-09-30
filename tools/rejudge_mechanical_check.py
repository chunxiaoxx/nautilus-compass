#!/usr/bin/env python3
"""rejudge 500 题抽样复算 · 机械层+抽样任务生成+汇总。

预注册判据正本:docs/metering/REJUDGE_RECOMPUTE_PREREG_20260930.md
(J1 冲突率≤5%/J2 盲判一致率≥90%/J3 双绿升级/J4 seed=20260930/J5 盲/J6 原样读数)

用法:
  python tools/rejudge_mechanical_check.py            # 机械层 + 生成抽样任务
  python tools/rejudge_mechanical_check.py summary    # 汇总(需 sample_verdicts.json)
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "vtf" / "_e2e_diag" / "arm_a_rows_rejudged.json"
OUT = ROOT / "runtime" / "rejudge_check"
SEED = 20260930
SAMPLE_N = 50


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def mech_verdict(truth, answer: str):
    """M1 数值 / M3 不判(文本不机械判)。

    修正 #1(判据档 append):原 M2 短文本子串规则被首跑证伪——49 冲突全 M2
    零 M1,实例全为语义等价改写('five'vs'5'/人称/括号),judge 全判对、
    探针误伤。M2 已并入 M3 抽样池;J1 只用 M1(数值,假阳方向=放过,无误伤)。
    """
    if isinstance(truth, int) or re.fullmatch(r"\d+", str(truth).strip()):
        t = int(truth)
        nums = {int(float(x)) for x in re.findall(r"\d+(?:\.\d+)?", answer or "")}
        return ("M1", t in nums)
    return ("M3", None)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = json.loads(SRC.read_text(encoding="utf-8"))
    mech = {"M1": [], "M2": [], "M3": []}
    report = []
    conflicts = []
    for qid, r in rows.items():
        rule, mc = mech_verdict(r.get("truth"), r.get("model_answer") or "")
        judge_ok = (r.get("judge_raw") == "CORRECT")
        rec = {"qid": qid, "rule": rule, "mech": mc, "judge_ok": judge_ok,
               "question_type": r.get("question_type")}
        report.append(rec)
        mech[rule].append(qid)
        if mc is False and judge_ok:  # 高置信模型答错 但 judge 判对 → judge 疑似错
            conflicts.append(qid)
    (OUT / "mech_report.json").write_text(
        json.dumps({"per_q": report,
                    "counts": {k: len(v) for k, v in mech.items()},
                    "conflicts_judge_CORRECT_vs_mech_incorrect": conflicts},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    # 抽样任务(M3 题,seed 固定;字段级排除 judge_raw/is_correct → J5 盲)
    m3_rows = [(qid, r) for qid, r in rows.items()
               if mech_verdict(r.get("truth"), r.get("model_answer") or "")[0] == "M3"]
    sample = random.Random(SEED).sample(m3_rows, min(SAMPLE_N, len(m3_rows)))
    tasks = [{"qid": qid, "question": r["question"], "truth": r["truth"],
              "model_answer": r["model_answer"]} for qid, r in sample]
    (OUT / "sample_tasks_50.json").write_text(
        json.dumps(tasks, ensure_ascii=False, indent=1), encoding="utf-8")

    import hashlib
    digest = hashlib.sha256(
        json.dumps([t["qid"] for t in tasks]).encode()).hexdigest()[:16]
    print(f"[mech] M1={len(mech['M1'])} M2={len(mech['M2'])} M3={len(mech['M3'])}")
    print(f"[J1] mech=incorrect & judge=CORRECT 冲突 = {len(conflicts)} "
          f"/ 机械可判 {len(mech['M1']) + len(mech['M2'])} 题 "
          f"({len(conflicts) / max(len(mech['M1']) + len(mech['M2']), 1) * 100:.1f}%)")
    print(f"[sample] seed={SEED} n={len(tasks)} 名单sha16={digest} → sample_tasks_50.json")


def summary():
    mr = json.loads((OUT / "mech_report.json").read_text(encoding="utf-8"))
    verdicts = {v["qid"]: v for v in
                json.loads((OUT / "sample_verdicts.json").read_text(encoding="utf-8"))}
    rows = json.loads(SRC.read_text(encoding="utf-8"))
    n = agree = 0
    disagreements = []
    for qid, v in verdicts.items():
        judge_ok = rows[qid]["judge_raw"] == "CORRECT"
        indep_ok = v.get("verdict") == "CORRECT"
        n += 1
        if judge_ok == indep_ok:
            agree += 1
        else:
            disagreements.append({"qid": qid, "judge": judge_ok, "indep": indep_ok,
                                  "indep_reason": v.get("reason", "")[:150]})
    conflicts = mr["conflicts_judge_CORRECT_vs_mech_incorrect"]
    mech_n = mr["counts"]["M1"] + mr["counts"]["M2"]
    print(f"[J1] 冲突率 = {len(conflicts)}/{mech_n} "
          f"({len(conflicts) / max(mech_n, 1) * 100:.1f}%) → "
          f"{'PASS' if len(conflicts) / max(mech_n, 1) <= 0.05 else 'FAIL'}")
    rate = agree / max(n, 1)
    print(f"[J2] 抽样一致率 = {agree}/{n} ({rate * 100:.1f}%) → "
          f"{'PASS' if rate >= 0.90 else 'FAIL'}")
    print(f"[J3] {'双绿→500 升 labelled' if rate >= 0.90 and len(conflicts) / max(mech_n, 1) <= 0.05 else '不升级;分歧样本入勘误库'}")
    (OUT / "final_summary.json").write_text(
        json.dumps({"conflicts": conflicts, "mech_n": mech_n,
                    "agree": agree, "n": n, "disagreements": disagreements},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    for dd in disagreements:
        print(f"  分歧 {dd['qid']}: judge={dd['judge']} indep={dd['indep']} | {dd['indep_reason'][:100]}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        summary()
    else:
        main()
