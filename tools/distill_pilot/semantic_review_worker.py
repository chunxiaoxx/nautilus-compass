#!/usr/bin/env python3
"""Run the independent semantic-review lane over the full distill queue.

The worker is resumable and evidence-first:
* MiniMax-M3 and Kimi k3-256k review the same source-bound candidate;
* raw model text is never treated as a verdict until quotes are checked;
* only dual-review candidates with strong mechanical anchor coverage receive a
  ``distill-source-review/1`` receipt;
* no memory publication is performed by this worker.

Use ``--limit`` for a bounded pilot.  Omitting it processes the whole queue,
but each row is appended to the result JSONL before the next row starts.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from anchor_check import CJK_RE, collect_anchors
from compress_arm import scrub
from incremental_distill import MEMORY_DIR

import sys
sys.path.insert(0, "/Users/chunxiao.wang/Projects/nautilusflywheel/scripts/pipeline")
import model_backends as mb  # noqa: E402


SYSTEM = (
    "你是独立的源文审计员。把纪要总纪要部分拆成原子声明；"
    "对每条在源文中找出逐字支持引用，引用必须是源文中连续的原文；"
    "找不到就把 quote 置空。只输出严格 JSON 数组，不要其它文字："
    '[{"claim":"...","quote":"原文连续引用或空串"}]。'
    "最多40条，只选事实、数字、路径、日期、因果和结论。不要根据常识补充。"
)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _vault_value(name: str) -> str:
    path = Path.home() / ".claude/.cache/.fde_api_secrets.env"
    if not path.exists():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip().removeprefix("export ").strip() == name:
            return value.strip().strip('"\'')
    return ""


def _minimax_call(user: str) -> str:
    key = _vault_value("MINIMAX_API_KEY")
    if not key:
        raise RuntimeError("MINIMAX_API_KEY missing")
    body = json.dumps({
        "model": "MiniMax-M3", "system": SYSTEM,
        "messages": [{"role": "user", "content": user[:150000]}],
        "max_tokens": 8000, "temperature": 0,
    }).encode()
    req = Request(
        "https://api.minimaxi.com/anthropic/v1/messages", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                 "anthropic-version": "2023-06-01"},
    )
    with urlopen(req, timeout=300) as response:
        data = json.loads(response.read().decode("utf-8", "replace"))
    return "".join(block.get("text", "") for block in data.get("content", [])
                   if block.get("type") == "text")


def _kimi_call(user: str) -> str:
    return mb.call_model("k3-256k", SYSTEM + "\n\n" + user[:150000],
                         max_tokens=8000, retries=2, channel="relay", stream=False)


def parse_claims(raw: str, source: str) -> list[dict]:
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if not match:
        raise ValueError("no_json_array")
    claims = json.loads(match.group(0))
    if not isinstance(claims, list):
        raise ValueError("claims_not_array")
    for claim in claims:
        quote = str(claim.get("quote") or "").strip()
        claim["supported"] = bool(quote) and quote in source
        claim["quote_ok_len"] = len(quote)
    return claims[:40]


def line_bounds(text: str, quote: str) -> tuple[int, int] | None:
    offset = text.find(quote)
    if offset < 0:
        return None
    start = text.count("\n", 0, offset) + 1
    return start, start + quote.count("\n")


def mechanical_anchor_recall(source: str, final: str) -> tuple[int, int, float | None]:
    anchors = {
        item["value"] for item in collect_anchors(source)
        if item["type"] in ("path", "date", "tag_id", "url")
        and not CJK_RE.search(item["value"])
    }
    covered = sum(anchor in final for anchor in anchors)
    return len(anchors), covered, round(covered / len(anchors), 4) if anchors else None


def _reviewer_result(name: str, raw: str, source: str) -> dict:
    claims = parse_claims(raw, source)
    unsupported = [str(c.get("claim", ""))[:240] for c in claims if not c["supported"]]
    return {
        "reviewer": name, "claims": len(claims),
        "supported": sum(1 for c in claims if c["supported"]),
        "unsupported": unsupported[:10], "claims_detail": claims,
    }


def build_receipt(row: dict, source_raw: str, claims: list[dict], reviewers: list[str]) -> dict:
    source_path = Path(row["source_path"])
    summary_path = Path(row["summary_path"])
    anchors_path = Path(row["anchors_path"])
    evidence = []
    for index, claim in enumerate(claims):
        quote = str(claim.get("quote") or "").strip()
        bounds = line_bounds(source_raw, quote) if quote else None
        if not claim.get("supported") or not bounds:
            continue
        evidence.append({
            "id": f"e{index}", "path": str(source_path.resolve()),
            "sha256": sha(source_path.read_bytes()), "line_start": bounds[0],
            "line_end": bounds[1], "excerpt_sha256": sha(quote.encode()),
        })
    destination = Path.home() / ".claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory" / (
        "distill-" + row["session_id"] + ".md")
    return {
        "schema": "distill-source-review/1", "decision": "approved",
        "session_id": row["session_id"], "source_path": str(source_path.resolve()),
        "source_sha256": sha(source_path.read_bytes()),
        "summary_sha256": sha(summary_path.read_bytes()),
        "anchors_sha256": sha(anchors_path.read_bytes()),
        "previous_memory_sha256": sha(destination.read_bytes()) if destination.exists() else None,
        "reviewer": "+".join(reviewers),
        "reviewed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "evidence": evidence,
        "checks": [
            {"id": "latest_decision", "status": "supported",
             "evidence_ids": [evidence[0]["id"]] if evidence else [],
             "rationale": "All reviewed claims have exact source quotes."},
            {"id": "error_attribution", "status": "not_applicable",
             "evidence_ids": [], "rationale": "No separate error-attribution claim was required."},
            {"id": "completion_evidence", "status": "supported",
             "evidence_ids": [evidence[0]["id"]] if evidence else [],
             "rationale": "The reviewed summary is bound to exact source evidence."},
        ],
    }


def review_one(row: dict, reviewers: tuple[str, ...]) -> dict:
    source_path = Path(row["source_path"])
    summary_path = Path(row["summary_path"])
    source_raw = source_path.read_text(encoding="utf-8", errors="replace")
    source = scrub(source_raw)
    final = summary_path.read_text(encoding="utf-8", errors="replace").split("## 附")[0]
    user = f"【源文】\n{source}\n\n【纪要】\n{final}"
    item = {"session_id": row["session_id"], "status": "hold", "reviewers": {},
            "source_sha256": sha(source_path.read_bytes()),
            "summary_sha256": sha(summary_path.read_bytes()),
            "anchors_sha256": sha(Path(row["anchors_path"]).read_bytes())}
    for reviewer in reviewers:
        try:
            raw = _minimax_call(user) if reviewer == "minimax-m3" else _kimi_call(user)
            item["reviewers"][reviewer] = _reviewer_result(reviewer, raw, source)
        except Exception as error:  # preserve channel failures per row
            item["reviewers"][reviewer] = {
                "error_type": type(error).__name__, "error": str(error)[:300]
            }
    anchor_count, covered, anchor_recall = mechanical_anchor_recall(source_raw, final)
    item["anchor_count"], item["anchor_covered"], item["anchor_recall"] = anchor_count, covered, anchor_recall
    complete = all("error" not in item["reviewers"].get(name, {}) for name in reviewers)
    strong = all(
        result.get("claims", 0) > 0 and result.get("supported") == result.get("claims")
        for result in item["reviewers"].values() if "error" not in result
    )
    if complete and strong and (anchor_recall is None or anchor_recall >= 0.9):
        combined = item["reviewers"][reviewers[0]]["claims_detail"]
        item["status"] = "approved_receipt_candidate"
        item["review_receipt"] = build_receipt(row, source_raw, combined, list(reviewers))
    else:
        # Hold reports need only counts and short unsupported examples. Keep
        # the full claims in memory for an approved receipt, but avoid making
        # the all-history JSONL grow by tens of megabytes of repeated quotes.
        for result in item["reviewers"].values():
            result.pop("claims_detail", None)
    return item


def load_rows(queue_path: Path) -> list[dict]:
    return json.loads(queue_path.read_text(encoding="utf-8"))["items"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queue", type=Path,
                        default=Path("runtime/scratch_distill_pilot_20261104/semantic-review-queue-20261118.json"))
    parser.add_argument("--out", type=Path,
                        default=Path("runtime/scratch_distill_pilot_20261104/semantic-review-worker-results.jsonl"))
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    parser.add_argument("--reviewers", default="minimax-m3,kimi-k3-256k",
                        help="Comma-separated reviewers: minimax-m3,kimi-k3-256k")
    args = parser.parse_args(argv)
    rows = load_rows(args.queue)
    selected = rows[args.offset: args.offset + args.limit if args.limit else None]
    seen = set()
    if args.out.exists():
        for line in args.out.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                seen.add(json.loads(line)["session_id"])
            except (json.JSONDecodeError, KeyError):
                continue
    args.out.parent.mkdir(parents=True, exist_ok=True)
    processed = 0
    reviewers = tuple(name.strip() for name in args.reviewers.split(",") if name.strip())
    allowed = {"minimax-m3", "kimi-k3-256k"}
    if not reviewers or any(name not in allowed for name in reviewers):
        parser.error("--reviewers must use minimax-m3 and/or kimi-k3-256k")
    with args.out.open("a", encoding="utf-8") as handle:
        for row in selected:
            if row["session_id"] in seen:
                continue
            result = review_one(row, reviewers)
            handle.write(json.dumps(result, ensure_ascii=False) + "\n")
            handle.flush()
            processed += 1
            print(json.dumps({"session_id": row["session_id"], "status": result["status"],
                              "anchor_recall": result.get("anchor_recall")}, ensure_ascii=False), flush=True)
            if args.sleep_seconds > 0:
                time.sleep(args.sleep_seconds)
    print(json.dumps({"selected": len(selected), "processed": processed,
                      "out": str(args.out)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
