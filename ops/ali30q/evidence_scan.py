#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gate-evidence 读数证据链完整性扫描器(2026-10-30 · CS-007 污染第二例后立)。

扫描三数据面全部 _s5/*_result.json:
  CONFLICT      内嵌未解决 merge conflict 标记(<<<<<<<)——CS-007 案签名
  UTMIX         同题各轮 UT 数不一致(ut 集合应恒定,口径漂移=撞名/换版嫌疑)
  SCOREMISMATCH score 与 ut_vector 不自洽(score=1.0 但有 UT 挂/有 ut 但 score=None)
  EMPTYUT       ut_vector 空(死件,gate5 会拒载,此处留痕)
与 gate5/stocktake 互补:gate5 判达标,本器判证据链可采信。
用法: python3 ops/ali30q/evidence_scan.py [--json OUT]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate5_stocktake import BASES  # noqa: E402

CONFLICT_MARK = "<<<<<<<"


def scan_item(item: Path) -> dict:
    findings = {"item": item.name, "CONFLICT": [], "UTMIX": None,
                "SCOREMISMATCH": [], "EMPTYUT": [], "n_valid": 0}
    ut_counts = {}
    for f in sorted(item.glob("_s5/*_run[0-9]_result.json")):
        try:
            raw = f.read_text(encoding="utf-8", errors="replace")
            d = json.loads(raw)
        except Exception:
            if CONFLICT_MARK in raw:
                findings["CONFLICT"].append(f"{f.name}: conflict致JSON损坏")
            else:
                findings["SCOREMISMATCH"].append(f"{f.name}: JSON解析失败")
            continue
        if CONFLICT_MARK in raw:
            findings["CONFLICT"].append(f.name)
        uv = d.get("ut_vector")
        if not isinstance(uv, dict) or not uv:
            findings["EMPTYUT"].append(f.name)
            continue
        findings["n_valid"] += 1
        ut_counts[f.name] = len(uv)
        score = d.get("score")
        all_pass = all(v == 1 for v in uv.values())
        if score == 1.0 and not all_pass:
            findings["SCOREMISMATCH"].append(f"{f.name}: score=1.0 但 UT 有挂")
        if score is None:
            findings["SCOREMISMATCH"].append(f"{f.name}: 有 ut_vector 但 score=None")
    if ut_counts:
        distinct = set(ut_counts.values())
        if len(distinct) > 1:
            findings["UTMIX"] = f"{len(distinct)}种UT数: {sorted(distinct)}"
    return findings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="runtime/pipeline_state/evidence_scan_latest.json")
    a = ap.parse_args()
    rows, clean = [], 0
    seen = set()
    for base in BASES:
        if not base.is_dir():
            continue
        for item in sorted(base.iterdir()):
            if item.is_dir() and item.name.startswith("CS-") and item.name not in seen:
                seen.add(item.name)
                r = scan_item(item)
                rows.append(r)
                if not (r["CONFLICT"] or r["UTMIX"] or r["SCOREMISMATCH"] or r["EMPTYUT"]):
                    clean += 1
    bad = [r for r in rows if r["CONFLICT"] or r["UTMIX"] or r["SCOREMISMATCH"] or r["EMPTYUT"]]
    out = {"schema": "evidence-scan-v1", "bases": [str(b) for b in BASES],
           "n_items": len(rows), "n_clean": clean, "n_flagged": len(bad), "rows": rows}
    Path(a.json).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"证据链扫描: {len(rows)} 题 · 干净 {clean} · 🔴带伤 {len(bad)}")
    for r in bad:
        tags = [k for k in ("CONFLICT", "UTMIX", "SCOREMISMATCH", "EMPTYUT")
                if r[k] and (not isinstance(r[k], list) or r[k])]
        print(f"  {r['item']}: {','.join(tags)}")
        if r["CONFLICT"]:
            print(f"     └ conflict件: {r['CONFLICT']}")
        if r["UTMIX"]:
            print(f"     └ {r['UTMIX']}")
    print(f"全量JSON: {a.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
