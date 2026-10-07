#!/usr/bin/env python3
"""corpus_pipeline.py · 判例→判分器语料管道 (A 件, 2026-10-06 · R270)

合并 verdict_corpus 三 split + delta/*.jsonl(+ 未来判例集导出件),按 qid 去重分组防泄漏,
产 SFT 就绪清单+manifest(sha16+计数)。触发器:train 计数每 +500 打印 RETRAIN-CANDIDATE
(判据:PRECOR 修订版或 P2v2 同门复用);7B 对拍触发=train≥3000(用户 10/6 拍)。

用法: python tools/corpus_pipeline.py [--root runtime/verdict_corpus]
只读输入,写 manifest_corpus_pipeline.json 于 root 目录。幂等。
"""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path

SFT_TRIGGERS = {"retrain_candidate_step": 500, "sevenb_compare": 3000}


def sha16(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()[:16]


def load_jsonl(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def qid_of(e: dict) -> str:
    return ((e.get("artifact") or {}).get("qid") or e.get("id")
            or e.get("pf_id", ""))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="runtime/verdict_corpus")
    a = ap.parse_args()
    root = Path(a.root)

    sources: dict[str, list[dict]] = {}
    for name in ("split_train_v1", "split_dev_v1", "split_test_v1"):
        sources[name] = load_jsonl(root / f"{name}.jsonl")
    deltas = sorted((root / "delta").glob("delta_*.jsonl"))
    for d in deltas:
        sources[f"delta:{d.name}"] = load_jsonl(d)
    # ORG-FUEL 源(R294):过门 org 判例(L0/L1 且 judge pass)计入独立源
    fuel_v = root.parent / "org_fuel/fuel_verdicts.jsonl"
    if fuel_v.exists():
        gate = [json.loads(l) for l in fuel_v.read_text(encoding="utf-8").splitlines()
                if l.strip() and json.loads(l).get("judge_verdict") == "pass"
                and json.loads(l).get("anchor_level") in ("L0", "L1")]
        sources["org_fuel:gate_passed"] = gate

    # qid 防泄漏:同 qid 只保留 train/首个来源版;跨 split 重复=报数
    seen: dict[str, str] = {}
    dup = []
    merged: dict[str, dict] = {}
    for src, items in sources.items():
        for e in items:
            q = qid_of(e)
            if not q:
                continue
            if q in seen:
                dup.append((q, seen[q], src))
                continue
            seen[q] = src
            merged[q] = {"source": src, "entry": e}

    counts = {s: len(v) for s, v in sources.items()}
    n_train = len(sources["split_train_v1"])
    n_total = len(merged)

    all_bytes = json.dumps(
        [merged[q]["entry"] for q in sorted(merged)], ensure_ascii=False, sort_keys=True
    ).encode()
    h = sha16(all_bytes)

    triggers = {
        "retrain_candidate": n_train >= 1 and (n_train // SFT_TRIGGERS["retrain_candidate_step"])
        > ((n_train - len(sources.get("delta:delta_0003.jsonl", [])) or 0)
           // SFT_TRIGGERS["retrain_candidate_step"]),
        "sevenb_compare_ready": n_train >= SFT_TRIGGERS["sevenb_compare"],
    }

    manifest = {
        "generated_for": "judge_lora corpus pipeline (A 件)",
        "counts_by_source": counts,
        "merged_unique_by_qid": n_total,
        "cross_source_dups_ignored": len(dup),
        "train_count": n_train,
        "next_retrain_candidate_at": ((n_train // SFT_TRIGGERS["retrain_candidate_step"]) + 1)
        * SFT_TRIGGERS["retrain_candidate_step"],
        "sevenb_target": SFT_TRIGGERS["sevenb_compare"],
        "sevenb_remaining": max(0, SFT_TRIGGERS["sevenb_compare"] - n_train),
        "merged_sha16": h,
        "triggers": {k: bool(v) for k, v in triggers.items()},
    }
    out = root / "manifest_corpus_pipeline.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=1))
    if triggers["retrain_candidate"]:
        print("RETRAIN-CANDIDATE: 语料较上次候选阈值 +500,评估 LoRA 重训")
    if triggers["sevenb_compare_ready"]:
        print("SEVENB-COMPARE-READY: train≥3000,按 PRECOR_JUDGE14B_UPGRADE 框架对拍")
    return 0


if __name__ == "__main__":
    sys.exit(main())
