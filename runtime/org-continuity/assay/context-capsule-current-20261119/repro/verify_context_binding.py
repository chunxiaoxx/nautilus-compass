#!/usr/bin/env python3
"""Self-contained verifier for the project-scoped context capsule pack."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def canonical(doc: dict) -> bytes:
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    capsule = json.loads((root / "payload" / "context_capsule.json").read_text(encoding="utf-8"))
    validation = json.loads((root / "payload" / "context_validation.json").read_text(encoding="utf-8"))

    stored = capsule.get("integrity", {}).get("sha256")
    unsigned = dict(capsule)
    unsigned.pop("signature", None)
    unsigned["integrity"] = {"algorithm": "sha256", "status": "computed"}
    integrity_ok = stored == sha256(canonical(unsigned))

    project = capsule.get("project", {})
    task = capsule.get("task", {})
    permissions = capsule.get("permissions", {})
    mapping_ok = all([
        capsule.get("schema") == "context-capsule/1",
        project.get("project_id") == "nautilus-compass",
        project.get("memory_namespace") == "-Users-chunxiao-wang-Projects-nautilus-compass",
        bool(project.get("project_path")),
        bool(project.get("source_head")),
        bool(task.get("task_id")),
        bool(task.get("thread_id")),
        validation.get("status") == "agree",
        capsule.get("live_evidence", {}).get("daemon_ping", {}).get("status") == "pass",
        "external-send" in permissions.get("denied", []),
        "publish-memory" in permissions.get("denied", []),
    ])
    value = bool(integrity_ok and mapping_ok)
    print(json.dumps({
        "value": 1 if value else 0,
        "integrity_ok": integrity_ok,
        "mapping_ok": mapping_ok,
        "validation_status": validation.get("status"),
        "daemon_ping": capsule.get("live_evidence", {}).get("daemon_ping", {}).get("status"),
        "signature_status": capsule.get("signature", {}).get("status"),
        "boundary": "internal_context_binding_only",
    }, ensure_ascii=False))
    return 0 if value else 1


if __name__ == "__main__":
    raise SystemExit(main())
