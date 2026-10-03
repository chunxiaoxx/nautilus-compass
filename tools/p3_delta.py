#!/usr/bin/env python3
"""P3 S1 · 增量收集器(白名单门+指纹对账)。

设计档:docs/plans/P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003.md §二。
职责:扫 runtime/verdict_corpus/delta/inbox/*.jsonl(原料投递区,任何导出器/案件
把带标签样本投这里)→ 按 content_hash 对已接受指纹账去重 → label_origin 白名单
过滤 → 新样本写 delta/delta_NNNN.jsonl + manifest → 已吸收 inbox 移 absorbed/。

白名单(反自指护栏 3:判官自产标签永久禁入):
  independent_recompute / human_review / official_rule / three_vendor_final

首跑(无指纹账)=初始化基线:P2v2 冻结三折(split_train/dev/test)content_hash
+既有 delta_0001 样本,全部记为已接受,不出批(基线不是增量)。
幂等:同输入重跑零新增。用法:python tools/p3_delta.py
"""
from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "runtime" / "verdict_corpus"
DELTA = CORPUS / "delta"
INBOX = DELTA / "inbox"
ABSORBED = DELTA / "absorbed"
FINGERPRINTS = DELTA / "accepted_hashes.json"

WHITELIST = {"independent_recompute", "human_review", "official_rule",
             "three_vendor_final"}


def load_fingerprints() -> set:
    if FINGERPRINTS.exists():
        return set(json.loads(FINGERPRINTS.read_text(encoding="utf-8")))
    fps = set()
    for name in ("split_train.jsonl", "split_dev.jsonl", "split_test.jsonl"):
        for line in (CORPUS / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                fps.add(json.loads(line).get("content_hash"))
    for line in (DELTA / "delta_0001.jsonl").read_text(encoding="utf-8").splitlines():
        if line.strip():
            fps.add(json.loads(line).get("content_hash"))
    FINGERPRINTS.write_text(json.dumps(sorted(x for x in fps if x)), encoding="utf-8")
    print(f"[init] 基线指纹 {len(fps)} 条(三折 1454+delta_0001 14,判官自产标签本就不在其中)")
    return fps


def next_cycle() -> int:
    existing = sorted(DELTA.glob("delta_*.jsonl"))
    return len(existing) + 1


def main() -> int:
    INBOX.mkdir(parents=True, exist_ok=True)
    ABSORBED.mkdir(parents=True, exist_ok=True)
    fps = load_fingerprints()
    fresh, rejected, seen_files = [], 0, []
    for f in sorted(INBOX.glob("*.jsonl")):
        seen_files.append(f.name)
        for line in f.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            h = row.get("content_hash")
            if not h or h in fps:
                continue
            if row.get("label_origin") not in WHITELIST:
                rejected += 1
                fps.add(h)  # 拒绝件也记指纹,防反复投递反复计数
                continue
            fresh.append(row)
            fps.add(h)
    if not fresh:
        out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"), "cycle": next_cycle() - 1,
               "verdict": "SKIP", "new": 0, "rejected": rejected,
               "inbox_files": seen_files}
        print(json.dumps(out, ensure_ascii=False))
        FINGERPRINTS.write_text(json.dumps(sorted(fps)), encoding="utf-8")
        return 0
    n = next_cycle()
    out_f = DELTA / f"delta_{n:04d}.jsonl"
    out_f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in fresh) + "\n",
                     encoding="utf-8")
    dist = {}
    for r in fresh:
        dist[r["truth_label"]] = dist.get(r["truth_label"], 0) + 1
    manifest = {"delta_id": f"delta_{n:04d}", "exported_at": time.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
                "n_new": len(fresh), "label_distribution": dist, "whitelist_rejected": rejected,
                "inbox_files": seen_files}
    (DELTA / f"manifest_delta_{n:04d}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    for f in INBOX.glob("*.jsonl"):
        shutil.move(str(f), str(ABSORBED / f.name))
    FINGERPRINTS.write_text(json.dumps(sorted(fps)), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    print(f"[save] {out_f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
