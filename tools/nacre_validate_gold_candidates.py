#!/usr/bin/env python3
"""Validate the structure of NACRE gold-set candidates without approving them."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "runtime" / "nacre" / "gold_candidates_v0.jsonl"
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
REQUIRED = {"id", "category", "task", "allowed_tools", "expected_outcome", "forbidden_actions"}


def validate(source: Path) -> dict:
    errors: list[str] = []
    rows: list[dict] = []
    if not source.exists():
        errors.append("source_missing")
    else:
        for line_no, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"line_{line_no}:invalid_json")
                continue
            rows.append(row)
            missing = sorted(REQUIRED - set(row)) if isinstance(row, dict) else sorted(REQUIRED)
            if missing:
                errors.append(f"line_{line_no}:missing:{','.join(missing)}")
                continue
            if not isinstance(row["allowed_tools"], list) or not set(row["allowed_tools"]).issubset(ALLOWED_TOOLS):
                errors.append(f"line_{line_no}:tool_not_allowlisted")
            if not isinstance(row["forbidden_actions"], list) or not row["forbidden_actions"]:
                errors.append(f"line_{line_no}:forbidden_actions_missing")
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != len(set(ids)):
        errors.append("duplicate_ids")
    return {
        "schema": "nacre-gold-candidate-validation-v0",
        "source": str(source),
        "ok": not errors,
        "candidate_count": len(rows),
        "errors": errors,
        "approved_for_training": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = validate(args.source)
    rendered = json.dumps(report, ensure_ascii=False, indent=2)
    print(rendered)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
