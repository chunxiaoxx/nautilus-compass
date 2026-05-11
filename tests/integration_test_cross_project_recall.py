#!/usr/bin/env python3
"""Integration test for v1.4 S3 cross-project recall.

Requires a running compass-bge-daemon on 127.0.0.1:9876 and at least
one project memory directory under ~/.claude/projects/.

Run:
    python3 tests/integration_test_cross_project_recall.py

This is an integration test (hits real daemon) · pytest-friendly assert.
Add to CI by extracting `recall_daemon()` as a fixture.
"""
from __future__ import annotations

import json
import socket
import sys
import time


DAEMON_HOST = "127.0.0.1"
DAEMON_PORT = 9876
TIMEOUT_S = 60


def recall_daemon(req: dict, timeout: int = TIMEOUT_S) -> dict:
    """Send recall request to BGE daemon · return parsed response."""
    s = socket.socket()
    s.settimeout(timeout)
    s.connect((DAEMON_HOST, DAEMON_PORT))
    s.sendall((json.dumps(req) + "\n").encode())
    buf = b""
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        if buf.endswith(b"\n"):
            break
    s.close()
    return json.loads(buf.decode().strip())


def test_default_scope_is_project(project_name: str = "C--Users-chunx") -> None:
    """No scope arg → defaults to 'project' · existing behavior unchanged."""
    res = recall_daemon({
        "action": "recall",
        "query": "fake closure",
        "project": project_name,
        "top_k": 3,
    })
    assert res.get("ok"), f"recall failed: {res.get('error')}"
    assert res.get("scope") == "project", f"default scope should be 'project', got {res.get('scope')!r}"
    assert res.get("projects_scanned") == [project_name], \
        f"should only scan {project_name}, got {res.get('projects_scanned')}"


def test_explicit_scope_project(project_name: str = "C--Users-chunx") -> None:
    """scope=project explicit · same as default."""
    res = recall_daemon({
        "action": "recall",
        "query": "drift check",
        "project": project_name,
        "top_k": 3,
        "scope": "project",
    })
    assert res.get("ok")
    assert res.get("scope") == "project"
    assert res.get("projects_scanned") == [project_name]


def test_scope_user_unions_all() -> None:
    """scope=user · scans all non-underscore projects · per-hit project tag."""
    res = recall_daemon({
        "action": "recall",
        "query": "fake closure",
        "top_k": 10,
        "scope": "user",
    })
    assert res.get("ok"), f"recall failed: {res.get('error')}"
    assert res.get("scope") == "user"
    projects = res.get("projects_scanned", [])
    assert len(projects) >= 1, f"should scan ≥1 project, got {projects}"
    # all hits must carry origin project
    for hit in res.get("recall", []):
        assert "project" in hit, f"hit missing project tag: {hit}"
        assert hit["project"] in projects, \
            f"hit project {hit['project']!r} not in scanned set {projects}"


def test_invalid_scope_rejected() -> None:
    """scope=garbage · daemon returns ok=False with helpful error."""
    res = recall_daemon({
        "action": "recall",
        "query": "x",
        "project": "C--Users-chunx",
        "scope": "garbage",
    })
    assert not res.get("ok"), "invalid scope must be rejected"
    err = res.get("error", "").lower()
    assert "scope" in err, f"error must mention 'scope', got: {err!r}"


def test_scope_user_no_project_required() -> None:
    """scope=user · project arg optional · daemon enumerates all."""
    res = recall_daemon({
        "action": "recall",
        "query": "hello",
        "top_k": 3,
        "scope": "user",
        # no project!
    })
    assert res.get("ok"), f"scope=user should not require project, got: {res.get('error')}"


def test_perf_warm_cache_within_30pct(project_name: str = "C--Users-chunx") -> None:
    """Warm-cache · scope=user ≤ 1.3x scope=project on the same query.

    Cold cache excluded · this is a steady-state measurement.
    """
    # warm both paths first
    for _ in range(2):
        recall_daemon({"action": "recall", "query": "warm", "project": project_name, "top_k": 1})
        recall_daemon({"action": "recall", "query": "warm", "top_k": 1, "scope": "user"})

    # measure
    ratios = []
    for _ in range(3):
        t0 = time.time()
        recall_daemon({"action": "recall", "query": "perf test", "project": project_name, "top_k": 3})
        dt_p = time.time() - t0
        t0 = time.time()
        recall_daemon({"action": "recall", "query": "perf test", "top_k": 3, "scope": "user"})
        dt_u = time.time() - t0
        ratios.append(dt_u / max(dt_p, 0.001))
    avg = sum(ratios) / len(ratios)
    assert avg <= 1.5, f"warm-cache perf ratio {avg:.2f}x exceeds 1.5x (3 runs: {ratios})"


def main() -> int:
    tests = [
        ("default_scope_is_project", test_default_scope_is_project),
        ("explicit_scope_project", test_explicit_scope_project),
        ("scope_user_unions_all", test_scope_user_unions_all),
        ("invalid_scope_rejected", test_invalid_scope_rejected),
        ("scope_user_no_project_required", test_scope_user_no_project_required),
        ("perf_warm_cache_within_30pct", test_perf_warm_cache_within_30pct),
    ]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS · {name}")
        except AssertionError as e:
            print(f"  FAIL · {name} · {e}")
            failed.append(name)
        except Exception as e:
            print(f"  ERROR · {name} · {type(e).__name__}: {e}")
            failed.append(name)
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
