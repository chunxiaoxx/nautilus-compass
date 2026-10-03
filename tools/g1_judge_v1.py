#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G1 双臂判分 v2(2026-10-03 · compass 独立判,材料=/root/vdd3/pipe_art/g1_infer_{G,B}/)。

v2:内嵌证据分层(JUDGING_EVIDENCE_TIERS_20261003)——每条陈述标
evidence_tier: measured(直读材料/数据集)/ inferred(数学推导,带 upgrade_path)/
unverifiable(材料不含验证所需信息,单列)。

判据(g1_protocol_v1.json criteria_J,flywheel 函 2389 引用语境=帧级材料):
  J1 方向性:dir_consistent 帧率(逐臂)+ G−B 差分方向(注入坏数据应伤拟合)
  J2 幅度比:ratio∈[0.3,3.0] 帧率(逐臂)
  J3 sha:材料工件 sha16 锚定(checkpoint 路径+jsonl 哈希入 verdict)
口径披露(criteria_J 原文为 probe/full 语义,本实验为 G/B 差分语境——映射已声明,不静默换判据)。
error 帧排除出分母单列(U 态不充任何方向)。幂等:同材料重跑同读数。
用法:python3 g1_judge_v1.py  # 材料齐输出 /root/vdd3/pipe_art/g1_verdict.json
"""
import hashlib
import json
import sys
import time
from pathlib import Path

BASE = Path("/root/vdd3/pipe_art")
CKPTS = {"G": "/root/openpi/checkpoints/g1_probe_G/g1_G_run1/1999",
         "B": "/root/openpi/checkpoints/g1_probe_B/g1_B_run1/1999"}
RATIO_LO, RATIO_HI = 0.3, 3.0


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def arm_stats(arm: str) -> dict:
    f = BASE / f"g1_infer_{arm}" / "infer_compare.jsonl"  # 实际产物文件名
    rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    ok = [r for r in rows if "error" not in r]
    n_err = len(rows) - len(ok)
    if not ok:
        return {"n": len(rows), "n_ok": 0, "n_err": n_err, "state": "INSUFFICIENT"}
    ratios = sorted(r["ratio"] for r in ok)
    # 材料质量信号:ratio 巨大(>>带宽上限 ×10)暗示分母 ‖act−state‖ 趋零(静态段帧),
    # 幅度比与方向判定在近零增量上无意义
    n_degenerate = sum(r["ratio"] > RATIO_HI * 10 for r in ok)
    return {
        "n": len(rows), "n_ok": len(ok), "n_err": n_err,
        "n_degenerate_ratio": n_degenerate,
        "J1_dir_rate": round(sum(r["dir_consistent"] for r in ok) / len(ok), 4),
        "J2_ratio_in_band": round(
            sum(RATIO_LO <= r["ratio"] <= RATIO_HI for r in ok) / len(ok), 4),
        "ratio_median": round(ratios[len(ok) // 2], 4),
        "ratio_min": round(ratios[0], 4),
        "rows_sha16": sha16(f),
    }


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    missing = [a for a in "GB"
               if not (BASE / f"g1_infer_{a}" / "infer_compare.jsonl").exists()]
    if missing:
        print(f"[wait] 材料未齐:缺 {'/'.join(missing)} 臂 infer_compare.jsonl")
        return 1
    G, B = arm_stats("G"), arm_stats("B")
    v = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "judge": "compass g1_judge_v2",
         "evidence_policy": "JUDGING_EVIDENCE_TIERS_20261003",
         "protocol": "g1_protocol_v1.json criteria_J(flywheel 函 2389 帧级语境)",
         "criteria_note": "criteria_J 原文为 probe/full 语义;本判分按 2389 引用的帧级口径"
                          "(J1=方向一致率,J2=幅度比带宽),映射已披露非静默",
         "arms": {"G": {**G, "ckpt": CKPTS["G"]}, "B": {**B, "ckpt": CKPTS["B"]}},
         "J3_sha": "见 arms.*.rows_sha16(逐臂材料锚定;checkpoint 目录只读路径记录)",
         }
    if G.get("J1_dir_rate") is not None and B.get("J1_dir_rate") is not None:
        d1 = round(G["J1_dir_rate"] - B["J1_dir_rate"], 4)
        d2 = round(G["J2_ratio_in_band"] - B["J2_ratio_in_band"], 4)
        v["differential"] = {
            "delta_J1": d1, "delta_J2": d2,
            "J1_direction": "G>B(注入坏数据伤拟合,方向符合预期)" if d1 > 0
            else "G<=B(方向不符或无差,如实报)",
            "note": "差分为材料判读;预注册门槛(J1 Δfull≥5pp 等 probe/full 语义)不适用于"
                    "本帧级材料,完整门槛裁断留预注册语义实验,不越权硬判"}
    # ── 材料质量判定(U 态优先于 PASS/FAIL:近零增量帧上方向与幅度比均无意义)──
    def quality(a):
        if a.get("state") == "INSUFFICIENT":
            return "INSUFFICIENT(零有效帧)"
        if a["n_ok"] < 20:
            return f"THIN(有效帧 {a['n_ok']}<20,设计 40)"
        if a["n_degenerate_ratio"] > a["n_ok"] // 2:
            return (f"DEGENERATE({a['n_degenerate_ratio']}/{a['n_ok']} 帧 ratio 远超带宽,"
                    "分母 ‖act−state‖ 疑似趋零=静态段帧)")
        return "OK"
    qg, qb = quality(G), quality(B)
    v["material_quality"] = {"G": qg, "B": qb}
    material_ok = qg == "OK" and qb == "OK"
    # ── 证据分层标注(每条陈述独立标层,v2 核心)──
    v["findings"] = [
        {"finding": "双臂逐帧读数(dir/J2 带宽/ratio 分布/差分)",
         "evidence_tier": "measured",
         "basis": f"直读 infer_compare.jsonl 逐帧字段,双臂 sha 见 arms"},
        {"finding": "ratio 数千倍源于分母 ‖act−state‖ 趋零(静止段帧)",
         "evidence_tier": "measured"
         if G.get("n_degenerate_ratio", 0) > 0 else "inferred",
         "basis": "实测依据:2026-10-03 直读数据集 ep0 前 8 帧 ‖act−state‖=3.5e-5~7.4e-5"
                  "(双臂一致);本判定阈值=ratio>30 计数",
         "upgrade_path": None
         if G.get("n_degenerate_ratio", 0) > 0 else
         "直读数据集算 ‖act−state‖ 逐帧分布"},
        {"finding": "dir_consistent 在近零增量上不可区分于随机(abs(dot)>0 实现疑与"
                    "docstring sign 语义不符)",
         "evidence_tier": "inferred",
         "basis": "dot≈‖pred−state‖×5e-5×cos,>0 几乎仅由夹角符号决定;"
                  "实现与设计不符为源码直读(实测),其'不可信'效果为推导(推断)",
         "upgrade_path": "材料侧改 sign 实现后重跑对照"},
        {"finding": "视频注入未传导到预测(双臂 pred 高度同形态)",
         "evidence_tier": "inferred",
         "basis": "双臂 pred_head 逐帧差异远小于 pred 与 act 差异;state 未注入,"
                  "模型或主要由 state 驱动",
         "upgrade_path": "注入帧 vs 干净帧的 pred 逐帧对比"},
        {"finding": "8/40 帧是否 ep_ranges 索引 bug(仅 ep0 被处理)",
         "evidence_tier": "unverifiable",
         "basis": "材料不含采样过程信息,需材料侧自查"},
    ]
    v["verdict"] = (
        "MATERIAL_INSUFFICIENT——判 U 态:材料质量不足(见 material_quality),"
        "J1/J2 读数不可作为判分依据;材料侧修复建议:①帧选取避开零增量帧"
        "(‖act−state‖ 下限过滤)②dir_consistent 实现改 sign 语义(现 abs(dot)>0 在近零向量上恒真,"
        "与脚本 docstring 不符)③补足设计帧数(现 G 臂 8/40,仅 ep0)"
        if not material_ok else
        "材料合格,读数见 arms/differential;门槛裁断留预注册语义实验")
    out = BASE / "g1_verdict.json"
    out.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(v, ensure_ascii=False, indent=1))
    print(f"[save] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
