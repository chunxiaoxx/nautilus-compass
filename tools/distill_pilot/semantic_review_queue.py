#!/usr/bin/env python3
"""Build a source-bound semantic-review queue for local 9B candidates.

This is deliberately a queue builder, not an approver.  It binds each
candidate's source, summary and anchor hashes and leaves promotion on hold
until an independent reviewer writes the exact ``distill-source-review/1``
receipt consumed by ``publish_to_memory.py``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from incremental_distill import MEMORY_DIR, load_state, sha256, version_paths


def build_queue(runtime: Path, memory_dir: Path) -> dict:
    state = load_state(runtime, memory_dir)
    rows: list[dict] = []
    counts = {"review_required": 0, "ready_for_independent_review": 0,
              "missing_artifact": 0, "source_reviewed_scoped": 0}
    for session_id, record in sorted(state.get("sessions", {}).items()):
        semantic_status = record.get("semantic_status", "")
        if semantic_status == "source_reviewed_scoped":
            counts["source_reviewed_scoped"] += 1
            continue
        source_sha = record.get("source_sha256")
        if not source_sha:
            continue
        paths = version_paths(runtime, session_id, source_sha)
        missing = [name for name, path in paths.items() if not path.is_file()]
        if missing:
            counts["missing_artifact"] += 1
            rows.append({"session_id": session_id, "action": "missing_artifact",
                         "source_sha256": source_sha, "missing": missing})
            continue
        artifact_sha256 = {name: sha256(path.read_bytes()) for name, path in paths.items()}
        review_file = runtime / "semantic_reviews" / f"{session_id}.json"
        if review_file.is_file():
            action = "ready_for_independent_review"
            counts["ready_for_independent_review"] += 1
        else:
            action = "review_required"
            counts["review_required"] += 1
        rows.append({
            "session_id": session_id,
            "action": action,
            "source_path": str(paths["source"].resolve()),
            "summary_path": str(paths["narrative"].resolve()),
            "anchors_path": str(paths["anchors"].resolve()),
            "source_sha256": source_sha,
            "artifact_sha256": artifact_sha256,
            "j1": record.get("j1"),
            "review_receipt": str(review_file.resolve()) if review_file.is_file() else None,
            "promotion": "hold",
        })
    return {
        "schema": "distill-semantic-review-queue/1",
        "runtime": str(runtime.resolve()),
        "memory_dir": str(memory_dir.resolve()),
        "policy": "Queue and hash-bind candidates; never approve or publish.",
        "counts": counts,
        "items": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime", type=Path,
                        default=Path("runtime/scratch_distill_pilot_20261104"))
    parser.add_argument("--memory-dir", type=Path, default=MEMORY_DIR)
    parser.add_argument("--out", type=Path,
                        default=Path("runtime/scratch_distill_pilot_20261104/semantic-review-queue-latest.json"))
    args = parser.parse_args(argv)
    document = build_queue(args.runtime, args.memory_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"out": str(args.out), "counts": document["counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
