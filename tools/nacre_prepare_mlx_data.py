#!/usr/bin/env python3
"""Convert NACRE preview records to MLX-LM chat JSONL files.

The converter keeps the model target as a structured JSON response. It does
not train, upload, or call a provider. The output is a disposable staging
directory until the gold-set gate passes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "runtime" / "nacre" / "dataset_preview.jsonl"
DEFAULT_OUT = ROOT / "runtime" / "nacre" / "mlx_data"

SYSTEM_PROMPT = (
    "你是 NACRE 本地 agent。只输出 JSON，格式为 "
    '{"tool_calls":[{"name":"白名单工具","arguments":{}}],"final":"中文结论或 null"}。'
    "工具调用必须服从白名单和证据门，禁止发送、部署、支付和任意 shell。"
)


def load_records(source: Path) -> list[dict]:
    records = []
    if not source.exists():
        return records
    for line in source.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            records.append(value)
    return records


def to_chat(record: dict) -> dict:
    tool_calls = []
    for call in record.get("tool_trace") or []:
        if isinstance(call, dict):
            tool_calls.append({
                "name": call.get("name"),
                "arguments": call.get("arguments") or {},
            })
    assistant = json.dumps(
        {"tool_calls": tool_calls, "final": record.get("target") or None},
        ensure_ascii=False,
    )
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": str(record.get("task", ""))},
            {"role": "assistant", "content": assistant},
        ],
    }


def prepare(source: Path, output: Path) -> dict:
    records = load_records(source)
    output.mkdir(parents=True, exist_ok=True)
    counts = {"train": 0, "validation": 0, "test": 0}
    files = {"train": "train.jsonl", "validation": "valid.jsonl", "test": "test.jsonl"}
    for split, filename in files.items():
        rows = [to_chat(record) for record in records if record.get("split") == split]
        (output / filename).write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
            encoding="utf-8",
        )
        counts[split] = len(rows)
    manifest = {
        "schema": "nacre-mlx-data-manifest-v0",
        "source": str(source),
        "output": str(output),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest() if source.exists() else None,
        "counts": counts,
        "format": "mlx-lm chat messages",
        "training_started": False,
        "notes": [
            "This is staging data only.",
            "A human-reviewed gold set and independent validation are required before training.",
        ],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.output), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
