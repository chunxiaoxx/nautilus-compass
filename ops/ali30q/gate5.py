#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""质检方案五条件判定器(原文行525/527 终极口径 · 2026-10-28)

达标五条件+区分度三指标(全部满足):
  ①五模型各4轮完成
  ②整体通过率=全过运行数/(5×4) < 70%
  ③opus5.5 全过轮∈[1,3] (0轮=过难TopHard剔除;4轮=过简剔除)
  ④qwen3.8max 至少一次未全过,且4轮平均通过率同时低于 opus5.5 与 gpt6-astra
  ⑤qwen passrate ∈ {25%, 50%} (4次采样;1.9%类过低不接受)
  ⑥区分度三指标(需求行963·函22917):失败集合多样性≥50%/最大签名占比≤50%/Jaccard≥1.25
    (实装=discrimination_jaccard.signature_gates;不可算=UNVERIFIED 即不达标,U 显式留痕)

用法: python3 gate5.py <item_dir>  → 逐条判定+出局原因
"""
import json, glob, sys
from pathlib import Path

MODELS = ["qwen3.8max", "kimi-k3", "glm5.3", "opus5.5", "gpt-6-astra"]
ALIAS = {"kimi-k3-ark": "kimi-k3", "glm5.3-anthropic": "glm5.3",
         "opus5.5-qixuw": "opus5.5", "gpt6-astra": "gpt-6-astra",
         "qwen3.8max": "qwen3.8max"}

def canon(m):
    m = m.replace("_result", "")
    return ALIAS.get(m, m)

def load(item: Path):
    per = {}
    for f in sorted(Path(item).glob("_s5/*_run[0-9]_result.json")):
        try:
            d = json.load(open(f))
        except Exception:
            continue
        uv = d.get("ut_vector")
        if not isinstance(uv, dict) or not uv:
            continue
        stem = Path(f).stem              # <model>_run<N>
        model, _, run = stem.rpartition("_run")
        model = canon(model)
        run_n = int(run.split("_")[0]) if run else -1
        all_pass = all(v == 1 for v in uv.values())
        per.setdefault(model, []).append(
            {"run": run_n, "all_pass": all_pass,
             "pass_n": sum(1 for v in uv.values() if v == 1),
             "total": len(uv), "fail_set": frozenset(k for k, v in uv.items() if v != 1)})
    return per

def gate5(item: Path):
    per = load(item)
    r = {"item": item.name, "cond": {}, "pass": False, "reason": []}
    # ①五模型各4轮
    missing = [m for m in MODELS if len(per.get(m, [])) < 4]
    r["cond"]["①四模型四轮"] = not missing
    if missing:
        r["reason"].append(f"①模型缺轮: {missing}")
        r["reason"].append("不可判(先补读数)")
        return r
    # 全过轮口径: UT 全对=1 的轮
    full_pass = {m: sum(1 for x in per[m] if x["all_pass"]) for m in MODELS}
    r["full_pass_rounds"] = full_pass
    opus_fp = full_pass["opus5.5"]
    # ②整体通过率: 全过运行数/(5×4)
    all_pass_runs = sum(full_pass.values())
    overall = all_pass_runs / 20
    r["cond"]["②整体通过率<70%"] = overall < 0.70
    if overall >= 0.70:
        r["reason"].append(f"②整体通过率 {overall:.0%}≥70% (过简)")
    # ③opus 全过轮∈[1,3]
    r["cond"]["③opus全过轮∈[1,3]"] = 1 <= opus_fp <= 3
    if opus_fp == 0:
        r["reason"].append("③opus 0轮全过=过难(TopHard剔除)")
    elif opus_fp == 4:
        r["reason"].append("③opus 4轮全过=过简剔除")
    # ④qwen 至少一次全挂为零 + 平均通过率双低于 opus 与 gpt(22924·行758:轮级口径,全对记1否则0)
    q = per["qwen3.8max"]; g = per["gpt-6-astra"]
    q_avg = full_pass["qwen3.8max"] / 4     # 轮级: 全过轮数/4(整题全对率)
    g_avg = full_pass["gpt-6-astra"] / 4
    o_avg = full_pass["opus5.5"] / 4
    some_fail = any(not x["all_pass"] for x in q)
    zero_round = any(x["pass_n"] == 0 for x in q)   # 行40: qwen 至少一次为零(全挂轮)
    # 行35: glm/kimi 与 qwen 同等水平(国内组同档)
    k_avg = full_pass["kimi-k3"] / 4
    glm_avg = full_pass["glm5.3"] / 4
    domestic_spread = max(q_avg, k_avg, glm_avg) - min(q_avg, k_avg, glm_avg)
    r["domestic_spread_pp"] = round(domestic_spread * 100, 1)
    r["cond"]["④qwen双低+至少一轮零分"] = zero_round and q_avg < o_avg and q_avg < g_avg
    if not zero_round:
        r["reason"].append("④qwen 无全挂轮(行40:至少一次为零)")
    elif not (q_avg < o_avg and q_avg < g_avg):
        r["reason"].append(f"④qwen均 {q_avg:.3f} 未双低(opus {o_avg:.3f}/gpt {g_avg:.3f})")
    # ⑤qwen passrate(轮级·行758) ∈ {25%,50%} = 全过轮数 1 或 2
    q_pr = full_pass["qwen3.8max"] / 4
    r["qwen_passrate"] = round(q_pr, 4)
    r["cond"]["⑤qwen∈{25%,50%}"] = any(abs(q_pr - t) < 0.02 for t in (0.25, 0.50))
    if not r["cond"]["⑤qwen∈{25%,50%}"]:
        near = min((0.25, 0.50), key=lambda t: abs(q_pr - t))
        r["reason"].append(f"⑤qwen passrate {q_pr:.1%} 距目标{near:.0%}差 {abs(q_pr-near)*100:.1f}pp")
    # ⑥区分度三指标(需求行963 · 函22917):多样性≥50%/最大签名占比≤50%/Jaccard≥1.25
    try:
        from discrimination_jaccard import signature_gates
        sig_runs = [{"usable": True, "fail_set": x["fail_set"], "model": m}
                    for m in MODELS for x in per[m]]
        sig = signature_gates(sig_runs)
    except Exception as e:  # 三指标不可算≠默认过,U 态显式留痕
        sig = {"status": "UNVERIFIED", "jaccard_note": f"三指标计算异常: {e}"}
    r["sig"] = sig
    r["cond"]["⑥区分度三指标"] = sig.get("status") == "PASS"
    if sig.get("status") != "PASS":
        r["reason"].append(
            f"⑥区分度三指标 {sig.get('status')}: div={sig.get('diversity')}"
            f"/share={sig.get('max_share')}/jaccard={sig.get('jaccard_ratio')}"
            f" ({sig.get('jaccard_note', '')})")
    r["pass"] = all(r["cond"].values())
    r["opulus_avg"] = round(o_avg, 3); r["gpt_avg"] = round(g_avg, 3); r["qwen_avg"] = round(q_avg, 3)
    return r

if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = gate5(Path(p))
        tags = " ".join(("✓" if v else "✗") + k.replace("cond", "cond][") + "]" for k, v in r["cond"].items())
        print(f"{r['item'] if isinstance(r['item'],str) else r['item'].name}: {'✅达标' if r['pass'] else '❌'} · {tags}")
        for reason in r["reason"]:
            print(f"   └ {reason}")
