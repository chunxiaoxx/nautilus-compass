#!/usr/bin/env python3
"""Build a leakage-checked NACRE training dataset from local agent receipts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "runtime" / "nacre" / "training_events.jsonl"
DEFAULT_OUT = ROOT / "runtime" / "nacre" / "dataset_preview.jsonl"
DEFAULT_MANIFEST = ROOT / "runtime" / "nacre" / "dataset_manifest.json"


def _draft_requested(task: str) -> bool:
    positive = re.search(r"(?:写|生成|保存|准备).{0,24}(?:草稿|draft)", task, flags=re.IGNORECASE)
    prohibited = re.search(r"不要.{0,4}(?:写|生成|保存).{0,20}(?:草稿|draft)", task, flags=re.IGNORECASE)
    return bool(positive and not prohibited)


def _successful_tool(event: dict, name: str) -> bool:
    for step in event.get("steps") or []:
        for item in step.get("results") or []:
            if isinstance(item, dict) and item.get("tool") == name:
                result = item.get("result")
                if isinstance(result, dict) and result.get("ok") is True:
                    return True
    return False


def contract_violation(event: dict) -> str | None:
    """Return a reason for an unsafe positive SFT example, if any."""
    if event.get("contract_violations"):
        return "runtime_contract_violation"
    final = str(event.get("final", ""))
    if not _successful_tool(event, "write_draft") and re.search(r"草稿.*(?:已保存|保存至|写入)", final):
        return "draft_claim_without_successful_write_draft"
    return None


def redact(value):
    if isinstance(value, str):
        value = re.sub(r"(?i)(bearer\s+)[^\s]+", r"\1<redacted>", value)
        value = re.sub(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*\S+", r"\1=<redacted>", value)
        return value
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def load_events(source: Path):
    if not source.exists():
        return []
    events = []
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(redact(value))
    return events


def stable_id(event: dict) -> str:
    raw = json.dumps(event, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def build_record(event: dict) -> dict:
    event_id = stable_id(event)
    steps = event.get("steps") or []
    tool_trace = []
    for step in steps:
        output = step.get("model_output") or {}
        if isinstance(output, dict):
            for call in output.get("tool_calls") or []:
                if isinstance(call, dict):
                    tool_trace.append({"name": call.get("name"), "arguments": call.get("arguments") or {}})
    bucket = int(event_id[:2], 16) % 100
    if bucket < 10:
        split = "validation"
    elif bucket < 20:
        split = "test"
    else:
        split = "train"
    return {
        "schema": "nacre-sft-v0",
        "id": event_id,
        "split": split,
        "task": event.get("task", ""),
        "tool_trace": tool_trace,
        "target": event.get("final", ""),
        "safety": {
            "external_model_used": bool(event.get("external_model_used")),
            "external_send": bool(event.get("external_send")),
        },
        "source": "local_agent_runtime",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()

    events = load_events(args.source)
    records = []
    excluded = []
    for event in events:
        if event.get("external_model_used") or event.get("external_send"):
            excluded.append({"reason": "external_boundary", "task": event.get("task", "")})
            continue
        violation = contract_violation(event)
        if violation:
            excluded.append({"reason": violation, "task": event.get("task", "")})
            continue
        records.append(build_record(event))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    args.out.write_text(content, encoding="utf-8")
    manifest = {
        "schema": "nacre-dataset-manifest-v0",
        "source": str(args.source),
        "output": str(args.out),
        "record_count": len(records),
        "train_count": sum(record["split"] == "train" for record in records),
        "validation_count": sum(record["split"] == "validation" for record in records),
        "test_count": sum(record["split"] == "test" for record in records),
        "excluded_count": len(excluded),
        "excluded_reasons": {
            reason: sum(item.get("reason") == reason for item in excluded)
            for reason in sorted({item.get("reason") for item in excluded})
        },
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "external_model_records": sum(bool(event.get("external_model_used")) for event in events),
        "external_send_records": sum(bool(event.get("external_send")) for event in events),
        "notes": [
            "Only local-agent events are eligible.",
            "No email body, credential, external send, or arbitrary shell trace is included.",
            "A larger training run requires an independently reviewed gold set.",
        ],
    }
    args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
