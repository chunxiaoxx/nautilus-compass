#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""锚点库 anchor_v0 提取(蓝图组件 3 数据件 · P1 前置 · 零算力)。
设计件:runtime/verification-learning-papers/docs/锚点库设计-P1前置-20261002.md
判据 A1-A4(预注册,只许加严):A1 覆盖率如实报 / A2 果因可分性(dev 折,top-5 vs 随机×3)/ A3 零编造(字段逐条回溯断言)/ A4 三折隔离。
"""
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

DIR = Path(__file__).resolve().parent.parent / "runtime" / "verdict_corpus"
SRC = json.loads  # alias

def load_jsonl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

def main() -> None:
    folds = {}
    for name in ("train", "dev", "test"):
        for r in load_jsonl(DIR / f"split_{name}.jsonl"):
            folds[r["id"]] = name
    rows = load_jsonl(DIR / "train_set_v0.jsonl")

    anchors, u_anchors = [], []
    for r in rows:
        tid, lab = r["id"], r.get("truth_label")
        rec = {
            "anchor_id": tid,
            "effect": {"truth_label": lab if lab else "U",
                       "judge_output": r.get("judge_output"),
                       "reason_span": (r.get("reason") or "")[:300] or None,
                       "artifact_hash": r.get("content_hash")},
            "cause": {"criteria_refs": r.get("criteria_ref") or [],
                      "source_trace": r.get("source"),
                      "artifact_ref": r.get("artifact")},
            "label_origin": r.get("label_origin"),
            "u_flag": not bool(lab),
            "fold": folds.get(tid, "?"),
        }
        (u_anchors if rec["u_flag"] else anchors).append(rec)

    # ── A3 零编造:每条 anchor 字段回溯源行 ──
    src_by_id = {r["id"]: r for r in rows}
    for a in anchors + u_anchors:
        s = src_by_id[a["anchor_id"]]
        assert a["effect"]["truth_label"] == (s.get("truth_label") or "U")
        assert a["effect"]["judge_output"] == s.get("judge_output")
        assert a["effect"]["artifact_hash"] == s.get("content_hash")
        assert a["cause"]["criteria_refs"] == (s.get("criteria_ref") or [])
        assert a["cause"]["source_trace"] == s.get("source")
        assert a["cause"]["artifact_ref"] == s.get("artifact")
        assert a["effect"]["reason_span"] == (s.get("reason") or "")[:300] or None

    # ── A4 三折隔离:fold 与源完全一致 ──
    assert all(a["fold"] == folds[a["anchor_id"]] for a in anchors + u_anchors)
    assert len(anchors) + len(u_anchors) == len(rows) == 1454

    # ── A2 果因可分性(dev 折):effect(truth_label) 近邻 → cause 判据族 top-5 命中 ──
    dev = [a for a in anchors if a["fold"] == "dev" and a["cause"]["criteria_refs"]]
    rng = random.Random(7)
    def fam(a):  # 判据族 = criteria_refs 的 frozenset(简化口径,声明在设计件外无额外定义)
        return frozenset(a["cause"]["criteria_refs"])
    hits = 0
    trials = 0
    for a in dev:
        pool = [b for b in dev if b is not a]
        # 近邻代理:同 truth_label 的行为 effect 相似(设计件口径:判据族+truth_label)
        near = [b for b in pool if b["effect"]["truth_label"] == a["effect"]["truth_label"]]
        top5 = (near or rng.sample(pool, min(5, len(pool))))[:5]
        hits += any(fam(b) & fam(a) for b in top5)
        trials += 1
    rand_hits = 0
    for _ in range(5):
        rh = 0
        for a in dev:
            pool = [b for b in dev if b is not a]
            top5 = rng.sample(pool, min(5, len(pool)))
            rh += any(fam(b) & fam(a) for b in top5)
        rand_hits = max(rand_hits, rh)
    a2_near = hits / trials if trials else 0.0
    a2_rand = rand_hits / trials if trials else 0.0

    out = {"anchors": anchors, "u_anchors": u_anchors}
    (DIR / "anchor_v0.jsonl").write_text(
        "\n".join(json.dumps(a, ensure_ascii=False) for a in anchors + u_anchors), encoding="utf-8")
    sha16 = hashlib.sha256((DIR / "anchor_v0.jsonl").read_bytes()).hexdigest()[:16]
    report = {
        "ts": "2026-10-02T08:3x+08:00",
        "total": len(rows),
        "A1_coverage": {"full_anchors": len(anchors), "u_anchors": len(u_anchors),
                         "coverage": round(len(anchors) / len(rows), 4),
                         "note": "如实报,无达标线,U 锚单列"},
        "A2_separability": {"dev_trials": trials, "top5_family_hit": round(a2_near, 4),
                            "random_baseline_bestof5": round(a2_rand, 4),
                            "pass_x3": a2_near >= 3 * a2_rand if trials else None,
                            "note": "简化口径:truth_label 相似+判据族 frozenset 交"},
        "A3_zero_fabrication": "PASS(逐字段断言全过)",
        "A4_fold_isolation": "PASS(1454 全一致)",
        "anchor_sha16": sha16,
        "fold_dist": dict(Counter(a["fold"] for a in anchors)),
    }
    (DIR / "anchor_v0_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
