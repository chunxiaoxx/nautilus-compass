"""Offline source-reviewed candidates in the existing ORG-FUEL schema.

This writes a local candidate pool only. It never writes P3 inbox/splits, calls
models, or assigns training truth. Source-record support is not external truth.
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
from pathlib import Path
import re
import sys
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fuel_flywheel_vet import redact_pii
from compress_arm import scrub
from publish_to_memory import atomic_write


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def clean(text: str) -> str:
    text = scrub(redact_pii(text))
    return re.sub(r"/Users/[^/\s]+", "/Users/[local-user]", text)


def clean_tree(value):
    """Metadata is exported data too; apply the same policy to every string."""
    if isinstance(value, str):
        return clean(value)
    if isinstance(value, list):
        return [clean_tree(item) for item in value]
    if isinstance(value, dict):
        return {clean(str(key)): clean_tree(item) for key, item in value.items()}
    return value


def revision_hash(row: dict) -> str:
    return digest(json.dumps(row, ensure_ascii=False, sort_keys=True).encode())


def validate_case(case: dict) -> None:
    rights = case.get("rights", {})
    if rights.get("local_candidate_allowed") is not True:
        raise ValueError("local_candidate_rights_missing")
    if rights.get("training_allowed") is not False or rights.get("external_upload_allowed") is not False:
        raise ValueError("offline_candidate_scope_required")
    if case.get("fact_status") != "source_supported" or not case.get("reviewer"):
        raise ValueError("source_review_missing")
    if case.get("proposed_label") not in ("pass", "fail", "insufficient_evidence"):
        raise ValueError("invalid_proposed_label")
    if not case.get("case_id") or not case.get("session_id"):
        raise ValueError("candidate_identity_missing")
    if str(uuid.UUID(case["session_id"])) != case["session_id"]:
        raise ValueError("session_identity_not_canonical_uuid")
    if (not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,127}", case["case_id"])
            or clean(case["case_id"]) != case["case_id"]):
        raise ValueError("case_identity_invalid_or_sensitive")
    if not case.get("evidence") or not case.get("facts"):
        raise ValueError("fact_or_evidence_missing")
    if not any(e.get("sha256") == case.get("source_sha256") for e in case["evidence"]):
        raise ValueError("case_source_revision_unbound")
    compressed = case.get("compression_artifact", {})
    if digest(Path(compressed["path"]).read_bytes()) != compressed.get("sha256"):
        raise ValueError("compression_artifact_mismatch")
    ids = {e["id"] for e in case["evidence"]}
    if len(ids) != len(case["evidence"]):
        raise ValueError("duplicate_evidence_id")
    if any(not isinstance(key, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,127}", key)
           or clean(key) != key for key in ids):
        raise ValueError("evidence_identity_invalid_or_sensitive")
    for evidence in case["evidence"]:
        raw = Path(evidence["path"]).read_bytes()
        if digest(raw) != evidence["sha256"]:
            raise ValueError("source_revision_mismatch")
        lines = raw.decode("utf-8").splitlines(keepends=True)
        lo, hi = evidence["line_start"], evidence["line_end"]
        if not (1 <= lo <= hi <= len(lines)):
            raise ValueError("source_line_range_invalid")
        if digest("".join(lines[lo-1:hi]).encode()) != evidence["excerpt_sha256"]:
            raise ValueError("source_excerpt_mismatch")
    for fact in case["facts"]:
        if fact.get("fact_status") not in ("source_supported", "historical", "not_established"):
            raise ValueError("fact_status_invalid")
        if not fact.get("evidence_ids") or not set(fact["evidence_ids"]) <= ids:
            raise ValueError("fact_source_binding_missing")
    for key in ("situation", "content", "question", "response", "source_reference"):
        if not isinstance(case.get(key), str) or not case[key].strip():
            raise ValueError("empty_candidate_content")


def candidate(case: dict) -> dict:
    validate_case(case)
    safe = {k: clean(case[k]) for k in ("situation", "content", "question", "response", "source_reference")}
    h = digest(json.dumps(safe, ensure_ascii=False, sort_keys=True).encode())
    # Existing ORG-FUEL fields remain intact. Extra provenance has no implicit
    # conversion to NACRE labels. No raw transcript is copied into this row.
    row = clean_tree({
        "pf_id": "ORGM-" + h[:16], "source": "session:" + case["session_id"],
        "anchor_level": "L1", "domain": "org-memory", "situation": safe["situation"],
        "content_hash": h, "content": safe["content"],
        "candidate_key": digest((case["session_id"] + ":" + case["case_id"]).encode()),
        "case_id": case["case_id"],
        "fact_status": "source_supported", "candidate_status": "pending_independent_review",
        "source_revision": case["source_sha256"], "group_id": case["session_id"],
        "compression_artifact_sha256": case["compression_artifact"]["sha256"],
        "label_origin": "source_bound_candidate", "truth_label": None,
        "proposed_label": case["proposed_label"],
        "rights": case["rights"],
        "verification": {"reviewer": case["reviewer"], "evidence_sha256": [e["sha256"] for e in case["evidence"]],
                         "scope": "supports what source records say, not external execution success",
                         "facts": [{**f, "text": clean(f["text"])} for f in case["facts"]]},
        "artifact": {"domain": "artifact_judgment", "question": safe["question"],
                     "response": safe["response"],
                     "official_truth": "Source-record evidence only, not external runtime truth. " + safe["source_reference"]},
        "criteria_ref": "source-bound-memory-consistency/v1",
        "training_admission": {"allowed": False, "missing": ["independent_review_receipt", "approved_label_origin", "training_rights", "frozen_group_split_and_preregistered_training"]},
    })
    # Validated structured identifiers are not prose. Phone-like digit runs in
    # a real SHA must not corrupt its source binding during PII redaction.
    row.update(pf_id="ORGM-" + h[:16], source="session:" + case["session_id"],
               content_hash=h, candidate_key=digest((case["session_id"] + ":" + case["case_id"]).encode()),
               case_id=case["case_id"], source_revision=case["source_sha256"],
               group_id=case["session_id"], compression_artifact_sha256=case["compression_artifact"]["sha256"])
    row["verification"]["evidence_sha256"] = [e["sha256"] for e in case["evidence"]]
    # content_hash retains the existing ORG-FUEL contract. This separate hash
    # binds labels, rights, reviewers and evidence so corrections are retained.
    row["candidate_revision_sha256"] = revision_hash(row)
    return row


def export(manifest: Path, pool: Path) -> dict:
    root = Path(__file__).resolve().parents[2]
    forbidden = (root / "runtime/verdict_corpus", Path.home() / ".claude", Path.home() / ".codex/memories")
    if any(pool.resolve().is_relative_to(p.resolve()) for p in forbidden):
        raise ValueError("candidate_export_cannot_write_production_memory_or_training_corpus")
    document = json.loads(manifest.read_text())
    valid, rejected = [], []
    for case in document["cases"]:
        try:
            valid.append(candidate(case))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            rejected.append({"case_id": case.get("case_id"), "reason": str(exc)})
    pool.parent.mkdir(parents=True, exist_ok=True)
    with pool.with_suffix(pool.suffix + ".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            existing = [json.loads(line) for line in pool.read_text().splitlines() if line.strip()] if pool.exists() else []
        except json.JSONDecodeError as exc:
            raise ValueError("existing_candidate_pool_invalid_preserved_for_review") from exc
        seen = {r.get("candidate_revision_sha256") or revision_hash(r) for r in existing}
        latest = {r.get("candidate_key", r["content_hash"]): r.get("candidate_revision_sha256") or revision_hash(r) for r in existing}
        fresh, duplicate, revisions = [], 0, []
        for row in valid:
            revision = row["candidate_revision_sha256"]
            if revision in seen:
                duplicate += 1
            else:
                prior = latest.get(row["candidate_key"])
                if prior:
                    row["supersedes_candidate_revision_sha256"] = prior
                    revisions.append({"candidate_key": row["candidate_key"], "previous": prior, "current": revision})
                latest[row["candidate_key"]] = revision
                seen.add(revision)
                fresh.append(row)
        if fresh:
            payload = "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in existing + fresh)
            atomic_write(pool, payload.encode())
        readback = [json.loads(line) for line in pool.read_text().splitlines() if line.strip()] if pool.exists() else []
        if readback != existing + fresh:
            raise RuntimeError("candidate_pool_readback_mismatch")
    return {"input_cases": len(document["cases"]), "new": len(fresh), "duplicates": duplicate,
            "revisions": revisions,
            "rejected": rejected, "pool_rows": len(readback), "pool_sha256": digest(pool.read_bytes()) if pool.exists() else None,
            "training_admitted": 0, "model_calls": 0, "production_memory_writes": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--pool", type=Path, required=True)
    args = parser.parse_args(argv)
    print(json.dumps(export(args.manifest, args.pool), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
