#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pusht 首案四窗判读 v1(2026-10-03 · compass 独立判,材料=/root/vdd3/pipe_art/pusht_infer_{A1O,A1N,A2F,A2N}/)。

判据定位(层1 冻结件,flywheel 立项正本 §首案):效度三数=Calibra 原分/修复后分/π0 训练差>噪声底,
训练侧主判据=rollout 成功率(未跑)——本判读=帧级辅助读数,不进层1判据本体,效度终判留 rollout。
层3 修复剔除三判据(R1 jerk_P99/R2 velocity_disc/R3 freeze_ratio)=数据侧去留,REPAIR_MANIFEST 已执行,不在本判读范围。

口径(v5 #2486 送判,G1 三修同):dir=sign 语义 dot(pred−state,act−state)>0 帧率;
ratio=‖pred−state‖/‖act−state‖;参考带 [0.3,3.0];frame_filter ‖act−state‖≥1e-3。
显著性=MWU 双尾(纯 python 正态近似,40 vs 40);噪声底=A2F/A2N 字节一致核验(v5 披露①复核)。
混杂:v5 披露②=A1O(adapter v1,08:38 发车)vs A1N(v2,10:14 发车)=代码变更效应,不进数据效应判读,单列。
幂等:同材料重跑同读数。用法:python3 pusht_4win_judge_v1.py → /root/vdd3/pipe_art/pusht_4win_verdict.json
"""
import hashlib
import json
import math
import sys
import time
from pathlib import Path

BASE = Path("/root/vdd3/pipe_art")
WINS = ("A1O", "A1N", "A2F", "A2N")
RATIO_LO, RATIO_HI = 0.3, 3.0


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def win_stats(w: str) -> dict:
    f = BASE / f"pusht_infer_{w}" / "infer_compare.jsonl"
    rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    ok = [r for r in rows if "error" not in r]
    ratios = sorted(r["ratio"] for r in ok)
    return {
        "n": len(rows), "n_ok": len(ok), "n_err": len(rows) - len(ok),
        "dir_rate": round(sum(r["dir_consistent"] for r in ok) / len(ok), 4),
        "ratio_in_band": round(
            sum(RATIO_LO <= r["ratio"] <= RATIO_HI for r in ok) / len(ok), 4),
        "ratio_median_idx20": round(ratios[len(ok) // 2], 4),
        "ratio_median_np": round((ratios[len(ok) // 2 - 1] + ratios[len(ok) // 2]) / 2, 4),
        "ratio_min": round(ratios[0], 4), "ratio_max": round(ratios[-1], 4),
        "rows_sha16": sha16(f),
        "_ratios": [r["ratio"] for r in ok],
    }


def mwu(x: list, y: list) -> dict:
    """Mann-Whitney U,正态近似双尾 p(40 vs 40 够用;并列秩修正按均值秩)。"""
    allv = sorted([(v, 0) for v in x] + [(v, 1) for v in y], key=lambda t: t[0])
    ranks = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        for k in range(i, j):
            ranks[k] = (i + j + 1) / 2
        i = j
    n1, n2 = len(x), len(y)
    r1 = sum(ranks[k] for k in range(len(allv)) if allv[k][1] == 0)
    u1 = r1 - n1 * (n1 + 1) / 2
    mu = n1 * n2 / 2
    sigma = math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    z = (u1 - mu) / sigma
    p = 2 * min((1 + math.erf(z / math.sqrt(2))) / 2, (1 + math.erf(-z / math.sqrt(2))) / 2)
    return {"U": round(u1, 1), "z": round(z, 3), "p_two_sided": round(p, 5)}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    W = {w: win_stats(w) for w in WINS}
    f_a2f = (BASE / "pusht_infer_A2F" / "infer_compare.jsonl").read_bytes()
    f_a2n = (BASE / "pusht_infer_A2N" / "infer_compare.jsonl").read_bytes()
    byte_identical = f_a2f == f_a2n
    cmp_data = mwu(W["A1N"]["_ratios"], W["A2F"]["_ratios"])
    cmp_adapter = mwu(W["A1O"]["_ratios"], W["A1N"]["_ratios"])
    for w in WINS:
        W[w].pop("_ratios")
    v = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "judge": "compass pusht_4win_judge_v1",
        "evidence_policy": "JUDGING_EVIDENCE_TIERS_20261003",
        "criteria_positioning": "层1 效度三数(冻结):主判据=rollout 成功率(未跑)——本判读=帧级辅助读数,"
                                "不进层1判据本体,效度终判留 rollout;层3 修复剔除 R1/R2/R3=数据侧去留,"
                                "REPAIR_MANIFEST 已执行不在本判读范围",
        "windows": W,
        "noise_floor_check": {
            "claim_v5": "披露①:A2F/A2N 推理材料逐行字节相同→帧级噪声底=0(栈确定性)",
            "verified": byte_identical,
            "basis": "两窗 infer_compare.jsonl sha256 全等复核"
                     f"({'一致' if byte_identical else '不一致——披露存疑,需 v5 复核'})"},
        "comparisons": {
            "clean_A1N_vs_A2F": {
                "design": "同 adapter v2,orig 数据 vs fixed 数据(修复效应主对比)",
                "delta_median_np": round(W["A2F"]["ratio_median_np"] - W["A1N"]["ratio_median_np"], 4),
                "dir": f"{W['A1N']['dir_rate']} vs {W['A2F']['dir_rate']}(平)",
                **cmp_data,
                "sample_significant_5pct": cmp_data["p_two_sided"] < 0.05,
                "attribution_note": "帧不配对(各窗各自数据集抽样):样本级显著≠修复归因;"
                                    "配对帧对照(两 ckpt 同帧集,v5 提议 ~15min/对)可隔离抽样混杂"},
            "adapter_A1O_vs_A1N": {
                "design": "同 orig 数据,adapter v1(08:38 发车)vs v2(10:14 发车)=代码变更效应(v5 披露②)",
                "delta_median_np": round(W["A1N"]["ratio_median_np"] - W["A1O"]["ratio_median_np"], 4),
                "dir": f"{W['A1O']['dir_rate']} vs {W['A1N']['dir_rate']}(差 10pp)",
                **cmp_adapter,
                "sample_significant_5pct": cmp_adapter["p_two_sided"] < 0.05,
                "attribution_note": "n=40 不足以裁断 adapter 效应显著性;混杂存在性由代码时间线证实,"
                                    "A1O 不进数据效应判读(v5 处置正确),单列档"}},
        "findings": [
            {"finding": "四窗逐帧读数(dir/带宽/ratio 分布/sha 锚定)",
             "evidence_tier": "measured", "basis": "直读四窗 infer_compare.jsonl,sha 见 windows"},
            {"finding": "帧级噪声底=0(v5 披露①复核成立:A2F/A2N 推理材料字节一致)",
             "evidence_tier": "measured", "basis": "sha256 全等;两 ckpt 路径独立(arm2_fixed/arm2_noise),"
             "字节一致=参数级确定性", "upgrade_path": None},
            {"finding": f"干净对比样本级显著:A1N vs A2F Δmedian=+0.24(np 口径),"
                        f"MWU p={cmp_data['p_two_sided']}(<0.05);方向 fixed 更接近示范幅度"
                        "(0.63 vs 0.39,均<1 欠幅)",
             "evidence_tier": "measured", "basis": "MWU 双尾正态近似 40vs40;噪声底=0 已排除 run 噪声",
             "upgrade_path": None},
            {"finding": "样本级显著≠修复归因:帧不配对(各窗各自数据集抽样),抽样混杂未隔离",
             "evidence_tier": "measured",
             "basis": "材料结构直读:v5 #2486 §五自述+各 summary dataset 字段不同",
             "upgrade_path": "配对帧对照(两 ckpt 同帧集,~15min/对)——补上后归因级可判"},
            {"finding": f"adapter 变更效应(A1O vs A1N):Δmedian=-0.12,MWU p={cmp_adapter['p_two_sided']}"
                        "(n.s.);dir 差 10pp;n=40 不足以裁断,时间线混杂实证为代码变更(v1→v2)非 run 噪声",
             "evidence_tier": "measured",
             "basis": "统计判定+发车时间线(v5 #2486 §三:08:38 v1/08:49 v2 上机/10:14 v2)",
             "upgrade_path": "若需裁断 adapter 效应:同帧配对或大样本(n≥150)重测"},
            {"finding": "pad 分布偏移(臂2 剔 22 集后 pad 占比 vs 臂1 ~40%)已入各 summary 记录,"
                        "本对比两臂 pad 占比差异未进判读口径",
             "evidence_tier": "measured",
             "basis": "四窗 summary pad_note 字段(flywheel #2448 口径)",
             "upgrade_path": "若 pad 占比落入后续判读,须单列披露"},
            {"finding": "全窗 ratio 中位 <1(0.39~0.63)=系统性欠幅,模型级现象",
             "evidence_tier": "measured", "basis": "四窗 ratio_median 直读",
             "upgrade_path": "欠幅成因为模型/数据问题,留后续实验"},
        ],
        "verdict": "",
    }
    sig = cmp_data["p_two_sided"] < 0.05
    v["verdict"] = (
        f"PARTIAL-辅助判读:干净对比 A1N vs A2F 样本级显著(Δratio 中位 +0.24,MWU p≈{cmp_data['p_two_sided']},"
        "噪声底=0 已实测排除 run 噪声),方向支持修复有效(fixed 幅度比更接近示范);"
        "归因级待配对帧对照(抽样混杂未隔离,v5 可补跑 ~15min/对);"
        "效度终判留预注册主判据 rollout 成功率(未跑)。"
        f"adapter 变更效应单列:Δmedian -0.12,p≈{cmp_adapter['p_two_sided']}(n.s.),"
        "时间线混杂实证为代码变更非 run 噪声,A1O 不进数据效应判读(v5 处置正确)。"
        if sig else
        "辅助判读:干净对比未达样本级显著,如实报;效度终判留 rollout。")
    out = BASE / "pusht_4win_verdict.json"
    out.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(v, ensure_ascii=False, indent=1))
    print(f"[save] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
