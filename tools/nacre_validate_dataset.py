#!/usr/bin/env python3
"""Validate a NACRE preview dataset before it can become training input.

This is a deterministic gate. It does not call a model and it does not alter
the dataset. A green result means the file is structurally usable, not that the
examples are semantically gold-labelled.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET = ROOT / "runtime" / "nacre" / "dataset_preview.jsonl"
DEFAULT_MANIFEST = ROOT / "runtime" / "nacre" / "dataset_manifest.json"
ALLOWED_TOOLS = {
    "local_health",
    "compass_daemon_probe",
    "compass_recall",
    "evidence_gate",
    "memory_search",
    "github_mentions",
    "gmail_inbox_probe",
    "platform_mail_read",
    "org_continuity_read",
    "write_draft",
}
SECRET_PATTERN = re.compile(r"(?i)(bearer\s+[A-Za-z0-9._-]+|api[_-]?key\s*[:=]|password\s*[:=]|secret\s*[:=])")


def validate(dataset_path: Path, manifest_path: Path) -> dict:
    errors: list[str] = []
    records: list[dict] = []
    raw_lines = dataset_path.read_text(encoding="utf-8").splitlines() if dataset_path.exists() else []
    for line_no, line in enumerate(raw_lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid_json:{exc.msg}")
            continue
        if not isinstance(record, dict):
            errors.append(f"line {line_no}: record_not_object")
            continue
        records.append(record)
        if record.get("schema") != "nacre-sft-v0":
            errors.append(f"line {line_no}: schema_invalid")
        if not record.get("id"):
            errors.append(f"line {line_no}: id_missing")
        if record.get("split") not in {"train", "validation", "test"}:
            errors.append(f"line {line_no}: split_invalid")
        if not str(record.get("task", "")).strip():
            errors.append(f"line {line_no}: task_missing")
        if not str(record.get("target", "")).strip():
            errors.append(f"line {line_no}: target_missing")
        safety = record.get("safety")
        if not isinstance(safety, dict) or safety.get("external_model_used") or safety.get("external_send"):
            errors.append(f"line {line_no}: external_boundary_present")
        for call in record.get("tool_trace") or []:
            if not isinstance(call, dict) or call.get("name") not in ALLOWED_TOOLS:
                errors.append(f"line {line_no}: tool_not_allowlisted")
        if SECRET_PATTERN.search(line):
            errors.append(f"line {line_no}: possible_secret_pattern")

    ids = [record.get("id") for record in records]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_ids")

    content = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    manifest = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append("manifest_invalid_json")
    else:
        errors.append("manifest_missing")
    if manifest:
        if manifest.get("record_count") != len(records):
            errors.append("manifest_record_count_mismatch")
        if manifest.get("sha256") != hashlib.sha256(content.encode("utf-8")).hexdigest():
            errors.append("manifest_sha256_mismatch")

    report = {
        "schema": "nacre-dataset-validation-v0",
        "dataset": str(dataset_path),
        "manifest": str(manifest_path),
        "ok": not errors,
        "record_count": len(records),
        "train_count": sum(record.get("split") == "train" for record in records),
        "validation_count": sum(record.get("split") == "validation" for record in records),
        "test_count": sum(record.get("split") == "test" for record in records),
        "errors": errors,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    report = validate(args.dataset, args.manifest)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
