#!/usr/bin/env python3
"""Publish version-bound distillation documents and return verifiable receipts."""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

MEMORY_DIR = Path.home() / ".claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass/memory"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def preserve_previous(path: Path, history_dir: Path) -> None:
    if not path.exists():
        return
    data = path.read_bytes()
    history_dir.mkdir(parents=True, exist_ok=True)
    archive = history_dir / (sha256(data) + path.suffix)
    try:
        with archive.open("xb") as handle:
            handle.write(data)
    except FileExistsError:
        if archive.read_bytes() != data:
            raise ValueError("History archive content does not match its digest")


def one_line(narrative: str) -> str:
    for line in narrative.splitlines():
        text = line.strip().lstrip("#-• *").strip()
        if len(text) >= 12 and not text.startswith(("源:", "生成:")):
            return text[:60]
    return "会话蒸馏纪要"


def validate_review(review_file: Path, session_id: str, source_sha256: str | None,
                    narrative_bytes: bytes, anchors_bytes: bytes) -> tuple[dict, str]:
    """Validate review custody, not natural-language truth or reviewer independence."""
    raw = review_file.read_bytes()
    review = json.loads(raw)
    expected = {
        "schema": "distill-source-review/1", "decision": "approved",
        "session_id": session_id, "source_sha256": source_sha256,
        "summary_sha256": sha256(narrative_bytes), "anchors_sha256": sha256(anchors_bytes),
    }
    if not source_sha256 or any(review.get(k) != v for k, v in expected.items()):
        raise ValueError("Semantic review does not approve this exact source and candidate")
    if not review.get("reviewer") or not review.get("reviewed_at_utc"):
        raise ValueError("Semantic review must identify reviewer and review time")
    if sha256(Path(review["source_path"]).read_bytes()) != source_sha256:
        raise ValueError("Reviewed source changed after review")
    evidence = review.get("evidence", [])
    by_id = {item["id"]: item for item in evidence}
    if not evidence or len(by_id) != len(evidence):
        raise ValueError("Review requires distinct source evidence")
    for item in evidence:
        data = Path(item["path"]).read_bytes()
        if sha256(data) != item["sha256"]:
            raise ValueError("Review evidence changed")
        lines = data.decode("utf-8").splitlines(keepends=True)
        start, end = item["line_start"], item["line_end"]
        if not (isinstance(start, int) and isinstance(end, int) and 1 <= start <= end <= len(lines)):
            raise ValueError("Review evidence has invalid line bounds")
        if sha256("".join(lines[start-1:end]).encode()) != item["excerpt_sha256"]:
            raise ValueError("Review excerpt does not match its source")
    sections = review.get("checks", [])
    required = {"latest_decision", "error_attribution", "completion_evidence"}
    if len(sections) != 3 or {x["id"] for x in sections} != required:
        raise ValueError("Review must cover decision order, error attribution and completion evidence")
    for item in sections:
        if item.get("status") not in ("supported", "not_applicable") or not item.get("rationale"):
            raise ValueError("Review contains an unresolved semantic check")
        refs = item.get("evidence_ids", [])
        if (item["status"] == "supported" and not refs) or any(ref not in by_id for ref in refs):
            raise ValueError("Review check lacks bound evidence")
    return review, sha256(raw)


def publish_document(md: Path, anchors: Path, memory_dir: Path,
                     source_sha256: str | None = None,
                     review_file: Path | None = None) -> dict:
    narrative_bytes = md.read_bytes()
    anchors_bytes = anchors.read_bytes()
    narrative = narrative_bytes.decode("utf-8").strip()
    if not narrative:
        raise ValueError("Cannot publish an empty narrative")
    anchor_lines = [line for line in anchors_bytes.decode("utf-8").splitlines() if line.strip()]
    session_id = md.stem
    review, review_sha = (validate_review(review_file, session_id, source_sha256,
                                          narrative_bytes, anchors_bytes)
                          if review_file is not None else (None, None))
    name = "distill-" + session_id
    description = f"蒸馏纪要 {session_id[:8]} {one_line(narrative)}"
    body = (
        "---\n"
        f"name: {json.dumps(name, ensure_ascii=False)}\n"
        f"description: {json.dumps(description, ensure_ascii=False)}\n"
        "metadata:\n"
        "  node_type: memory\n  type: project\n  tier: episodic\n"
        "  decay_rate: 0.7\n  origin: distill-pilot\n"
        f"  session_id: {json.dumps(session_id)}\n"
        f"  source_sha256: {json.dumps(source_sha256)}\n"
        f"  summary_sha256: {json.dumps(sha256(narrative_bytes))}\n"
        f"  anchors_sha256: {json.dumps(sha256(anchors_bytes))}\n"
        f"  semantic_status: {json.dumps('source_reviewed_scoped' if review else 'unreviewed_j1_only')}\n"
        f"  semantic_review_sha256: {json.dumps(review_sha)}\n"
        "---\n\n"
        f"{narrative}\n\n## 锚点索引({len(anchor_lines)} 条·源文直提)\n"
        + "\n".join(f"- {line}" for line in anchor_lines)
        + f"\n\n(生产形态正本: {md.resolve()})\n"
    ).encode("utf-8")
    memory_dir.mkdir(parents=True, exist_ok=True)
    with (memory_dir / ".distill-publish.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        destination = memory_dir / (name + ".md")
        # Earlier releases used eight-character IDs and a date. Reuse a card
        # only when its footer binds it to this complete session ID.
        legacy = []
        for candidate in memory_dir.glob("distill-*.md"):
            if candidate == destination or not candidate.name.startswith("distill-" + session_id[:8] + "-"):
                continue
            candidate_lines = candidate.read_text(encoding="utf-8").rstrip().splitlines()
            footer = candidate_lines[-1] if candidate_lines else ""
            if footer.startswith("(生产形态正本: ") and footer.endswith(f"/{session_id}.md)"):
                legacy.append(candidate)
        if len(legacy) > 1 or (destination.exists() and legacy):
            raise ValueError("Multiple memory cards claim the same complete session ID")
        if legacy:
            destination = legacy[0]
        changed = not destination.exists() or destination.read_bytes() != body
        previous = destination.read_bytes() if destination.exists() else None
        # All existing cards are protected, including legacy source-reviewed
        # cards that predate semantic metadata. J1 is never an overwrite grant.
        if changed and previous is not None and review is None:
            return {
                "status": "review_required", "changed": False,
                "reason": "existing_memory_requires_revision_review",
                "session_id": session_id, "source_sha256": source_sha256,
                "summary_sha256": sha256(narrative_bytes), "anchors_sha256": sha256(anchors_bytes),
                "existing": {"path": str(destination.resolve()), "sha256": sha256(previous),
                             "bytes": len(previous)},
            }
        if changed and review is not None:
            expected_previous = review.get("previous_memory_sha256")
            actual_previous = sha256(previous) if previous is not None else None
            if "previous_memory_sha256" not in review or expected_previous != actual_previous:
                raise ValueError("Reviewed destination changed; a stale review cannot replace it")
        if changed:
            preserve_previous(destination, md.parent / ".published_history" / session_id)
            atomic_write(destination, body)
        actual = destination.read_bytes()
        if actual != body:
            raise RuntimeError("Published memory readback differs from requested document")
        return {
            "status": "published", "changed": changed, "session_id": session_id,
            "source_sha256": source_sha256, "summary_sha256": sha256(narrative_bytes),
            "anchors_sha256": sha256(anchors_bytes), "path": str(destination.resolve()),
            "sha256": sha256(actual), "bytes": len(actual),
            "semantic_status": "source_reviewed_scoped" if review else "unreviewed_j1_only",
            "semantic_review_sha256": review_sha,
        }


def publish_one(md: Path, anchors: Path) -> bool:
    """Keep the original callable's changed/unchanged return contract."""
    return publish_document(md, anchors, MEMORY_DIR)["changed"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prod-dir", type=Path,
                        default=Path("runtime/scratch_distill_pilot_20261104/summaries_9b_prod"))
    parser.add_argument("--only", default="")
    parser.add_argument("--memory-dir", type=Path, default=MEMORY_DIR)
    parser.add_argument("--source-sha256")
    parser.add_argument("--review-file", type=Path,
                        help="Exact source/candidate/destination-bound semantic review receipt")
    args = parser.parse_args(argv)
    if args.source_sha256 and (len(args.source_sha256) != 64 or
                              any(c not in "0123456789abcdef" for c in args.source_sha256)):
        parser.error("--source-sha256 must be a SHA-256 hex digest")
    requested = {name for name in args.only.split(",") if name}
    sources = {md.stem: md for md in args.prod_dir.glob("*.md")}
    missing = sorted(requested - sources.keys())
    errors = [{"session_id": sid, "error": "requested_summary_missing"} for sid in missing]
    publications = []
    for sid in sorted(requested & sources.keys() if requested else sources.keys()):
        try:
            publications.append(publish_document(
                sources[sid], args.prod_dir / (sid + ".anchors.txt"),
                args.memory_dir, args.source_sha256, args.review_file))
        except (OSError, ValueError, RuntimeError, UnicodeError, KeyError, TypeError) as error:
            errors.append({"session_id": sid, "error": type(error).__name__, "detail": str(error)})
    print(json.dumps({"publications": publications, "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
