#!/usr/bin/env python3
"""外部勘误子集吸收器(A 案执行 · 承 #2667 裁决/#2678 交付)。

v5 交付 schema → 我方 P3 样本 schema 映射;truth_label 用显式映射表(可审计,
不用语义猜测);全部投 delta/inbox 交 p3_delta.py——白名单门自动拒
self_recompute(=对账件归档留痕),independent_recompute 过门入燃料计数。
用法:python tools/absorb_external_delta.py <raw.jsonl>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "runtime" / "verdict_corpus" / "raw"
INBOX = ROOT / "runtime" / "verdict_corpus" / "delta" / "inbox"

# case_id → truth_label(对原 claim 的复算终判;全 10 条显式列出,未列=拒收)
TRUTH = {
    "E1": "pass",                    # 复算 amended pass
    "E2": "pass",                    # 确定性三层互证成立
    "E3": "fail",                    # 干预无效应=原落账读数被证伪
    "E4": "fail",                    # 逐帧复现注不成立
    "S1": "insufficient_evidence",   # 活性在但计量盲区
    "S2": "fail",                    # M1 归因叙事(v5 发起非对方主动)证伪
    "S3": "fail",                    # 空转指控不成立(966 settled)
    "S4": "fail",                    # 闲置指控不成立(在途接单)
    "S5": "insufficient_evidence",   # 运行健康≠产出健康,产出存疑 U 态
    "S6": "fail",                    # 18890 行数声明证伪(端口号)
}


def content_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:16]


def main() -> int:
    src = Path(sys.argv[1])
    out_rows = []
    for line in src.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        cid = r["case_id"]
        if cid not in TRUTH:
            print(f"[reject] {cid} 无映射——拒收")
            continue
        s = {
            "id": f"errata_{cid}_{r['qid']}"[:80],
            "exported_at": r["filed_at"],
            "source": f"v5 A案交付(#2678) raw={r['source']} coords={r['coords']}",
            "criteria_ref": f"errata 复算判定(原判定见 original_verdict)",
            "artifact": {
                "qid": r["qid"],
                "artifact_ref": r["artifact_ref"],
                "original_verdict": r["original_verdict"],
                "domain": r["domain"],
                "fuel_eligible": r["fuel_eligible"],
            },
            "judge_output": {
                "recompute_verdict": r["recompute_verdict"],
                "judge_reason": r["judge_reason"],
            },
            "truth_label": TRUTH[cid],
            "label_origin": r["label_origin"],
            "reason": f"复算终判 {TRUTH[cid]};v5 标 fuel_eligible={r['fuel_eligible']}",
        }
        s["content_hash"] = content_hash([s["criteria_ref"], s["artifact"], s["judge_output"]])
        out_rows.append(s)
    INBOX.mkdir(parents=True, exist_ok=True)
    out = INBOX / f"{src.stem}.samples.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in out_rows) + "\n",
                   encoding="utf-8")
    dist = {}
    for r in out_rows:
        dist[r["label_origin"]] = dist.get(r["label_origin"], 0) + 1
    print(f"[ok] {out} rows={len(out_rows)} label_origin={dist}")
    print("[next] python tools/p3_delta.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
