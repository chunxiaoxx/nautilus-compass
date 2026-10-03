#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verdict Schema v2 validator+migrator(docs/protocol/VERDICT_SCHEMA_V2.md)。

L1 结构/L2 语义/L3 锚定/L4 一致四级校验;migrate 子命令出 v2 版本存档(原文件不动)。
用法:
  python tools/verdict_schema_v2.py validate <verdict.json>
  python tools/verdict_schema_v2.py migrate  <verdict.json> [--out out_v2.json]
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TIERS = {"measured", "inferred", "unverifiable"}
STATES = {"VERDICT", "PARTIAL", "U_STATE"}


def parse_state(text: str) -> str:
    head = text.split("(")[0]
    if "U" in head or "insufficient" in text or "判不动" in text:
        return "U_STATE"
    if "PARTIAL" in head or "PARTIAL" in text:
        return "PARTIAL"
    return "VERDICT"


def migrate(v: dict) -> dict:
    """v1(今日四真件形态)→v2;已含 v2 段的字段原样保留。"""
    out = dict(v)
    out.setdefault("ts", v.get("ts", ""))
    out.setdefault("judge", v.get("judge", ""))
    out.setdefault("case_id", v.get("case_id", Path("unknown").name))
    out.setdefault("evidence_policy", v.get("evidence_policy",
                                            "JUDGING_EVIDENCE_TIERS_20261003"))
    if "criteria" not in out or not isinstance(out.get("criteria"), dict):
        out["criteria"] = {"ref": (v.get("criteria_positioning")
                                   or (v.get("criteria") if isinstance(v.get("criteria"), str)
                                       else "")),
                           "version": "v1-legacy",
                           "freeze_chain": [{"event": "legacy(迁移件,冻结链待补)", "ref": "-", "ts": v.get("ts", "")}],
                           **({"mapping_note": v["criteria_note"]}
                              if v.get("criteria_note") else {})}
    if "readings" not in out:
        rd = {k: v[k] for k in ("arms", "windows", "readings") if k in v}
        if rd:
            out["readings"] = rd
    if "material" not in out:
        mat = {}
        for k in ("material_dirs", "material"):
            if isinstance(v.get(k), dict):
                mat.update({kk: {"source_path": vv} for kk, vv in v[k].items()})
        for grp in ("arms", "windows"):
            for arm, d in (v.get(grp) or {}).items():
                if isinstance(d, dict) and d.get("rows_sha16"):
                    mat.setdefault(arm, {})["sha16"] = d["rows_sha16"]
        if v.get("material_sha16"):
            mat.update({k: {"sha256": s} for k, s in v["material_sha16"].items()})
        out["material"] = mat
    if "statistics" not in out:
        stats = {}
        if isinstance(v.get("comparisons"), dict):
            items = list(v["comparisons"].items())
            if items:
                stats["primary"] = {"method": "see_source", "data": items[0]}
            if len(items) > 1:
                stats["secondary"] = {"method": "see_source", "data": items[1:]}
        for k in ("coverage_continuous_v2", "noise_floor", "sensitivity_mixed_ref",
                  "main_criterion"):
            if k in v:
                stats[k] = v[k]
        if stats:
            out["statistics"] = {**stats,
                                 "ruling": out.get("statistics", {}).get("ruling",
                                         "legacy 迁移件;裁决规则见 coverage_continuous_v2.T2_ruling"
                                         if "coverage_continuous_v2" in stats else
                                         "legacy 迁移件,两法裁决规则未注册")}
    if "claims" not in out:
        out["claims"] = []
    if isinstance(out.get("verdict"), str):
        text = out["verdict"]
        out["verdict"] = {"state": parse_state(text), "text": text}
    out["verdict"].setdefault("stop_loss", {})
    return out


def validate(v: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warns: list[str] = []
    for f in ("ts", "judge", "evidence_policy", "readings", "findings"):
        if f not in v:
            errors.append(f"L1 顶层缺 {f}")
    if "criteria" not in v or not isinstance(v.get("criteria"), dict):
        errors.append("L1 缺 criteria 段(或为 legacy 字符串,须 migrate)")
    else:
        if not v["criteria"].get("version"):
            errors.append("L1 criteria.version 必填")
    vd = v.get("verdict")
    if isinstance(vd, str):
        errors.append("L1 verdict 须为对象(v2),见 migrate")
        vd = {"state": parse_state(vd), "text": vd}
    if not vd or vd.get("state") not in STATES:
        errors.append(f"L1 verdict.state 枚举外: {vd.get('state') if vd else None}")
    for i, f in enumerate(v.get("findings", [])):
        if f.get("evidence_tier") not in TIERS:
            errors.append(f"L1 findings[{i}].evidence_tier 枚举外")
        if f.get("evidence_tier") in ("inferred", "unverifiable"):
            if not f.get("upgrade_path") and not re.search("推断|不可验|inferred", f.get("basis", "")):
                warns.append(f"L2 findings[{i}] inferred/unverifiable 缺 upgrade_path 且 basis 无推断字样")
    for i, cm in enumerate(v.get("claims", [])):
        if cm.get("supported") is False and not cm.get("boundary"):
            errors.append(f"L2 claims[{i}] supported=false 缺 boundary")
    for k, m in (v.get("material") or {}).items():
        if not (m.get("sha256") or m.get("sha16") or m.get("source_path")):
            warns.append(f"L3 material[{k}] 无任何锚定字段")
    sl = (vd or {}).get("stop_loss") or {}
    if sl and not all(sl.get(k) for k in ("seed_locked", "no_expansion", "no_new_methods")):
        if any(k in sl for k in ("seed_locked", "no_expansion", "no_new_methods")):
            errors.append("L3 stop_loss 三布尔须全 true 才算启用")
    text = (vd or {}).get("text", "")
    if "显著" in text and "statistics" not in v:
        errors.append("L4 verdict 称'显著'但无 statistics 段(主判据旁路嫌疑)")
    if "statistics" in v and not v["statistics"].get("ruling"):
        warns.append("L4 statistics.ruling 未注册(两法分歧无裁决规则)")
    return errors, warns


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    cmd, src = sys.argv[1], Path(sys.argv[2])
    v = json.loads(src.read_text(encoding="utf-8"))
    if cmd == "validate":
        errors, warns = validate(v)
        print(json.dumps({"file": src.name, "errors": errors, "warnings": warns,
                          "compliant": not errors}, ensure_ascii=False, indent=1))
        return 0 if not errors else 1
    if cmd == "migrate":
        out = migrate(v)
        dst = src.with_name(src.stem + "_v2.json")
        dst.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
        errors, warns = validate(out)
        print(json.dumps({"migrated_to": str(dst), "post_errors": errors,
                          "post_warnings": warns, "compliant": not errors},
                         ensure_ascii=False, indent=1))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
