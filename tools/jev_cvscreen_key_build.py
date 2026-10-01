#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jev CV-screening 校准测量 · answer key 构建(K 先于模型承诺件)。

规则(预注册 §二/§四点五):
- key 只从 manifest.json 的 profile 文本机械映射,零模型输入
- 映射依据必须引用 profile 原文短语;无依据维度 = "U"(insufficient_evidence)
- 映射表随 key 同发布(可审计)
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "runtime" / "typesafe_jev_cvscreen" / "manifest.json"
OUT = ROOT / "runtime" / "typesafe_jev_cvscreen" / "answer_key.json"

# ── 机械映射表(profile 短语 → 维度 key;锚定 fields.ts choice 选项名) ──
MAP_CAREER = [
    (r"lateral moves", "lateral_moves",
     "profile states 'lateral moves' → fields.ts criteria lateral_moves"),
    (r"job[ -]?hopping", "job_hopping",
     "profile states 'job hopping' → fields.ts criteria job_hopping"),
    (r"steady growth|clear progression", "steady_growth",
     "profile states growth → fields.ts criteria steady_growth"),
]


def career_key(profile: str):
    for pat, val, basis in MAP_CAREER:
        if re.search(pat, profile, re.I):
            return val, basis
    return "U", "profile has no progression-shape phrase (only tenure/employer counts)"


def tech_key(profile: str):
    # manifest 不含 hands-on depth 意图;仅当 profile 明写才锚
    if re.search(r"hands-on|deep specialist|architect", profile, re.I):
        m = "profile states depth phrase — anchor"
        return "ANCHOR_NEEDED", m
    return "U", "manifest carries no hands-on-depth intent; scoring levels 0-5 not derivable"


def main():
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = []
    for f in man["files"]:
        prof = f.get("profile", "")
        ck, cb = career_key(prof)
        tk, tb = tech_key(prof)
        rows.append({
            "qid": f["file"],
            "language": f.get("language"),
            "career_progression": {"key": ck, "basis": cb},
            "technical_depth": {"key": tk, "basis": tb},
            "ownership_leadership": {"key": "U", "basis": "no manifest intent"},
            "communication": {"key": "U", "basis": "no manifest intent"},
            "motivation_fit": {"key": "U", "basis": "depends on role preset; no single-role manifest intent"},
            "english_level": {"key": "U", "basis": f"language={f.get('language')} is indirect evidence only"},
            "flag_fields": {  # 副读数:合规 flag,不进 score(泄漏率测量对象)
                "military": bool(re.search(r"military", prof, re.I)),
                "age_evidence": "age evidence" in prof.lower() and "no age evidence" not in prof.lower(),
                "gender": re.search(r"\b(male|female)\b", prof, re.I).group(0).lower() if re.search(r"\b(male|female)\b", prof, re.I) else None,
            },
            "profile_verbatim": prof,
        })
    out = {
        "_meta": {
            "corpus_sha16": "c304f878800b1fcb",
            "key_built_at": "2026-10-01",
            "rule": "manifest-only mechanical mapping; U where no basis",
            "model_runs_before_this_commit": 0,
        },
        "items": rows,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    n_lat = sum(1 for r in rows if r["career_progression"]["key"] == "lateral_moves")
    n_hop = sum(1 for r in rows if r["career_progression"]["key"] == "job_hopping")
    n_u = sum(1 for r in rows if r["career_progression"]["key"] == "U")
    print(f"key built: {len(rows)} items | career: lateral={n_lat} hopping={n_hop} U={n_u}")
    print(f"anchor-needed(tech): {sum(1 for r in rows if r['technical_depth']['key']=='ANCHOR_NEEDED')}")


if __name__ == "__main__":
    main()
