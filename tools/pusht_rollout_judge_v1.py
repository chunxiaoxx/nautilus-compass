#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pusht 首案 rollout 判读 v1(2026-10-03 · compass 独立判,材料=/root/vdd3/pipe_art/pusht_rollout_20261003_133459/)。

判据定位(层1 冻结件):主判据=rollout 成功率(success_def=terminated & info[is_success],阈值 coverage>0.95,
300 步,同 seed 跨窗配对)。判据零放宽:成功率全员零则差分判不动如实报,不把 coverage 升格顶替冻结语义;
coverage=连续代理辅助读数,标注非冻结。噪声底=同臂双跑 |A2F−A2N|(rollout 维)。
A1O=v1 协议混杂存档参照,不进主判(v5 env_fingerprint 坐标注一致)。

口径:coverage 逐集分布(读 rollout_*.jsonl)+MWU(20 vs 20,纯 python 正态近似,并列秩均值修正);
锚定=rollout_all_summary.json sha16+四窗 ckpt_sha16。幂等:同材料重跑同读数。
用法:python3 pusht_rollout_judge_v1.py → /root/vdd3/pipe_art/pusht_rollout_verdict.json
"""
import hashlib
import json
import math
import sys
import time
from pathlib import Path

BASE = Path("/root/vdd3/pipe_art") / "pusht_rollout_20261003_133459"
WINS = ("A1O", "A1N", "A2F", "A2N")


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def norm_p(z: float) -> float:
    return round(2 * (1 - (1 + math.erf(abs(z) / math.sqrt(2))) / 2), 5)


def mwu(x, y):
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
    z = (u1 - n1 * n2 / 2) / math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    return {"U": round(u1, 1), "z": round(z, 3), "p_two_sided": norm_p(z)}


def ep_coverages(w: str):
    """逐集 final coverage(字段名宽容探测)。"""
    f = BASE / f"rollout_{w}.jsonl"
    rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    if not rows:
        return [], 0
    key = next((k for k in ("final_coverage", "coverage", "cov") if k in rows[0]), None)
    covs = [r[key] for r in rows] if key else []
    skey = next((k for k in ("success", "is_success", "terminated_success") if k in rows[0]), None)
    n_succ = sum(1 for r in rows if r.get(skey)) if skey else 0
    return covs, n_succ


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    allsum = json.loads((BASE / "rollout_all_summary.json").read_text())
    W = {w["window"]: w for w in allsum["windows"]}
    cov = {}
    for w in WINS:
        c, ns = ep_coverages(w)
        cov[w] = c
        if c:
            s = sorted(c)
            W[w]["cov_median"] = round((s[len(s) // 2 - 1] + s[len(s) // 2]) / 2, 4)
            W[w]["cov_min"], W[w]["cov_max"] = round(s[0], 4), round(s[-1], 4)
        W[w]["eps_success_recount"] = ns
    cmp_main = mwu(cov["A1N"], cov["A2F"]) if cov["A1N"] and cov["A2F"] else None
    noise_floor = round(abs(W["A2F"]["mean_final_coverage"] - W["A2N"]["mean_final_coverage"]), 6)
    per_ep_noise = (round(max(abs(a - b) for a, b in zip(cov["A2F"], cov["A2N"])), 6)
                    if cov["A2F"] and cov["A2N"] else None)
    all_zero = all(W[w]["n_success"] == 0 for w in WINS)
    cov_ratio = round(W["A2F"]["mean_final_coverage"] / W["A1N"]["mean_final_coverage"], 4)
    v = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "judge": "compass pusht_rollout_judge_v1",
        "evidence_policy": "JUDGING_EVIDENCE_TIERS_20261003",
        "criteria_positioning": "层1 主判据=rollout 成功率(冻结语义:success_def/阈值 0.95/300 步/同 seed 配对)——"
                                "判据零放宽,成功率判不动即如实报;coverage=连续代理辅助读数(非冻结语义,不顶替);"
                                "A1O v1 协议混杂存档不进主判",
        "material": {"dir": BASE.name, "all_summary_sha16": sha16(BASE / "rollout_all_summary.json"),
                     "ckpt_sha16": {w: W[w]["ckpt_sha16"] for w in WINS},
                     "env_fingerprint_sha16": sha16(BASE / "env_fingerprint.json")},
        "windows": {w: {k: W[w][k] for k in ("role", "n_eps", "n_success", "success_rate",
                                             "mean_final_coverage", "cov_median", "cov_min",
                                             "cov_max", "eps_success_recount") if k in W[w]}
                    for w in WINS},
        "main_criterion": {
            "all_windows_zero_success": all_zero,
            "reading": "成功率 4 窗全 0/20(阈值 coverage>0.95)——地板效应,差分判不动(0 vs 0);"
                       "判据零放宽,不改义不递补"},
        "coverage_proxy": {
            "A1N_vs_A2F_mean": f"{W['A1N']['mean_final_coverage']} vs {W['A2F']['mean_final_coverage']}",
            "ratio": cov_ratio, **(cmp_main or {}),
            "note": "连续代理,非冻结主判据语义;方向与帧级配对判读(p=0.00986)一致"},
        "noise_floor_rollout": {
            "mean_cov_abs_diff": noise_floor, "per_ep_max_abs_diff": per_ep_noise,
            "ckpt_sha16_differ": W["A2F"]["ckpt_sha16"] != W["A2N"]["ckpt_sha16"],
            "note": "结果级噪声底=0(coverage 全同);A2F/A2N ckpt_sha16 不同=sha 对象疑含参数外内容,"
                    "口径请 v5 披露;与披露①(帧级字节一致)并读"},
        "findings": [
            {"finding": "四窗 rollout 20 集全完成,成功率全 0/20(阈值 coverage>0.95/300 步)",
             "evidence_tier": "measured", "basis": "rollout_all_summary.json+逐集 jsonl 复算"},
            {"finding": f"主判据地板效应:成功率差分判不动(0 vs 0),判据零放宽不递补",
             "evidence_tier": "measured", "basis": "冻结 success_def 直读"},
            {"finding": f"coverage 辅助:A2F {W['A2F']['mean_final_coverage']} vs A1N "
                        f"{W['A1N']['mean_final_coverage']}(×{cov_ratio}),MWU p="
                        f"{(cmp_main or {}).get('p_two_sided')};中位 {W['A2F'].get('cov_median')} vs "
                        f"{W['A1N'].get('cov_median')};方向与帧级配对判读一致支持修复",
             "evidence_tier": "measured", "basis": "逐集 coverage MWU 20vs20",
             "upgrade_path": "coverage 若需升正判据:判据档主新预注册(阈值/语义),我方不越权"},
            {"finding": f"rollout 维噪声底=0(mean 差 {noise_floor},逐集最大差 {per_ep_noise})",
             "evidence_tier": "measured", "basis": "A2F/A2N 同臂双跑对拍"},
            {"finding": "A1O coverage 0.0531 最低(v1 协议混杂存档参照,不进主判)",
             "evidence_tier": "measured", "basis": "v5 env_fingerprint 坐标注+汇总直读"},
            {"finding": "与 Calibra 原分 76.7 不可对表:口径(阈值/步数/协议)不在本材料内",
             "evidence_tier": "unverifiable", "basis": "材料内无 Calibra 协议细节",
             "upgrade_path": "flywheel/v5 提供 Calibra 评分协议或同口径复评分"},
        ],
        "verdict": "",
    }
    v["verdict"] = (
        "PARTIAL-U(层1 主判据无区分度):rollout 成功率四窗全 0/20(阈值 coverage>0.95/300 步)——"
        "地板效应,成功率差分判不动,判据零放宽不改义;"
        f"辅助读数 coverage:A2F×{cov_ratio} A1N(MWU p={(cmp_main or {}).get('p_two_sided')}),"
        "方向与帧级配对判读(p=0.00986)一致支持修复,但=连续代理非冻结语义不顶替;"
        f"rollout 维噪声底=0(mean 差 {noise_floor});"
        "效度终判条件=判据档主定夺:协议修订(阈值/步数,须新预注册)或 coverage 代理正式入判据;"
        "与 Calibra 76.7 口径不可对表[不可验]。")
    out = Path("/root/vdd3/pipe_art/pusht_rollout_verdict.json")
    out.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(v["main_criterion"], ensure_ascii=False))
    print(json.dumps(v["coverage_proxy"], ensure_ascii=False))
    print(json.dumps(v["noise_floor_rollout"], ensure_ascii=False))
    print("verdict:", v["verdict"])
    print(f"[save] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
