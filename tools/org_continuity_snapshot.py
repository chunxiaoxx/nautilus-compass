#!/usr/bin/env python3
"""Create a read-only organization continuity snapshot.

This is an audit receipt, not a business SSOT.  It deliberately reports local
state, live services, review progress, and customer-facing evidence as separate
sections so that copying files or seeing a process cannot be mistaken for
acceptance.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
PROJECTS_ROOT = HOME / ".claude" / "projects"
CORE_ROOT = ROOT.parent / "nautilus-core"
REPOS = {
    "compass": ROOT,
    "core": CORE_ROOT,
    "v5": ROOT.parent / "nautilus-v5",
    "flywheel": ROOT.parent / "nautilusflywheel",
}
VALIDATION_PATH = CORE_ROOT / "docs" / "org" / "ali-zen-pilot" / "client-requirements-validation.json"
REVIEW_PROGRESS = ROOT / "runtime" / "scratch_distill_pilot_20261104" / "semantic-review-progress.json"
SMOKE_RECEIPT = ROOT / "runtime" / "scratch_distill_pilot_20261104" / "verification_smoke_20261118" / "receipt.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def run(cmd: list[str], cwd: Path | None = None, timeout: float = 8.0) -> str:
    try:
        p = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=timeout,
            check=False,
        )
        return p.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def git_summary(name: str, path: Path) -> dict[str, Any]:
    exists = path.is_dir()
    if not exists:
        return {"name": name, "path": str(path), "exists": False}
    status_lines = run(["git", "status", "--short"], path, timeout=12).splitlines()
    branch = run(["git", "branch", "--show-current"], path)
    head = run(["git", "rev-parse", "HEAD"], path)
    upstream = run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"], path)
    counts = {"ahead": None, "behind": None}
    if upstream:
        raw = run(["git", "rev-list", "--left-right", "--count", f"HEAD...{upstream}"], path)
        try:
            left, right = raw.split()
            counts = {"ahead": int(left), "behind": int(right)}
        except (ValueError, AttributeError):
            pass
    worktrees = run(["git", "worktree", "list", "--porcelain"], path).splitlines()
    worktree_count = sum(1 for line in worktrees if line.startswith("worktree "))
    recent = run(["git", "log", "-3", "--date=iso-strict", "--format=%h %ad %s"], path, timeout=12).splitlines()
    agents = path / "AGENTS.md"
    return {
        "name": name,
        "path": str(path),
        "exists": True,
        "branch": branch or None,
        "head": head or None,
        "upstream": upstream or None,
        "ahead_behind": counts,
        "dirty_count": len(status_lines),
        "dirty_sample": status_lines[:8],
        "worktree_count": worktree_count,
        "agents_md": {"exists": agents.exists(), "sha256": sha256(agents)},
        "recent_commits": recent,
    }


def read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def memory_inventory() -> dict[str, Any]:
    if not PROJECTS_ROOT.is_dir():
        return {"root": str(PROJECTS_ROOT), "exists": False}
    all_files: list[Path] = []
    namespace_counts: dict[str, dict[str, int]] = {}
    for namespace in sorted(PROJECTS_ROOT.iterdir()):
        if not namespace.is_dir() or namespace.is_symlink():
            continue
        files = [p for p in namespace.rglob("*") if p.is_file() and not p.is_symlink()]
        namespace_counts[namespace.name] = {
            "files": len(files),
            "markdown": sum(p.suffix.lower() == ".md" for p in files),
        }
        all_files.extend(files)

    digest_counts: collections.Counter[str] = collections.Counter()
    for path in all_files:
        digest = sha256(path)
        if digest:
            digest_counts[digest] += 1
    duplicate_groups = sum(1 for n in digest_counts.values() if n > 1)
    duplicate_files = sum(n - 1 for n in digest_counts.values() if n > 1)

    active_names = {
        "compass": "-Users-chunxiao-wang-Projects-nautilus-compass",
        "core": "-Users-chunxiao-wang-Projects-nautilus-core",
        "v5": "-Users-chunxiao-wang-Projects-nautilus-v5",
        "flywheel": "-Users-chunxiao-wang-Projects-nautilusflywheel",
    }
    active: dict[str, Any] = {}
    for role, namespace in active_names.items():
        p = PROJECTS_ROOT / namespace / "memory"
        files = [x for x in p.rglob("*") if x.is_file() and not x.is_symlink()] if p.is_dir() else []
        semantic = collections.Counter()
        drift = collections.Counter()
        for path in files:
            if path.suffix.lower() != ".md":
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")[:8192]
            except OSError:
                continue
            m = re.search(r"(?m)^semantic_status:\s*([^\n#]+)", text)
            d = re.search(r"(?m)^drift:\s*([^\n#]+)", text)
            semantic[(m.group(1).strip().strip("'\"").lower() if m else "missing")] += 1
            drift[(d.group(1).strip().strip("'\"").lower() if d else "missing")] += 1
        active[role] = {
            "namespace": namespace,
            "path": str(p),
            "exists": p.is_dir(),
            "all_files": len(files),
            "markdown_files": sum(x.suffix.lower() == ".md" for x in files),
            "semantic_status": dict(sorted(semantic.items())),
            "drift": dict(sorted(drift.items())),
        }
    largest = sorted(namespace_counts.items(), key=lambda item: item[1]["files"], reverse=True)[:10]
    return {
        "root": str(PROJECTS_ROOT),
        "exists": True,
        "namespace_count": len(namespace_counts),
        "all_files": len(all_files),
        "unique_content_hashes": len(digest_counts),
        "duplicate_hash_groups": duplicate_groups,
        "duplicate_files_beyond_first": duplicate_files,
        "largest_namespaces": [{"namespace": k, **v} for k, v in largest],
        "active_projects": active,
    }


def daemon_probe() -> dict[str, Any]:
    result: dict[str, Any] = {"host": "127.0.0.1", "port": 9876, "tcp": False, "ping": None}
    try:
        with socket.create_connection(("127.0.0.1", 9876), timeout=2) as sock:
            result["tcp"] = True
            sock.sendall(b'{"action":"ping"}\n')
            data = b""
            while b"\n" not in data:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                data += chunk
            result["ping"] = json.loads(data.split(b"\n", 1)[0].decode("utf-8"))
    except Exception as exc:  # keep negative evidence in the receipt
        result["error"] = str(exc)
    return result


def port_probe(port: int) -> dict[str, Any]:
    out = {"port": port, "tcp": False}
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            out["tcp"] = True
    except OSError as exc:
        out["error"] = str(exc)
    return out


def service_snapshot() -> dict[str, Any]:
    gateway = run(["curl", "-sS", "--max-time", "3", "-o", "/dev/null", "-w", "%{http_code}", "http://127.0.0.1:8770/healthz"], timeout=5)
    return {
        "daemon_9876": daemon_probe(),
        "mcp_http_8097": port_probe(8097),
        "gateway_8770_healthz": gateway or None,
        "embed_8400": port_probe(8400),
        "rerank_8401": port_probe(8401),
    }


def review_snapshot() -> dict[str, Any]:
    data = read_json(REVIEW_PROGRESS)
    return {
        "path": str(REVIEW_PROGRESS),
        "exists": data is not None,
        "sha256": sha256(REVIEW_PROGRESS),
        "state": data,
    }


def smoke_snapshot() -> dict[str, Any]:
    data = read_json(SMOKE_RECEIPT)
    if data is None:
        return {"path": str(SMOKE_RECEIPT), "exists": False}
    keep = {
        "schema": data.get("schema"),
        "path": str(SMOKE_RECEIPT),
        "sha256": sha256(SMOKE_RECEIPT),
        "model": data.get("model"),
        "endpoint": data.get("endpoint"),
        "compression": data.get("compression"),
        "published_to_memory": data.get("published_to_memory"),
        "mechanical_verification": data.get("mechanical_verification"),
    }
    return keep


def validation_snapshot() -> dict[str, Any]:
    data = read_json(VALIDATION_PATH)
    if data is None:
        return {"path": str(VALIDATION_PATH), "exists": False}
    evidence = data.get("current_candidate_evidence") or {}
    rows = evidence.get("row_evidence") or {}
    statuses = collections.Counter(str(v.get("status", "missing")) for v in rows.values() if isinstance(v, dict))
    return {
        "path": str(VALIDATION_PATH),
        "exists": True,
        "sha256": sha256(VALIDATION_PATH),
        "at_utc": data.get("at_utc"),
        "row_count": data.get("row_count"),
        "pc_rows": data.get("pc_rows"),
        "mobile_rows": data.get("mobile_rows"),
        "conflict_count": data.get("conflict_count"),
        "all_document_checks_passed": data.get("all_document_checks_passed"),
        "engineering_evidence_checks": data.get("engineering_evidence_checks"),
        "row_status_counts": dict(sorted(statuses.items())),
        "customer_acceptance": evidence.get("customer_acceptance"),
        "model_runs_verified": evidence.get("model_runs_verified"),
        "human_grades_verified": evidence.get("human_grades_verified"),
        "external_messages_sent": evidence.get("external_messages_sent"),
        "latest_native_scoped_evidence_readback": data.get("latest_native_scoped_evidence_readback"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    snapshot = {
        "schema": "organization-continuity-snapshot/1",
        "generated_at_utc": utc_now(),
        "policy": "Read-only audit receipt; local/live/delivered/accepted gates remain separate; no cleanup, ack, send, deploy, or publish.",
        "repositories": [git_summary(name, path) for name, path in REPOS.items()],
        "memory": memory_inventory(),
        "services": service_snapshot(),
        "semantic_review": review_snapshot(),
        "local_9b_smoke": smoke_snapshot(),
        "platform_validation": validation_snapshot(),
        "gates": {
            "organization_continuity": "observed_snapshot_only",
            "memory_publication": "blocked_until_signed_independent_receipt_and_consumer_readback",
            "9b_full_history_acceptance": "not_done",
            "customer_acceptance": "not_claimed",
        },
        "next_action": {
            "owner": "compass",
            "action": "Use this snapshot as the single readback for the next coordination round; then close one P0 gate: trusted user-to-project-task mapping or signed Assay receipt plus consumer readback.",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.output.with_suffix(args.output.suffix + ".tmp")
    tmp.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(args.output)
    print(json.dumps({"path": str(args.output), "sha256": sha256(args.output), "generated_at_utc": snapshot["generated_at_utc"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
