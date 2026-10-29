#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""双轨重算(裁决 22765 · 轨 A=1012 原文 / 轨 B=内部加严连续带)

用法:
  python3 ops/ali30q/dualtrack_recompute.py > runtime/_out_20261028_dualtrack.md
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collect_for_quickscreen import is_empty_output, SCRATCHES  # noqa: E402
from s5_json import latest_batch, load_s5_json  # noqa: E402

HOME = Path.home()
V5 = HOME / "Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items"


def wilson_lb(successes: float, n: int, z: float = 1.96) -> float | None:
    if n <= 0:
        return None
    p = successes / n
    z2 = z * z
    den = 1 + z2 / n
    centre = p + z2 / (2 * n)
    spread = z * math.sqrt((p * (1 - p) + z2 / (4 * n)) / n)
    return max(0.0, (centre - spread) / den)


def cont_score(d: dict) -> float | None:
    s = d.get("score")
    if s is None:
        return 0.0 if is_empty_output(d) else None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def bin_score(s: float | None) -> float | None:
    if s is None:
        return None
    return 1.0 if s == 1.0 else 0.0


def collect() -> dict[str, dict]:
    raw: dict[str, dict[str, list]] = {}
    dirs = [V5] + [s for s in SCRATCHES if s.exists()]
    for d in dirs:
        for item in sorted(d.glob("CS-*")):
            s5 = item / "_s5"
            if not s5.exists():
                continue
            ent = raw.setdefault(item.name, {"qwen3.8max": [], "opus5.5": []})
            for pat in ent:
                for f in sorted(s5.glob(f"{pat}_run*_result.json")):
                    r = load_s5_json(f)
                    if not r:
                        continue
                    sc = cont_score(r)
                    if sc is None:
                        continue
                    fails = []
                    uv = r.get("ut_vector") or {}
                    if isinstance(uv, dict):
                        fails = sorted(k for k, v in uv.items() if v in (0, 0.0, False))
                    try:
                        mt = f.stat().st_mtime
                    except OSError:
                        continue
                    ent[pat].append((mt, sc, tuple(fails)))
    out = {}
    for name, models in raw.items():
        rec = {}
        for pat, files in models.items():
            batch = latest_batch([(mt, (sc, fails)) for mt, sc, fails in files])
            rec[pat] = {
                "cont": [sc for _, (sc, _) in batch],
                "fails": [fails for _, (_, fails) in batch],
            }
        if rec["qwen3.8max"]["cont"] or rec["opus5.5"]["cont"]:
            out[name] = rec
    return out


def mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def track_a(q: list[float], o: list[float]) -> tuple[bool, str]:
    reasons = []
    qm, om = mean(q), mean(o)
    if qm is None:
        return False, "qwen 无读数"
    if qm >= 0.70:
        reasons.append(f"qwen均值{qm:.3f}≥0.70")
    non1 = sum(1 for x in q if x != 1.0)
    if non1 < 2:
        reasons.append(f"非全1仅{non1}<2")
    if not o or not any(x == 1.0 for x in o):
        reasons.append("opus无全1")
    if q and o:
        q_all1 = all(x == 1.0 for x in q)
        q_all0 = all(x == 0.0 for x in q)
        o_all1 = all(x == 1.0 for x in o)
        o_all0 = all(x == 0.0 for x in o)
        if (q_all1 and o_all1) or (q_all0 and o_all0):
            reasons.append("全1或全0")
    if qm is not None and om is not None and (om - qm) < 0.20:
        reasons.append(f"区分度{(om-qm):.3f}<20pp")
    ok = not reasons
    return ok, "PASS" if ok else ";".join(reasons)


def track_b(q: list[float], o: list[float], fail_sets: list[tuple]) -> tuple[str, str]:
    """返回 PASS/FAIL/U + 原因。"""
    reasons = []
    qm, om = mean(q), mean(o)
    if qm is None:
        return "FAIL", "qwen 无读数"
    if not (0.25 <= qm < 0.70):
        reasons.append(f"qwen连续均值{qm:.3f}∉[0.25,0.70)")
    if om is None or om < 0.90:
        reasons.append(f"opus均值{om if om is None else f'{om:.3f}'}<0.90")
    if not o or not any(x == 1.0 for x in o):
        reasons.append("opus无全1")
    named = set()
    missing_vec = True
    for fs in fail_sets:
        if fs:
            missing_vec = False
            named.update(fs)
        elif fs == ():
            missing_vec = missing_vec and True
    if any(fs for fs in fail_sets):
        missing_vec = False
    if missing_vec and q:
        status_u = True
        reasons.append("失败UT集合不可验(无ut_vector)")
    else:
        status_u = False
        if len(named) < 2 and (qm is not None and qm < 1.0):
            reasons.append(f"失败UT distinct={len(named)}<2")
    n = len(q)
    lb = wilson_lb(sum(q), n) if n else None
    if n >= 4 and lb is not None and lb < 0.05:
        status_u = True
        reasons.append(f"Wilson LB {lb:.3f}<0.05 标U")
    if status_u:
        return "U", ";".join(reasons) or "U"
    return ("PASS" if not reasons else "FAIL"), ("PASS" if not reasons else ";".join(reasons))


def main() -> None:
    data = collect()
    print("# 双轨重算表(裁决 22765 · 2026-10-28 首表)")
    print()
    print("> 轨 A=1012 原文呈报;轨 B=内部加严连续带(质检前置)。")
    print("> 读数=各题 `_s5` 最新批(F-009 聚簇);连续均值与二值并列。")
    print("> 失败 UT 非退化依赖 `ut_vector`;缺失标 U 不入交付。[实测/不可验] 分层。")
    print()
    print("| 题 | qwen连续 n/均值 | qwen二值均值 | opus n/均值 | 轨A(甲方) | 轨B(内部) | 备注 |")
    print("|---|---|---|---|---|---|---|")
    a_pass, b_pass = [], []
    for name in sorted(data):
        rec = data[name]
        q = rec["qwen3.8max"]["cont"]
        o = rec["opus5.5"]["cont"]
        qb = [bin_score(x) for x in q]
        qm, om, qbm = mean(q), mean(o), mean([x for x in qb if x is not None])
        a_ok, a_why = track_a(q, o)
        b_st, b_why = track_b(q, o, rec["qwen3.8max"]["fails"])
        if a_ok:
            a_pass.append(name)
        if b_st == "PASS":
            b_pass.append(name)
        qn = f"{len(q)}/{qm:.3f}" if qm is not None else f"{len(q)}/—"
        on = f"{len(o)}/{om:.3f}" if om is not None else f"{len(o)}/—"
        qbn = f"{qbm:.3f}" if qbm is not None else "—"
        print(
            f"| {name} | {qn} | {qbn} | {on} | "
            f"{'PASS' if a_ok else 'FAIL'} | {b_st} | {a_why if not a_ok else b_why} |"
        )
    print()
    print(f"- 轨 A PASS {len(a_pass)}: {', '.join(a_pass) or '∅'}")
    print(f"- 轨 B PASS {len(b_pass)}: {', '.join(b_pass) or '∅'}")
    print("- 本表为首表:失败 UT 非退化多标 U(result.json 多数无 ut_vector);补向量后可升 PASS。")


if __name__ == "__main__":
    main()
