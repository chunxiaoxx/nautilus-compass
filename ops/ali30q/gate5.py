#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""质检方案五条件判定器(原文行525/527 终极口径 · 2026-10-28 v2)

达标五条件+区分度三指标(全部满足):
  ①五模型各4轮完成
  ②整体通过率=全过运行数/(5×4) < 70%
  ③opus5.5 全过轮∈[1,3] (0轮=过难TopHard剔除;4轮=过简剔除)
  ④qwen3.8max 至少一次未全过,且4轮平均通过率同时低于 opus5.5 与 gpt6-astra
  ⑤qwen passrate ∈ {25%, 50%} (4次采样;1.9%类过低不接受)
  ⑥区分度三指标(需求行963·函22917):失败集合多样性≥50%/最大签名占比≤50%/Jaccard≥1.25
    (实装=discrimination_jaccard.signature_gates;不可算=UNVERIFIED 即不达标,U 显式留痕)

v2 修复(承函 23171 终审裁定,修复 R182 审查卡 S5_GATE5_PARITY_AUDIT_20261028 四缺陷):
  P0 缺陷1: 双命名双计——同模型同 run 号去重取 mtime 最新一份;归一后不在五模型
            清单的变体拒载并留痕(报错不静默);分母固定 20,缺轮时条件出 None
            (不可判),不再产出 >100% 假读数
  P1 缺陷2: 冲突残留/坏 JSON 不再静默丢弃——拒载+留痕清单(文件名+原因)入输出
  P1 缺陷3: 批次纪律(F-009 同款)——mtime 聚簇只取最新批,跨时段读数不混算;
            轮数超规格(>4)取 mtime 最新 4 轮并留痕
  P2 缺陷4: ①缺轮不再先拦整体 return——各条件按可判数据独立评,不可判的出
            None(⚠),部分可判也出部分结论

用法: python3 gate5.py <item_dir>  → 逐条判定+出局原因
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # 从仓根调用时找同目录 s5_json/discrimination_jaccard
from s5_json import latest_batch  # F-009/F-012 mtime 聚簇

MODELS = ["qwen3.8max", "kimi-k3", "glm5.3", "opus5.5", "gpt-6-astra"]
ALIAS = {"kimi-k3-ark": "kimi-k3", "glm5.3-anthropic": "glm5.3",
         "opus5.5-qixuw": "opus5.5", "gpt6-astra": "gpt-6-astra",
         "qwen3.8max": "qwen3.8max"}

def canon(m):
    m = m.replace("_result", "")
    return ALIAS.get(m, m)

def load(item: Path):
    """装载判读数据 → (per, rejected)。

    rejected 为拒载/剔除留痕清单(缺陷2/缺陷1 的可见降级),每条 {file, reason}。"""
    rejected: list[dict] = []
    seen: dict[tuple[str, int], tuple[float, dict]] = {}  # (model, run) -> (mtime, rec)
    for f in sorted(Path(item).glob("_s5/*_run[0-9]_result.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            rejected.append({"file": f.name,
                             "reason": f"JSON解析失败({type(e).__name__},冲突残留类),拒载"})
            continue
        uv = d.get("ut_vector")
        if not isinstance(uv, dict) or not uv:
            rejected.append({"file": f.name, "reason": "无 ut_vector(非判读格式),拒载"})
            continue
        stem = Path(f).stem              # <model>_run<N>
        model, _, run = stem.rpartition("_run")
        model = canon(model)
        if model not in MODELS:
            rejected.append({"file": f.name,
                             "reason": f"归一后模型名 '{model}' 不在五模型清单,拒载(报错不静默)"})
            continue
        run_n = int(run.split("_")[0]) if run else -1
        mt = f.stat().st_mtime
        rec = {"run": run_n, "mtime": mt, "src": f.name,
               "all_pass": all(v == 1 for v in uv.values()),
               "pass_n": sum(1 for v in uv.values() if v == 1),
               "total": len(uv),
               "fail_set": frozenset(k for k, v in uv.items() if v != 1)}
        key = (model, run_n)
        if key in seen:                  # 缺陷1: 双命名重件,同 run 号只留 mtime 最新
            old_mt, old_rec = seen[key]
            win, lose = (rec, old_rec) if mt > old_mt else (old_rec, rec)
            seen[key] = (win["mtime"], win)
            rejected.append({"file": lose["src"],
                             "reason": f"同 {model} run{run_n} 双命名重件,保留 mtime 最新('{win['src']}'),剔除"})
        else:
            seen[key] = (mt, rec)
    per: dict[str, list] = {}
    for (model, _), (_, rec) in seen.items():
        per.setdefault(model, []).append(rec)
    for m in list(per):                  # 缺陷3: 批次纪律
        pairs = sorted(((r["mtime"], r) for r in per[m]), key=lambda x: x[0])
        kept = latest_batch(pairs)
        kept_src = {r["src"] for _, r in kept}
        for _, r in pairs:
            if r["src"] not in kept_src:
                rejected.append({"file": r["src"],
                                 "reason": f"{m} run{r['run']}: 非最新 mtime 批(F-009 跨时段不混算),剔除"})
        rows = [r for _, r in kept]
        if len(rows) > 4:                # 超规格只取最新 4 轮,留痕
            rows.sort(key=lambda r: -r["mtime"])
            for r in rows[4:]:
                rejected.append({"file": r["src"],
                                 "reason": f"{m} 轮数超规格({len(rows)}>4),取 mtime 最新 4 轮,剔除"})
            rows = rows[:4]
        per[m] = rows
    return per, rejected

def gate5(item: Path):
    per, rejected = load(item)
    r = {"item": item.name, "cond": {}, "reason": [], "rejected": rejected,
         "pass": False}
    counts = {m: len(per.get(m, [])) for m in MODELS}
    r["rounds"] = counts
    missing = [m for m in MODELS if counts[m] < 4]
    r["cond"]["①五模型各4轮"] = not missing
    if missing:
        r["reason"].append(f"①模型缺轮: {missing}(其余条件按可判数据独立评·缺陷4修复)")

    full_pass = {m: sum(1 for x in per.get(m, []) if x["all_pass"]) for m in MODELS}
    r["full_pass_rounds"] = full_pass
    # ②整体通过率: 全 20 轮齐才可判(缺轮时分母失配,不出误导读数)
    total_rounds = sum(counts.values())
    if not missing:
        overall = sum(full_pass.values()) / 20
        r["overall_passrate"] = round(overall, 4)
        r["cond"]["②整体通过率<70%"] = overall < 0.70
        if overall >= 0.70:
            r["reason"].append(f"②整体通过率 {overall:.0%}≥70% (过简)")
    else:
        r["cond"]["②整体通过率<70%"] = None
        r["reason"].append(f"②不可判: 实际入选轮数 {total_rounds}/20(缺轮分母失配)")
    # ③opus 全过轮∈[1,3]: opus 齐 4 轮即可判
    opus_fp = full_pass["opus5.5"]
    if counts["opus5.5"] >= 4:
        r["cond"]["③opus全过轮∈[1,3]"] = 1 <= opus_fp <= 3
        if opus_fp == 0:
            r["reason"].append("③opus 0轮全过=过难(TopHard剔除)")
        elif opus_fp == 4:
            r["reason"].append("③opus 4轮全过=过简剔除")
    else:
        r["cond"]["③opus全过轮∈[1,3]"] = None
        r["reason"].append(f"③不可判: opus 仅 {counts['opus5.5']} 轮(<4)")
    # ④⑤: qwen/opus/gpt 三模型齐即可判(kimi/glm 仅入 domestic_spread 观察列)
    trio = counts["qwen3.8max"] >= 4 and counts["opus5.5"] >= 4 and counts["gpt-6-astra"] >= 4
    if trio:
        q_avg = full_pass["qwen3.8max"] / 4     # 轮级: 全过轮数/4(整题全对率)
        g_avg = full_pass["gpt-6-astra"] / 4
        o_avg = full_pass["opus5.5"] / 4
        zero_round = any(x["pass_n"] == 0 for x in per["qwen3.8max"])   # 行40: qwen 至少一次为零
        dom = [full_pass[m] / 4 for m in ("qwen3.8max", "kimi-k3", "glm5.3") if counts[m] >= 4]
        r["domestic_spread_pp"] = round((max(dom) - min(dom)) * 100, 1) if len(dom) == 3 else None
        r["cond"]["④qwen双低+至少一轮零分"] = zero_round and q_avg < o_avg and q_avg < g_avg
        if not zero_round:
            r["reason"].append("④qwen 无全挂轮(行40:至少一次为零)")
        elif not (q_avg < o_avg and q_avg < g_avg):
            r["reason"].append(f"④qwen均 {q_avg:.3f} 未双低(opus {o_avg:.3f}/gpt {g_avg:.3f})")
        q_pr = q_avg
        r["qwen_passrate"] = round(q_pr, 4)
        r["cond"]["⑤qwen∈{25%,50%}"] = any(abs(q_pr - t) < 0.02 for t in (0.25, 0.50))
        if not r["cond"]["⑤qwen∈{25%,50%}"]:
            near = min((0.25, 0.50), key=lambda t: abs(q_pr - t))
            r["reason"].append(f"⑤qwen passrate {q_pr:.1%} 距目标{near:.0%}差 {abs(q_pr-near)*100:.1f}pp")
        r["opulus_avg"] = round(o_avg, 3); r["gpt_avg"] = round(g_avg, 3); r["qwen_avg"] = round(q_avg, 3)
    else:
        lacking = [m for m in ("qwen3.8max", "opus5.5", "gpt-6-astra") if counts[m] < 4]
        r["cond"]["④qwen双低+至少一轮零分"] = None
        r["cond"]["⑤qwen∈{25%,50%}"] = None
        r["reason"].append(f"④⑤不可判: {lacking} 缺 4 轮")
    # ⑥区分度三指标: 五模型齐 20 轮签名池才可算
    if not missing:
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
    else:
        r["cond"]["⑥区分度三指标"] = None
        r["reason"].append("⑥不可判: 五模型未齐,20 轮签名池不全")
    r["pass"] = all(v is True for v in r["cond"].values())
    return r

def _mark(v):
    return {True: "✓", False: "✗", None: "⚠不可判"}[v]

if __name__ == "__main__":
    for p in sys.argv[1:]:
        r = gate5(Path(p))
        tags = " ".join(f"{_mark(v)}{k}" for k, v in r["cond"].items())
        verdict = "✅达标" if r["pass"] else "❌不达标"
        print(f"{r['item']}: {verdict} · {tags}")
        for reason in r["reason"]:
            print(f"   └ {reason}")
        for bad in r["rejected"]:
            print(f"   ⊘ {bad['file']}: {bad['reason']}")
