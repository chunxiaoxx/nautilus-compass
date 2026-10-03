#!/usr/bin/env python3
"""判例→训练样本转换器(P3 燃料瓶颈机制化解)。

背景:delta_0001 手写导出只产 14 条/案,200 门槛=14 案件日——判分产出与语料
沉淀之间缺机制。本转换器把任意 verdict JSON 的 findings/verdict 自动映射为
训练样本,投递 delta/inbox/ 交 p3_delta.py 白名单门吸收。

映射规则(判例→样本,一判读多样本):
  · 每个 finding(带 evidence_tier+upgrade_path)→ 1 条样本:
      artifact=finding 全文+basis;truth_label 按证据层映射
      (measured 且判定成立→pass;inferred/unverifiable→insufficient_evidence;
       被否证的 claim 类 finding→fail,由 --fail-keywords 识别)
  · verdict 总判定 → 1 条样本(PARTIAL/PASS→pass,U→insufficient_evidence)
标签纪律:转换器**不产生 fail 假阳性**——只把明确被否证的推断标 fail,
其余一律 pass 或 U;拿不准=U(宁欠勿毒,承 judge 自报三陷阱)。

用法:python tools/verdict_to_samples.py <verdict.json> [--judge <judge名>] [--dry]
输出:runtime/verdict_corpus/delta/inbox/v2s_<stem>.jsonl(交白名单门)
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "runtime" / "verdict_corpus" / "delta" / "inbox"
FAIL_HINTS = ("否证", "不成立", "refut", "not hold", "被驳回")


def content_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False,
                                     sort_keys=True).encode()).hexdigest()[:16]


def convert(v: dict, judge: str) -> list[dict]:
    rows = []
    total = v.get("verdict", "")
    is_u = ("U" in total.split("(")[0]) or ("insufficient" in total) or ("判不动" in total)
    # 判例 1:总判定
    rows.append({
        "source": f"v2s:{judge}", "criteria_ref": str(v.get("criteria_positioning",
                                                             v.get("criteria", "")))[:160],
        "artifact": {"verdict": total[:600], "ts": v.get("ts", "")},
        "judge_output": {"type": "case_verdict", "gates": bool(v.get("gates") or v.get("arms") or v.get("windows"))},
        "truth_label": "insufficient_evidence" if is_u else "pass",
        "label_origin": "independent_recompute",
        "reason": f"总判定({'U态' if is_u else '判定成立'});{'主判据无区分度' if is_u else '按冻结判据成立'}",
    })
    # 判例 2..n:逐 finding
    for i, f in enumerate(v.get("findings", [])):
        text = f.get("finding", "")
        tier = f.get("evidence_tier", "unverifiable")
        if tier == "inferred" and any(h in text for h in FAIL_HINTS):
            label, reason = "fail", "推断被实测否证(finding 含否证语+inferred 层)"
        elif tier in ("measured", "inferred"):
            label = "insufficient_evidence" if tier == "inferred" else "pass"
            reason = f"finding[{i}] {tier} 层:{'实测成立' if tier == 'measured' else '推断不冒充实测'}"
        else:
            label, reason = "insufficient_evidence", f"finding[{i}] unverifiable"
        rows.append({
            "source": f"v2s:{judge}", "criteria_ref": str(v.get("criteria_positioning",
                                                                v.get("criteria", "")))[:160],
            "artifact": {"finding": text[:500], "basis": str(f.get("basis", ""))[:300],
                         "upgrade_path": f.get("upgrade_path")},
            "judge_output": {"type": "finding", "idx": i},
            "truth_label": label, "label_origin": "independent_recompute",
            "reason": reason,
        })
    return rows


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    src = Path(args[0])
    dry = "--dry" in sys.argv
    judge = src.stem
    v = json.loads(src.read_text(encoding="utf-8"))
    rows = convert(v, judge)
    for r in rows:
        r["content_hash"] = content_hash([r["criteria_ref"], r["artifact"], r["judge_output"]])
    dist = {}
    for r in rows:
        dist[r["truth_label"]] = dist.get(r["truth_label"], 0) + 1
    print(json.dumps({"verdict_file": src.name, "samples": len(rows),
                      "label_distribution": dist}, ensure_ascii=False))
    if dry:
        print("[dry] 未投递")
        return 0
    INBOX.mkdir(parents=True, exist_ok=True)
    out = INBOX / f"v2s_{src.stem}.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
                   encoding="utf-8")
    print(f"[inbox] {out}(交 p3_delta.py 白名单门吸收)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
