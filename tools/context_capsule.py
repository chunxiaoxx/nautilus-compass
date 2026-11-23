#!/usr/bin/env python3
"""Create and validate a project-scoped context capsule.

The capsule binds an actor, project namespace, task, thread, checkout, and
allowed actions.  It is intentionally hash-bound but unsigned: Assay signing
is a later gate, and an unsigned capsule must never be treated as a signed
verdict or customer acceptance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MEMORY_NAMESPACE = "-Users-chunxiao-wang-Projects-nautilus-compass"
DAEMON_PATH = Path.home() / ".claude" / "plugins" / "nautilus-compass" / "daemon.py"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def run(cmd: list[str], cwd: Path = ROOT, timeout: float = 5.0) -> str:
    try:
        p = subprocess.run(
            cmd, cwd=str(cwd), text=True, capture_output=True,
            timeout=timeout, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return p.stdout.strip()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str | None:
    try:
        return sha256_bytes(path.read_bytes())
    except OSError:
        return None


def cognition_vault_binding(path: Path | None = None, *, required: bool = False) -> dict[str, Any]:
    """Bind an optional protected cognition projection by path and hash."""
    selected = path or (Path(os.environ["NAUTILUS_CORE_COGNITION_VAULT"]) if os.environ.get("NAUTILUS_CORE_COGNITION_VAULT") else None)
    binding: dict[str, Any] = {
        "required": required,
        "status": "unbound",
        "path": str(selected) if selected else "",
        "sha256": "",
        "vault_id": "",
    }
    if selected is None:
        return binding
    digest = sha256_file(selected)
    binding["sha256"] = digest or ""
    if digest is None:
        binding["status"] = "missing"
        return binding
    try:
        doc = json.loads(selected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        binding["status"] = "invalid"
        return binding
    binding["vault_id"] = str(doc.get("vault_id", ""))
    binding["status"] = "bound" if binding["vault_id"] else "invalid"
    return binding


def canonical_bytes(doc: dict[str, Any]) -> bytes:
    return json.dumps(doc, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def actor_identity() -> dict[str, str]:
    email = run(["git", "config", "--get", "user.email"])
    identity_hash = sha256_bytes(email.encode("utf-8"))[:16] if email else None
    return {
        "user_id": "local:chunxiao.wang",
        "identity_source": "git_user_email_sha256_prefix" if identity_hash else "unavailable",
        "identity_sha256_prefix": identity_hash or "",
    }


def git_binding() -> dict[str, Any]:
    root = run(["git", "rev-parse", "--show-toplevel"])
    branch = run(["git", "branch", "--show-current"])
    head = run(["git", "rev-parse", "HEAD"])
    dirty = run(["git", "status", "--short"]).splitlines()
    return {
        "project_path": str(ROOT),
        "git_root": root,
        "branch": branch,
        "source_head": head,
        "dirty_count": len(dirty),
        "dirty_sample": dirty[:8],
    }


def daemon_ping() -> dict[str, Any]:
    result: dict[str, Any] = {"endpoint": "127.0.0.1:9876", "status": "fail"}
    try:
        with socket.create_connection(("127.0.0.1", 9876), timeout=2) as sock:
            sock.sendall(b'{"action":"ping"}\n')
            buf = b""
            while b"\n" not in buf:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
        payload = json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
        result.update({"status": "pass" if payload.get("pong") else "fail", "payload": payload})
    except Exception as exc:  # preserve negative evidence in the capsule
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_capsule(
    task_id: str,
    thread_id: str,
    owner: str = "compass",
    *,
    goal: str | None = None,
    vault_path: Path | None = None,
    require_vault: bool = False,
) -> dict[str, Any]:
    binding = git_binding()
    capsule: dict[str, Any] = {
        "schema": "context-capsule/1",
        "capsule_id": f"{task_id}:{thread_id}",
        "created_at_utc": now_utc(),
        "authorization_basis": "current_user_instruction_continue",
        "scope": "organization-continuity-and-recall-gate",
        "actor": {**actor_identity(), "role": owner},
        "project": {
            "project_id": "nautilus-compass",
            "memory_namespace": MEMORY_NAMESPACE,
            **binding,
            "agents_sha256": sha256_file(ROOT / "AGENTS.md"),
        },
        "task": {
            "task_id": task_id,
            "owner": owner,
            "thread_id": thread_id,
            "goal": goal or "project-scoped continuity task",
        },
        "cognition_vault": cognition_vault_binding(vault_path, required=require_vault),
        "permissions": {
            "allowed": [
                "read:organization-state",
                "run:local-probes",
                "write:compass/runtime/org-continuity",
            ],
            "denied": [
                "external-send",
                "external-reply",
                "deploy",
                "publish-memory",
                "ack-mailbox",
                "clean-unrelated-worktrees",
            ],
        },
        "live_evidence": {
            "daemon_source_sha256": sha256_file(DAEMON_PATH),
            "daemon_ping": daemon_ping(),
        },
        "gates": {
            "user_project_task_mapping": "bound_if_validation_passes",
            "assay_signature": "not_signed",
            "consumer_readback": "pending",
        },
        "integrity": {"algorithm": "sha256", "status": "computed"},
    }
    unsigned = dict(capsule)
    unsigned["integrity"] = {"algorithm": "sha256", "status": "computed"}
    capsule["integrity"]["sha256"] = sha256_bytes(canonical_bytes(unsigned))
    capsule["signature"] = {
        "status": "not_signed",
        "reason": "Context binding is hash-bound in this P0 step; Assay Ed25519 receipt is a later gate.",
    }
    return capsule


def validate_capsule(capsule: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, Any] = {}
    mismatches: list[str] = []
    project = capsule.get("project") or {}
    task = capsule.get("task") or {}
    checks["schema"] = capsule.get("schema") == "context-capsule/1"
    checks["project_id"] = project.get("project_id") == "nautilus-compass"
    checks["memory_namespace"] = project.get("memory_namespace") == MEMORY_NAMESPACE
    checks["project_path"] = project.get("project_path") == str(ROOT)
    checks["git_root"] = project.get("git_root") == str(ROOT)
    checks["task_id_present"] = bool(task.get("task_id"))
    checks["thread_id_present"] = bool(task.get("thread_id"))
    current = git_binding()
    checks["branch_unchanged"] = project.get("branch") == current.get("branch")
    checks["source_head_unchanged"] = project.get("source_head") == current.get("source_head")
    checks["daemon_ping"] = daemon_ping().get("status") == "pass"
    vault = capsule.get("cognition_vault") or {}
    checks["cognition_vault"] = True
    if vault.get("required"):
        vault_path = Path(str(vault.get("path", "")))
        current_hash = sha256_file(vault_path) if vault_path else None
        checks["cognition_vault"] = (
            vault.get("status") == "bound"
            and bool(vault.get("vault_id"))
            and current_hash == vault.get("sha256")
        )
    for key, ok in checks.items():
        if not ok:
            mismatches.append(key)
    status = "agree" if not mismatches else "not_computable"
    return {
        "status": status,
        "checks": checks,
        "mismatches": mismatches,
        "validated_at_utc": now_utc(),
        "note": "A changed head or project path invalidates this capsule; regenerate instead of guessing.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("make")
    make.add_argument("--task-id", required=True)
    make.add_argument("--thread-id", required=True)
    make.add_argument("--owner", default="compass")
    make.add_argument("--goal")
    make.add_argument("--vault", type=Path)
    make.add_argument("--require-vault", action="store_true")
    make.add_argument("--output", type=Path, required=True)
    val = sub.add_parser("validate")
    val.add_argument("--capsule", type=Path, required=True)
    val.add_argument("--require-vault", action="store_true")
    args = parser.parse_args()
    if args.command == "make":
        doc = build_capsule(
            args.task_id,
            args.thread_id,
            args.owner,
            goal=args.goal,
            vault_path=args.vault,
            require_vault=args.require_vault,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        tmp = args.output.with_suffix(args.output.suffix + ".tmp")
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(args.output)
        print(json.dumps({"status": "created", "path": str(args.output), "sha256": sha256_file(args.output)}, ensure_ascii=False))
        return 0
    try:
        capsule = json.loads(args.capsule.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "not_computable", "error": str(exc)}, ensure_ascii=False))
        return 2
    if args.require_vault:
        capsule.setdefault("cognition_vault", {})["required"] = True
    result = validate_capsule(capsule)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "agree" else 1


if __name__ == "__main__":
    raise SystemExit(main())
