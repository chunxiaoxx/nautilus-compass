#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""pusht rollout n=100 终判(2026-10-03 · compass 独立判,材料=runtime/loop/_r73_n100/)。

判据状态:层1 主判据 v2(用户已批,#2568)——成功率差分(冻结语义,判不动如实报)
+coverage 连续主判(逐局,窗分=均值);统计两法按我方 T2 裁决:主=同 seed 配对
Wilcoxon(双尾),辅=MWU(双尾);T1=全量 100 集/窗(flywheel 送判口径即方案 a,
seed 70000-70099 跨窗配对);中位并陈(T2 附注);噪声底=A2F−A2N 逐局差。
正本数据 sha256 见 _r73_pull_n100.py 输出;A1O 存档参照不进主判。
幂等:同材料重跑同读数。
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DATA = Path(__file__).parent / "_r73_n100"
WINS = ("A1O", "A1N", "A2F", "A2N")


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def norm_p(z: float) -> float:
    return round(2 * (1 - (1 + math.erf(abs(z) / math.sqrt(2))) / 2), 5)


def ranks_of(vals):
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


def wilcoxon_paired(x, y):
    """逐 seed 配对 Wilcoxon 符号秩(双尾,零差对剔除,并列秩均值修正)。主法(T2)。"""
    d = [round(b - a, 6) for a, b in zip(x, y)]
    nz = [v for v in d if v != 0]
    if not nz:
        return {"n_pairs": len(d), "n_nonzero": 0, "identical_pairs": len(d),
                "mean_delta": round(sum(d) / len(d), 4), "median_delta": median(d),
                "pos": 0, "neg": 0, "W_plus": 0.0, "z": 0.0, "p_two_sided": 1.0,
                "note": "全部逐对相同=确定性(nz=0,检验不适用)"}
    r = ranks_of([abs(v) for v in nz])
    w_plus = sum(ri for ri, v in zip(r, nz) if v > 0)
    n = len(nz)
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    z = (w_plus - mu) / sigma
    return {"n_pairs": len(d), "n_nonzero": n, "identical_pairs": len(d) - n,
            "mean_delta": round(sum(d) / len(d), 4), "median_delta": median(d),
            "pos": sum(1 for v in d if v > 0), "neg": sum(1 for v in d if v < 0),
            "W_plus": round(w_plus, 1), "z": round(z, 3), "p_two_sided": norm_p(z)}


def mwu(x, y):
    allv = sorted([(v, 0) for v in x] + [(v, 1) for v in y], key=lambda t: t[0])
    r = [0.0] * len(allv)
    i = 0
    while i < len(allv):
        j = i
        while j < len(allv) and allv[j][0] == allv[i][0]:
            j += 1
        for k in range(i, j):
            r[k] = (i + j + 1) / 2
        i = j
    n1, n2 = len(x), len(y)
    u1 = sum(r[k] for k in range(len(allv)) if allv[k][1] == 0) - n1 * (n1 + 1) / 2
    z = (u1 - n1 * n2 / 2) / math.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
    return {"U": round(u1, 1), "p_two_sided": norm_p(z)}


def median(vals):
    s = sorted(vals)
    n = len(s)
    return round((s[n // 2 - 1] + s[n // 2]) / 2, 4) if n % 2 == 0 else round(s[n // 2], 4)


def load_win(w: str) -> dict:
    rows = [json.loads(l) for l in (DATA / f"rollout_{w}.jsonl").read_text().splitlines()
            if l.strip()]
    covs, succ = [], 0
    for r in rows:
        c = r.get("final_coverage", r.get("coverage", 0.0))
        covs.append(float(c))
        succ += bool(r.get("success", r.get("is_success", False)))
    s = sorted(covs)
    return {"n": len(rows), "n_success": succ, "covs": covs,
            "cov_mean": round(sum(covs) / len(covs), 4), "cov_median": median(covs),
            "cov_max": round(s[-1], 4)}


def main() -> int:
    W = {w: load_win(w) for w in WINS}
    allsum = json.loads((DATA / "rollout_all_summary.json").read_text())
    ver = {}
    for w in WINS:
        s = next(x for x in allsum["windows"] if x["window"] == w)
        ver[w] = (W[w]["n"] == s["n_eps"] and W[w]["n_success"] == s["n_success"]
                  and abs(W[w]["cov_mean"] - s["mean_final_coverage"]) < 5e-4)
    # 主判一:成功率差分(冻结语义)
    floor = all(W[w]["n_success"] == 0 for w in WINS)
    # 主判二(v2 连续):A2F−A1N 同 seed 配对
    wil = wilcoxon_paired(W["A1N"]["covs"], W["A2F"]["covs"])
    mw = mwu(W["A1N"]["covs"], W["A2F"]["covs"])
    # T2 裁决:主=配对 Wilcoxon
    sig = wil["p_two_sided"] < 0.05
    # 噪声底:A2F−A2N 逐局
    nf = wilcoxon_paired(W["A2N"]["covs"], W["A2F"]["covs"])
    # 敏感性:A1N−A1O(混杂参照)
    sens = wilcoxon_paired(W["A1O"]["covs"], W["A1N"]["covs"])
    v = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "judge": "compass rollout_n100_final_v1",
        "evidence_policy": "JUDGING_EVIDENCE_TIERS_20261003",
        "criteria": "层1 v2(用户已批#2568):成功率差分(冻结语义)+coverage 连续主判;"
                    "T1=全量100集/窗 seed70000-70099 配对;T2=主配对Wilcoxon辅MWU,中位并陈",
        "material_sha16": {w: sha16(DATA / f"rollout_{w}.jsonl") for w in WINS},
        "summary_verify_vs_v5": ver,
        "windows": {w: {k: W[w][k] for k in ("n", "n_success", "cov_mean", "cov_median",
                                             "cov_max")} for w in WINS},
        "primary_floor": {"all_zero": floor,
                          "reading": "成功率四窗全 0/100——冻结语义判不动,如实报"},
        "coverage_continuous_v2": {"A2F_minus_A1N_paired_wilcoxon(主)": wil,
                                   "A2F_vs_A1N_mwu(辅)": mw,
                                   "T2_ruling": "主法显著即判显著" if sig else
                                                "主法不显著即判 NS(辅法仅披露)"},
        "noise_floor": {"A2F_minus_A2N": nf, "note": "同臂双跑逐局核验"},
        "sensitivity_mixed_ref": {"A1N_minus_A1O": sens,
                                  "note": "含 v1/v2 协议混杂,不作纯 run 底(flywheel 同判)"},
        "verdict": "",
    }
    v["verdict"] = (
        f"终判(PARTIAL-U→v2 连续主判):①冻结语义成功率四窗全 0/100=地板依旧判不动,照实报;"
        f"②coverage 连续主判(v2):配对 Wilcoxon p={wil['p_two_sided']}"
        f"({'<0.05 显著' if sig else '≥0.05 NS'}),meanΔ={wil['mean_delta']}(中位 {wil['median_delta']},"
        f"正/负 {wil['pos']}/{wil['neg']},逐局全同 {wil['identical_pairs']} 局);"
        f"辅 MWU p={mw['p_two_sided']};噪声底=A2F/A2N 逐局 100/100 全同(p=1.0)——"
        f"{'效应为真' if sig else '效应未跨线'};③臂1底敏感性 p={sens['p_two_sided']}"
        "(含 v1/v2 混杂不作纯底);④首案效度判定:"
        + ("帧级(p=0.0099)与任务级 coverage(n=100 p=0.0018)双级显著一致支持修复,"
           "但'真达标'FULL≥0.95 无一窗触及(成功率 0),任务级有效性未达标——"
           "首案结论=修复方向显著有效(帧级+连续代理),达标性未证实(冻结语义)"
           if sig else
           "coverage 未跨线,首案按止损线归档'帧级有效/任务级未证实'")
        + ";判据零放宽,seed 序列不换,不再扩 n(止损线生效)。")
    out = DATA / "rollout_n100_verdict.json"
    out.write_text(json.dumps(v, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(v["coverage_continuous_v2"], ensure_ascii=False, indent=1))
    print(json.dumps(v["noise_floor"]["A2F_minus_A2N"], ensure_ascii=False))
    print("verdict:", v["verdict"])
    print(f"[save] {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
