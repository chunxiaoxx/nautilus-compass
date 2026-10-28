#!/usr/bin/env python3
"""资格战区分度量化门 · Jaccard / 失败签名多样性(函 22064 · 1012 原文)

判据正本: docs/metering/JUDGE_GATES_QUAL_BATTLE_20261026.md
用法:
  python3 ops/ali30q/discrimination_jaccard.py <item_dir>
  读 items/CS-NNN/_s5/*_result.json 的 ut_vector,打印三门+UNVERIFIED 脚注。

失败签名 = frozenset(ut 名 | ut_vector[ut]==0)
全过轮(失败集空)不进多样性分母,也不进 Jaccard 分子/分母。
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s5_json import latest_batch, load_s5_json  # noqa: E402
from collect_for_quickscreen import is_empty_output  # noqa: E402

CANON = {
    "qwen3.8max": "qwen3.8max",
    "qwen": "qwen3.8max",
    "kimi-k3": "kimi-k3",
    "kimi-k3-ark": "kimi-k3",
    "glm5.3": "glm5.3",
    "glm5.3-anthropic": "glm5.3",
    "opus5.5": "opus5.5",
    "opus5.5-qixuw": "opus5.5",
    "gpt-6-astra": "gpt-6-astra",
    "gpt6-astra": "gpt-6-astra",
}
MODELS = ("qwen3.8max", "kimi-k3", "glm5.3", "opus5.5", "gpt-6-astra")
SOTA = frozenset({"opus5.5", "gpt-6-astra"})
DOMESTIC = frozenset({"qwen3.8max", "glm5.3", "kimi-k3"})


def fail_set(ut_vector: dict[str, Any] | None) -> frozenset[str] | None:
    """None = 本轮不可用(无向量); empty = 全过。"""
    if not ut_vector:
        return None
    return frozenset(name for name, v in ut_vector.items() if int(v) == 0)


def jaccard_distance(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return 1.0 - (len(a & b) / len(union))


def _mean(xs: Iterable[float]) -> float | None:
    xs = list(xs)
    if not xs:
        return None
    return sum(xs) / len(xs)


def pair_mean_distance(sets: list[frozenset[str]]) -> float | None:
    if len(sets) < 2:
        return None
    dists = [
        jaccard_distance(sets[i], sets[j])
        for i in range(len(sets))
        for j in range(i + 1, len(sets))
    ]
    return _mean(dists)


def canonicalize_model(raw: str) -> str | None:
    if not raw:
        return None
    if raw in CANON:
        return CANON[raw]
    for prefix, canon in CANON.items():
        if raw.startswith(prefix):
            return canon
    return None


def _dedup_alias_runs(
    staged: list[tuple[float, dict[str, Any]]],
) -> list[tuple[float, dict[str, Any]]]:
    """F-014: canonicalize 后同 (model, run) 只留 mtime 最新。

    kimi-k3 / kimi-k3-ark(以及 glm5.3 / glm5.3-anthropic)同窗双写会把 n 翻倍,
    把 signature max_share 撑到刚好过门(CS-303 实证: kimi n=8 假 PASS)。
    run 缺失的记录不去重,原样保留。
    """
    best: dict[tuple[str, Any], tuple[float, dict[str, Any]]] = {}
    leftovers: list[tuple[float, dict[str, Any]]] = []
    for mt, rec in staged:
        model = rec.get("model")
        run = rec.get("run")
        if not model or run is None:
            leftovers.append((mt, rec))
            continue
        key = (str(model), run)
        prev = best.get(key)
        if prev is None or mt >= prev[0]:
            best[key] = (mt, rec)
    return leftovers + list(best.values())


def load_runs(item_dir: Path, use_latest_batch: bool = True) -> list[dict[str, Any]]:
    """F-012: 默认按模型 mtime 聚簇只取最新批,与快筛 latest_batch 同口径。
    F-014: 别名通道先按 (canon_model, run) 去重,再聚簇。"""
    s5 = item_dir / "_s5"
    if not s5.is_dir():
        return []
    staged: list[tuple[float, dict[str, Any]]] = []
    for p in sorted(s5.glob("*_result.json")):
        d = load_s5_json(p)
        if not d:
            continue
        try:
            mt = p.stat().st_mtime
        except OSError:
            continue
        model = canonicalize_model(str(d.get("model") or ""))
        fs = fail_set(d.get("ut_vector"))
        score = d.get("score")
        binary = None
        if fs is not None:
            binary = 1 if len(fs) == 0 else 0
        elif score is not None:
            try:
                binary = 1 if float(score) >= 1.0 - 1e-9 else 0
            except (TypeError, ValueError):
                binary = None
        else:
            # F-016: 完结空输出记 binary=0,仍 usable=False(无失败签名)
            if is_empty_output(d):
                binary = 0
        staged.append(
            (
                mt,
                {
                    "path": p.name,
                    "model": model,
                    "run": d.get("run"),
                    "score": score,
                    "fail_set": fs,
                    "binary": binary,
                    "usable": fs is not None,
                    "mtime": mt,
                },
            )
        )
    staged = _dedup_alias_runs(staged)
    if not use_latest_batch:
        return [r for _, r in staged]
    by_model: dict[str, list[tuple[float, dict[str, Any]]]] = defaultdict(list)
    for mt, rec in staged:
        by_model[rec["model"] or "_unknown"].append((mt, rec))
    out: list[dict[str, Any]] = []
    for files in by_model.values():
        out.extend(rec for _, rec in latest_batch(files))
    return out


def binary_passrate(runs: list[dict[str, Any]], model: str) -> tuple[float | None, int]:
    xs = [r["binary"] for r in runs if r["model"] == model and r["binary"] is not None]
    if not xs:
        return None, 0
    return sum(xs) / len(xs), len(xs)


def signature_gates(runs: list[dict[str, Any]]) -> dict[str, Any]:
    """多样性 / 最大单一签名 / Jaccard 比。"""
    non_all = [r for r in runs if r["usable"] and r["fail_set"] is not None and len(r["fail_set"]) > 0]
    n = len(non_all)
    if n == 0:
        return {
            "n_non_allpass": 0,
            "diversity": None,
            "max_share": None,
            "jaccard_ratio": None,
            "status": "UNVERIFIED",
            "reason": "无非全过可用轮(全过或全缺向量),签名门不可算",
        }
    sigs = [r["fail_set"] for r in non_all]
    uniq = set(sigs)
    counts = Counter(sigs)
    diversity = len(uniq) / n
    max_share = max(counts.values()) / n

    by_model: dict[str, list[frozenset[str]]] = defaultdict(list)
    for r in non_all:
        if r["model"]:
            by_model[r["model"]].append(r["fail_set"])

    intra = [
        d
        for m, ss in by_model.items()
        if (d := pair_mean_distance(ss)) is not None
    ]
    intra_mean = _mean(intra)

    model_sets = {m: ss for m, ss in by_model.items() if ss}
    names = sorted(model_sets)
    cross: list[float] = []
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            # 跨模型:两模型各自失败集两两平均
            dists = [
                jaccard_distance(sa, sb)
                for sa in model_sets[a]
                for sb in model_sets[b]
            ]
            if dists:
                cross.append(sum(dists) / len(dists))
    cross_mean = _mean(cross)

    if intra_mean is None or cross_mean is None:
        ratio, ratio_status = None, "UNVERIFIED"
        models_with_fail = sorted(m for m, ss in by_model.items() if ss)
        if len(models_with_fail) == 1:
            ratio_reason = (
                f"仅{models_with_fail[0]}有非全过轮,跨模型 Jaccard 不可算"
            )
        elif intra_mean is None:
            ratio_reason = "同模型失败轮<2,Jaccard 比不可算"
        else:
            ratio_reason = "跨模型对数不足,Jaccard 比不可算"
    elif intra_mean < 1e-12:
        if cross_mean > 0:
            ratio, ratio_status, ratio_reason = float("inf"), "PASS", "同模型距离≈0且跨模型>0"
        else:
            ratio, ratio_status, ratio_reason = 0.0, "UNVERIFIED", "同模型与跨模型距离均为 0"
    else:
        ratio = cross_mean / intra_mean
        ratio_status = "PASS" if ratio >= 1.25 else "FAIL"
        ratio_reason = ""

    div_ok = diversity >= 0.50
    share_ok = max_share <= 0.50
    hard = [div_ok, share_ok]
    if ratio_status == "FAIL":
        status = "FAIL"
    elif ratio_status == "UNVERIFIED" or not all(hard):
        status = "FAIL" if not all(hard) else "UNVERIFIED"
    else:
        status = "PASS"

    return {
        "n_non_allpass": n,
        "n_unique_signatures": len(uniq),
        "diversity": round(diversity, 4),
        "diversity_pass": div_ok,
        "max_share": round(max_share, 4),
        "max_share_pass": share_ok,
        "intra_mean": None if intra_mean is None else round(intra_mean, 4),
        "cross_mean": None if cross_mean is None else round(cross_mean, 4),
        "jaccard_ratio": None if ratio is None else ("inf" if ratio == float("inf") else round(ratio, 4)),
        "jaccard_status": ratio_status,
        "jaccard_note": ratio_reason,
        "status": status,
    }


def qwen_point_gate(passrate: float | None, n: int) -> dict[str, Any]:
    """qwen 二值 passrate 必须落在 {0.25, 0.50}; 禁 0。覆盖不足 → UNVERIFIED。"""
    if passrate is None or n < 4:
        return {"status": "UNVERIFIED", "passrate": passrate, "n": n, "reason": "qwen 可用轮<4"}
    # 允许浮点: 1/4 或 2/4
    allowed = {0.25, 0.50}
    hit = any(abs(passrate - a) < 1e-9 for a in allowed)
    if passrate == 0 or abs(passrate) < 1e-9:
        return {"status": "FAIL", "passrate": passrate, "n": n, "reason": "qwen=0 一律不达标(须改题至 25%/50%)"}
    if not hit:
        return {
            "status": "FAIL",
            "passrate": passrate,
            "n": n,
            "reason": f"qwen passrate={passrate:.2%} 不在 {{25%,50%}}",
        }
    return {"status": "PASS", "passrate": passrate, "n": n, "reason": ""}


def sota_gap_gate(
    qwen_pr: float | None, sota_prs: dict[str, tuple[float | None, int]]
) -> dict[str, Any]:
    present = {m: v for m, v in sota_prs.items() if v[0] is not None and v[1] > 0}
    if qwen_pr is None or len(present) < 1:
        return {"status": "UNVERIFIED", "gap": None, "reason": "qwen 或 SOTA 缺腿"}
    if len(present) < 2:
        # 单腿结论不可交付(10/24 教训),标 UNVERIFIED 不冒充 PASS
        sota_mean = next(iter(present.values()))[0]
        gap = (sota_mean or 0) - qwen_pr
        return {
            "status": "UNVERIFIED",
            "gap": round(gap, 4),
            "sota_mean": sota_mean,
            "reason": "SOTA 仅单腿,区分度不入交付",
        }
    sota_mean = sum(v[0] for v in present.values()) / len(present)  # type: ignore[arg-type]
    gap = sota_mean - qwen_pr
    ok = gap > 0.20
    return {
        "status": "PASS" if ok else "FAIL",
        "gap": round(gap, 4),
        "sota_mean": round(sota_mean, 4),
        "reason": "" if ok else f"SOTA-qwen={gap:.1%} 未过 >20pp",
    }


def mean_gradient_gate(item_dir: Path) -> dict[str, Any]:
    """22811 主门(2026-10-28 甲方判据实质变更):平均分数(UT通过率)梯度。

    SOTA 侧均分 − 国内侧均分 ≥ 15pp 才达标;passrate 二值梯度降为并列
    观察列(通报要求 passrate/均分两列都要有梯度,门值见 sota_gap_gate)。
    均分口径 = score(即该轮 UT 通过率),取模型全部 run 均值。
    """
    per_model = defaultdict(list)
    s5 = Path(item_dir) / "_s5"
    for p in sorted(s5.glob("*_result.json")):
        try:
            d = json.load(open(p))
        except Exception:
            continue
        m = canonicalize_model(d.get("model", ""))
        if not m:
            continue
        sc = d.get("score")
        uv = d.get("ut_vector") or {}
        if sc is None:
            if not uv:
                continue
            sc = sum(int(v) for v in uv.values()) / len(uv)
        per_model[m].append(float(sc))
    dom = per_model.get("qwen3.8max", [])
    sota = [x for m in SOTA for x in per_model.get(m, [])]
    if not dom or not sota:
        return {
            "status": "UNVERIFIED",
            "gap": None,
            "dom_mean": None,
            "sota_mean": None,
            "reason": "qwen 或 SOTA 侧均分数据缺腿",
        }
    dom_mean, sota_mean = sum(dom) / len(dom), sum(sota) / len(sota)
    gap = sota_mean - dom_mean
    ok = gap >= 0.15
    dom_all = [x for m in DOMESTIC for x in per_model.get(m, [])]
    dom_all_mean = sum(dom_all) / len(dom_all) if dom_all else None
    per_model_means = {
        m: round(sum(v) / len(v), 4) for m, v in sorted(per_model.items()) if v
    }
    return {
        "status": "PASS" if ok else "FAIL",
        "gap": round(gap, 4),
        "dom_mean": round(dom_mean, 4),
        "sota_mean": round(sota_mean, 4),
        "dom_all_mean": round(dom_all_mean, 4) if dom_all_mean is not None else None,
        "per_model_means": per_model_means,
        "reason": ""
        if ok
        else f"均分梯度(qwen vs SOTA)={gap:.1%} 未达 ≥15pp 主门(22811,甲方 507 判例同口径)",
    }


def evaluate(item_dir: Path) -> dict[str, Any]:
    runs = load_runs(item_dir)
    prs = {m: binary_passrate(runs, m) for m in MODELS}
    qwen_pr, qwen_n = prs["qwen3.8max"]
    report = {
        "item": item_dir.name,
        "n_result_files": len(runs),
        "n_usable_vectors": sum(1 for r in runs if r["usable"]),
        "binary_passrate": {m: {"passrate": pr, "n": n} for m, (pr, n) in prs.items()},
        "qwen_point": qwen_point_gate(qwen_pr, qwen_n),
        # 主门(22811):均分梯度 ≥15pp;sota_gap 降为 passrate 并列观察列
        "mean_gradient": mean_gradient_gate(item_dir),
        "sota_gap": sota_gap_gate(
            qwen_pr, {m: prs[m] for m in ("opus5.5", "gpt-6-astra")}
        ),
        "signature": signature_gates(runs),
    }
    parts = [
        report["mean_gradient"]["status"],
        report["qwen_point"]["status"],
        report["sota_gap"]["status"],
        report["signature"]["status"],
    ]
    if "FAIL" in parts:
        report["overall"] = "FAIL"
    elif "UNVERIFIED" in parts:
        report["overall"] = "UNVERIFIED"
    else:
        report["overall"] = "PASS"
    return report


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: discrimination_jaccard.py <item_dir>", file=sys.stderr)
        return 2
    item = Path(argv[1])
    rep = evaluate(item)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if rep["overall"] != "FAIL" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
