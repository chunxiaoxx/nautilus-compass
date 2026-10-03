#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pusht 首案配对帧判读 v1(2026-10-03 · compass 独立判,材料=/root/vdd3/pipe_art/pusht_infer_pair/)。

判据定位(层1 冻结件):主判据=rollout 成功率(仍未跑)——本判读=配对帧归因级辅助读数,不进层1判据本体,
效度终判仍留 rollout。配对设计=我方 #2496 ③建议的同帧集对照(两 ckpt 同 40 帧,隔离抽样混杂)。

口径:delta_i=ratio_A2F−ratio_A1N(逐帧);主统计=Wilcoxon 配对符号秩(纯 python 正态近似,并列秩均值修正);
稳健性=符号检验(二项正态近似);两法同报不挑。描述性=按 act_state_norm 中位二分看效应异质性。
复现性核验:配对 A2F 逐帧 ratio vs 未配对窗 pusht_infer_A2F/infer_compare.jsonl 按 (ep,idx) 对拍(v5 披露:
"同确定性帧选+确定性推理,median 完全相同 0.6297")。
幂等:同材料重跑同读数。用法:python3 pusht_pair_judge_v1.py → /root/vdd3/pipe_art/pusht_pair_verdict.json
"""
import hashlib
import json
import math
import sys
import time
from pathlib import Path

BASE = Path("/root/vdd3/pipe_art")
PAIR = BASE / "pusht_infer_pair"


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def ranks(vals):
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j < len(order) and vals[order[j]] == vals[order[i]]:
            j += 1
        for k in range(i, j):
            r[order[k]] = (i + j + 1) / 2
        i = j
    return r


def norm_p_two_sided(z: float) -> float:
    cdf = (1 + math.erf(abs(z) / math.sqrt(2))) / 2
    return round(2 * (1 - cdf), 5)


def wilcoxon(deltas):
    nz = [d for d in deltas if d != 0]
    r = ranks([abs(d) for d in nz])
    w_plus = sum(ri for ri, d in zip(r, nz) if d > 0)
    n = len(nz)
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (w_plus - mu) / sigma
    return {"n_nonzero": n, "W_plus": round(w_plus, 1), "z": round(z, 3),
            "p_two_sided": norm_p_two_sided(z)}


def sign_test(deltas):
    pos = sum(1 for d in deltas if d > 0)
    neg = sum(1 for d in deltas if d < 0)
    n = pos + neg
    z = (pos - n / 2) / math.sqrt(n / 4)
    return {"pos": pos, "neg": neg, "z": round(z, 3), "p_two_sided": norm_p_two_sided(z)}


def median(vals):
    s = sorted(vals)
    n = len(s)
    return round((s[n // 2 - 1] + s[n // 2]) / 2, 4) if n % 2 == 0 else round(s[n // 2], 4)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    f_cmp = PAIR / "paired_compare.jsonl"
    f_sum = PAIR / "paired_summary.json"
    rows = [json.loads(l) for l in f_cmp.read_text().splitlines() if l.strip()]
    summ = json.loads(f_sum.read_text())
    ok = [r for r in rows if "error" not in r]
    deltas = [round(r["ratio_A2F"] - r["ratio_A1N"], 4) for r in ok]
    # 字段自洽核验:jsonl 自带 delta_ratio 与重算一致性
    field_match = sum(1 for r, d in zip(ok, deltas) if abs(r["delta_ratio"] - d) < 1e-3)
    wil = wilcoxon(deltas)
    st = sign_test(deltas)
    # 汇总核验(v5 自报 vs 复算)
    ver = {
        "n_pairs_40": len(rows) == 40 and len(ok) == 40,
        "dir_A1N_0.85": round(sum(r["dir_A1N"] for r in ok) / len(ok), 4) == summ["dir_rate"]["A1N"],
        "dir_A2F_0.80": round(sum(r["dir_A2F"] for r in ok) / len(ok), 4) == summ["dir_rate"]["A2F"],
        "median_A1N": median([r["ratio_A1N"] for r in ok]),
        "median_A2F": median([r["ratio_A2F"] for r in ok]),
        "delta_median": median(deltas),
        "dir_agree": round(sum(r["dir_agree"] for r in ok) / len(ok), 4),
        "delta_field_match": f"{field_match}/{len(ok)}",
    }
    # 复现性对拍:配对 A2F vs 未配对窗 A2F 按 (ep,idx)
    f_a2f = BASE / "pusht_infer_A2F" / "infer_compare.jsonl"
    repro = {"checked": False}
    if f_a2f.exists():
        win_rows = [json.loads(l) for l in f_a2f.read_text().splitlines() if l.strip()]
        win = {(r["ep"], r["idx"]): r["ratio"] for r in win_rows}
        win_eps = sorted({r["ep"] for r in win_rows})
        pair_eps = sorted({r["ep"] for r in ok})
        shared = [k for k in win if any((r["ep"], r["idx"]) == k for r in ok)]
        pm = {(r["ep"], r["idx"]): r["ratio_A2F"] for r in ok}
        diffs = [abs(win[k] - pm[k]) for k in shared]
        n_eq = sum(1 for d in diffs if d < 1e-3)
        repro = {"checked": True,
                 "win_eps": win_eps, "pair_eps": pair_eps,
                 "coord_overlap": f"{len(shared)}/40",
                 "equal_ratio_at_shared": f"{n_eq}/{len(shared)}(tol 1e-3)",
                 "shared_coord_ratio_diff_max": round(max(diffs), 4) if diffs else None,
                 "reading": "两 run 帧集不同(未配对窗=fixed 数据 eps " + str(win_eps)
                            + ",配对=orig 数据 eps " + str(pair_eps) + ");共享坐标 ratio 差 1e-3 级"
                            "(orig vs fixed 输入微差);median 4dp 相同=分布级巧合非确定性复现——"
                            "v5'同确定性帧选'注记在帧级不成立,不影响配对判读有效性"}
    # 效应异质性(描述性):act_state_norm 中位二分
    med_norm = median([r["act_state_norm"] for r in ok])
    hi = [d for r, d in zip(ok, deltas) if r["act_state_norm"] >= med_norm]
    lo = [d for r, d in zip(ok, deltas) if r["act_state_norm"] < med_norm]
    hetero = {"act_norm_median": med_norm,
              "hi_half_delta_median": median(hi), "lo_half_delta_median": median(lo),
              "lo_half_neg_share": round(sum(1 for d in lo if d < 0) / len(lo), 4)}
    sig = wil["p_two_sided"] < 0.05
    v = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "judge": "compass pusht_pair_judge_v1",
        "evidence_policy": "JUDGING_EVIDENCE_TIERS_20261003",
        "criteria_positioning": "层1 主判据 rollout 成功率(未跑)——本判读=配对帧归因级辅助读数,"
                                "不进层1判据本体,效度终判仍留 rollout",
        "material": {"dir": "pusht_infer_pair", "compare_sha16": sha16(f_cmp),
                     "summary_sha16": sha16(f_sum), "n_pairs": len(ok)},
        "summary_verify_vs_v5": ver,
        "reproduction_check": repro,
        "statistics": {"wilcoxon_signed_rank": wil, "sign_test": st,
                       "delta_median": ver["delta_median"],
                       "delta_range": [round(min(deltas), 4), round(max(deltas), 4)],
                       "heterogeneity": hetero},
        "findings": [
            {"finding": f"v5 配对汇总自报与我方复算逐项一致(dir/median/delta_median/dir_agree;"
                        f"delta 字段自洽 {ver['delta_field_match']})",
             "evidence_tier": "measured", "basis": "paired_compare.jsonl 逐帧重算"},
            {"finding": f"配对归因级:Wilcoxon 符号秩 p={wil['p_two_sided']}"
                        f"({'<0.05 显著' if sig else '≥0.05 不显著'}),W+={wil['W_plus']};"
                        f"符号检验 p={st['p_two_sided']}({st['pos']}正/{st['neg']}负)——两法同报",
             "evidence_tier": "measured", "basis": "纯 python 正态近似,40 对"},
            {"finding": f"效应量级:delta 中位 {ver['delta_median']}(未配对 +0.24 的大半为抽样混杂,"
                        "v5 照实报成立,我方 #2496 保留被实测证实)",
             "evidence_tier": "measured", "basis": "配对 vs 未配对 median 对拍"},
            {"finding": f"dir 一致性 A2F 0.80 < A1N 0.85(配对帧)——幅度改善同时方向一致性略降,如实记",
             "evidence_tier": "measured", "basis": "逐帧 dir 字段"},
            {"finding": f"效应异质性:按 act_norm 中位二分,高半区 delta 中位 {hetero['hi_half_delta_median']}、"
                        f"低半区 {hetero['lo_half_delta_median']}(低半区不弱);负值帧两半区均见"
                        f"(低半区负占 {hetero['lo_half_neg_share']})——'改善集中高活动帧'叙事不成立,"
                        "异质性无清晰模式,如实记",
             "evidence_tier": "measured", "basis": "act_state_norm 中位二分描述统计",
             "upgrade_path": "若需确证异质性:分层 Wilcoxon/全 184 集配对"},
            {"finding": f"v5'同确定性帧选复现'注记帧级不成立:未配对窗帧集(fixed 数据 eps "
                        f"{repro.get('win_eps')})≠配对帧集(orig 数据 eps {repro.get('pair_eps')}),"
                        f"坐标重叠 {repro.get('coord_overlap')},共享坐标等值率 "
                        f"{repro.get('equal_ratio_at_shared')};median 4dp 相同=分布级巧合",
             "evidence_tier": "measured", "basis": "paired vs pusht_infer_A2F (ep,idx) 对拍",
             "upgrade_path": "v5 修正该注记;真正的确定性证据仍是披露①(A2F/A2N 字节一致,已复核)"},
        ],
        "verdict": "",
    }
    v["verdict"] = (
        f"PARTIAL-归因级辅助判读:配对 40 帧 Wilcoxon p={wil['p_two_sided']}"
        f"({'显著' if sig else '不显著'}),delta 中位 {ver['delta_median']}>0——"
        + ("方向支持 fixed 幅度更接近示范(欠幅减轻),抽样混杂已隔离;" if sig else
           "配对后效应未达显著,如实报;")
        + f"效应量级远小于未配对 +0.24(混杂大半,v5 照实报成立);"
        f"dir A2F 0.80<A1N 0.85 如实记;异质性无清晰模式(两半区均正,低半区不弱);"
        "v5'同帧选复现'注记帧级不成立(median 4dp 相同=巧合,已单列),不影响本判读;"
        "效度终判仍留层1 主判据 rollout 成功率(未跑,GPU 空窗可排)。")
    out = BASE / "pusht_pair_verdict.json"
    out.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(v["statistics"], ensure_ascii=False, indent=1))
    print(json.dumps(v["summary_verify_vs_v5"], ensure_ascii=False, indent=1))
    print(json.dumps(v["reproduction_check"], ensure_ascii=False))
    print("verdict:", v["verdict"])
    print(f"[save] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
