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


def load_runs(item_dir: Path) -> list[dict[str, Any]]:
    s5 = item_dir / "_s5"
    if not s5.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(s5.glob("*_result.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
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
        out.append(
            {
                "path": p.name,
                "model": model,
                "run": d.get("run"),
                "score": score,
                "fail_set": fs,
                "binary": binary,
                "usable": fs is not None,
            }
        )
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
        ratio_reason = "跨模型或同模型对数不足,Jaccard 比不可算"
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
        "sota_gap": sota_gap_gate(
            qwen_pr, {m: prs[m] for m in ("opus5.5", "gpt-6-astra")}
        ),
        "signature": signature_gates(runs),
    }
    parts = [
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
