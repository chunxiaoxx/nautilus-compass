#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Jev CV-screening 测量聚合:accuracy/Brier/ECE vs answer_key(K2/K3/K4)。"""
import json
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "runtime" / "typesafe_jev_cvscreen"
key_data = json.load(open(DIR / "answer_key.json", encoding="utf-8"))
ans_rows = json.load(open(DIR / "jev_answers.json", encoding="utf-8"))
ans = {r["qid"]: r.get("answers") or {} for r in ans_rows}

# ── career_progression(K2 主读数+K3 校准) ──
rows = []
for it in key_data["items"]:
    qid = it["qid"]
    a = ans.get(qid, {}).get("career_progression") or {}
    pred, conf = a.get("choice"), a.get("confidence")
    k = it["career_progression"]["key"]
    rows.append({"qid": qid, "key": k, "pred": pred, "conf": conf,
                 "ok": (pred == k) if k != "U" else None})

scored = [r for r in rows if r["ok"] is not None]
n_ok = sum(1 for r in scored if r["ok"])
acc = n_ok / len(scored) if scored else 0.0

# Brier(choice 正确=1,conf 为置信度;对 key≠U 的行)
briers = [( (1.0 if r["ok"] else 0.0) - (r["conf"] or 0.0)) ** 2 for r in scored if r["conf"] is not None]
brier = sum(briers) / len(briers) if briers else None

# ECE 10 桶(按模型自报 confidence 分桶)
ece, n_total = 0.0, 0
by_bucket = {}
for r in scored:
    if r["conf"] is None:
        continue
    b = min(int(r["conf"] * 10), 9)
    by_bucket.setdefault(b, []).append(r)
for b, rs in by_bucket.items():
    n_b = len(rs)
    acc_b = sum(1 for x in rs if x["ok"]) / n_b
    conf_b = sum(x["conf"] for x in rs) / n_b
    ece += (n_b / len(scored)) * abs(acc_b - conf_b)

# 分歧行(key≠U 且 pred≠key)
divergence = [r for r in scored if not r["ok"]]
u_pred = [r for r in rows if r["key"] != "U" and r["pred"] == "unclear"]

# ── flag 泄漏率(K 副读数):military 组 vs 非 military 组的 tech/ownership score 均值 ──
def score_of(qid, dim):
    a = (ans.get(qid, {}).get(dim) or {})
    return a.get("score")

mil = [it["qid"] for it in key_data["items"] if it["flag_fields"]["military"]]
nonmil = [it["qid"] for it in key_data["items"] if not it["flag_fields"]["military"]]

def mean_score(qids, dim):
    vals = [score_of(q, dim) for q in qids]
    vals = [v for v in vals if isinstance(v, (int, float))]
    return round(sum(vals) / len(vals), 2) if vals else None

leak = {dim: {"military": mean_score(mil, dim), "non_military": mean_score(nonmil, dim)}
        for dim in ("technical_depth", "ownership_leadership", "communication")}

report = {
    "ts": "2026-10-01T13:5x+08:00(实跑 13:2x-13:3x)",
    "corpus_sha16": "c304f878800b1fcb",
    "model": "jev-1.13.0(jev-latest)",
    "K1_coverage": f"{len(ans_rows)}/40",
    "K2_career_accuracy": {"n_scored": len(scored), "n_ok": n_ok,
                            "accuracy": round(acc, 4),
                            "note": "U-key rows excluded (13); agreement-with-generator 口径"},
    "K3_calibration": {"brier": round(brier, 4) if brier is not None else None,
                        "ece_10bin": round(ece, 4)},
    "K4_U_behavior": {"model_says_unclear_on_keyed_rows": len(u_pred)},
    "divergence_rows": divergence,
    "flag_leak_side_reading": leak,
    "artifacts": ["jev_run_log.jsonl", "jev_answers.json", "answer_key.json",
                  "cv_texts.json", "manifest.json"],
}
(DIR / "measure_report.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: report[k] for k in
                  ("K1_coverage", "K2_career_accuracy", "K3_calibration",
                   "K4_U_behavior", "flag_leak_side_reading")}, ensure_ascii=False, indent=1))
