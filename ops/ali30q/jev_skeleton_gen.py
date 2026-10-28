#!/usr/bin/env python3
"""JEV(judgement evidence)预生成骨架 · 函 21309/21321 落地件。

每题一份 jev/CS-XXX.json:
  题号 / 五模型四轮读数槽位 / G 门(gating UT)矩阵 / verify 记录 /
  平均分统计(模型+国内/SOTA 分组)/ 国内外差值与趋势一致性自检列。

已有读数(items/CS-XXX/_s5/*_result.json)自动预填,跑批数据流入重跑即增量填充。
纯 stdlib;用法: python3 jev_skeleton_gen.py [ITEMS_DIR] [-o OUT_DIR]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

MODELS = ["opus5.5", "gpt-6-astra", "qwen3.8max", "glm5.3", "kimi-k3"]
RUNS = [0, 1, 2, 3]
GROUP_CN = {"qwen3.8max", "glm5.3", "kimi-k3"}
GROUP_SOTA = {"opus5.5", "gpt-6-astra"}
CANON = {"kimi-k3-ark": "kimi-k3", "kimi-k3": "kimi-k3", "glm5.3": "glm5.3",
         "glm5.3-anthropic": "glm5.3", "opus5.5": "opus5.5",
         "gpt-6-astra": "gpt-6-astra", "qwen3.8max": "qwen3.8max"}

UTI_RE = re.compile(r"\[\[metadata\.ut_index\]\]\s*\n(.*?)(?=\n\[\[|\n\[verification\]|\Z)", re.S)


def parse_gates(task_toml: Path) -> list[dict]:
    gates = []
    text = task_toml.read_text(encoding="utf-8")
    for m in UTI_RE.finditer(text):
        block = m.group(1)
        name_m = re.search(r'ut_name\s*=\s*"([^"]+)"', block)
        gating_m = re.search(r"gating\s*=\s*(true|false)", block)
        if not (name_m and gating_m and gating_m.group(1) == "true"):
            continue
        dim_m = re.search(r'dimension\s*=\s*"([^"]*)"', block)
        gates.append({"uts": [name_m.group(1)],
                      "dimension": dim_m.group(1) if dim_m else ""})
    return [dict(g, gate=f"G{i+1}") for i, g in enumerate(gates)]


def load_reads(items_dir: Path, item: str) -> dict:
    reads: dict[str, dict] = {m: {} for m in MODELS}
    s5 = items_dir / item / "_s5"
    if not s5.is_dir():
        return reads
    for f in s5.glob("*_result.json"):
        m = re.match(r"(.+)_run(\d+)_result", f.name)
        if not m:
            continue
        model = CANON.get(m.group(1), m.group(1))
        if model not in reads or int(m.group(2)) not in RUNS:
            continue
        try:
            r = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if r.get("score") is None:
            continue
        reads[model][int(m.group(2))] = {
            "score": r["score"], "elapsed_s": r.get("elapsed_s"),
            "error": r.get("error", ""), "ut_pass_n": sum(r.get("ut_vector", {}).values()),
            "ut_total": len(r.get("ut_vector", {})),
        }
    return reads


def fill_stats(jev: dict) -> None:
    # 甲方澄清口径(1012/函21321): 平均分=二值(全过轮数/总轮数),passrate=UT 通过率均值
    per_model = {}
    for model, runs in jev["reads"].items():
        # 全过判定: ut_vector 可用按 ut 全过;旧读数 ut_vector 缺失时以 score==1.0 兜底
        full = [1 if (v["ut_total"] and v["ut_pass_n"] == v["ut_total"]) or v["score"] == 1.0 else 0
                for v in runs.values()]
        if full:
            per_model[model] = round(sum(full) / len(full), 4)
    jev["avg_score"]["per_model"] = per_model

    def group_avg(group):
        vals = [per_model[m] for m in group if m in per_model]
        return round(sum(vals) / len(vals), 4) if vals else None

    sota, cn = group_avg(GROUP_SOTA), group_avg(GROUP_CN)
    jev["avg_score"]["group_sota"] = sota
    jev["avg_score"]["group_cn"] = cn
    if sota is not None and cn is not None:
        jev["gap_check"]["cn_minus_sota_pp"] = round((cn - sota) * 100, 2)
        jev["gap_check"]["meets_20pp"] = bool(sota - cn >= 0.20)
    pr = {}
    for model, runs in jev["reads"].items():
        rates = [v["ut_pass_n"] / v["ut_total"] for v in runs.values() if v["ut_total"]]
        if rates:
            pr[model] = round(sum(rates) / len(rates), 4)
    jev["avg_score"]["passrate_per_model"] = pr
    if per_model and pr:
        hi = max(per_model, key=per_model.get)
        lo = min(per_model, key=per_model.get)
        if per_model[hi] != per_model[lo]:
            jev["gap_check"]["passrate_trend_consistent"] = bool(pr[hi] >= pr[lo])
        else:
            jev["gap_check"]["passrate_trend_consistent"] = None
    jev["gap_check"]["coverage_n"] = sum(len(v) for v in jev["reads"].values())
    jev["gap_check"]["coverage_full"] = jev["gap_check"]["coverage_n"] == len(MODELS) * len(RUNS)


def build(items_dir: Path, item: str) -> dict:
    task_toml = items_dir / item / "task.toml"
    gates = parse_gates(task_toml) if task_toml.is_file() else []
    reads = load_reads(items_dir, item)
    jev = {
        "item": item,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "schema": "jev-skeleton-v1 (letter 21309/21321)",
        "evidence_tier": "skeleton-empty-slots=PENDING; filled=per-field [实测] provenance _s5/*_result.json",
        "g_gates": {g["gate"]: {"uts": g["uts"], "dimension": g.get("dimension", ""),
                                "reads": {m: {r: None for r in RUNS} for m in MODELS}}
                    for g in gates},
        "reads": reads,
        "gold_check": "PENDING",
        "verify": {"independent_recompute": "PENDING", "recompute_session": None},
        "avg_score": {},
        "gap_check": {},
    }
    fill_stats(jev)
    return jev


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("items_dir", nargs="?",
                    default="/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items")
    ap.add_argument("-o", "--out", default=str(Path(__file__).parent / "jev"))
    a = ap.parse_args(argv)
    items_dir, out = Path(a.items_dir), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    made = 0
    for d in sorted(items_dir.glob("CS-*")):
        if not d.is_dir() or not (d / "task.toml").is_file():
            continue
        jev = build(items_dir, d.name)
        (out / f"{d.name}.json").write_text(
            json.dumps(jev, ensure_ascii=False, indent=1), encoding="utf-8")
        made += 1
    print(f"[OK] {made} JEV skeletons -> {out}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
