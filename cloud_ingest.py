"""v1.6.0 · 用户 #1 真融合 · 把本地 session_*.md push 到 cloud /v1/v14/ingest_obs

V7-N5 phase 2 P0:
本地 stop_hook 已写 session_*.md + drift sidecar · 但 cloud 不知道(local 不 sync cloud)。
V5/Kairos/Souls Fusion 的 cross-dialog recall 看不到我(claude-code-compass-dialog)写的。

修法: 每次 stop_hook 新写一份 session_*.md 后 · SSH inline POST 到 cloud:8770/v1/v14/ingest_obs ·
Cloud 当成自己 dir 收下 + BGE 索引 · 跨 dialog recall 可见。

Idempotent: sidecar `.cloud_ingested.jsonl` 一行一 session_name · 不重复 push。
Fail-soft: SSH 失败不 raise · stop_hook 继续。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

PLUGIN_DIR = Path(__file__).parent
SIDECAR = PLUGIN_DIR / ".cache" / "cloud_ingested.jsonl"
CLOUD_HOST = os.environ.get("COMPASS_SSH_HOST", "cloud")
CLOUD_URL = os.environ.get(
    "COMPASS_CLOUD_INGEST_URL", "http://127.0.0.1:8770/v1/v14/ingest_obs"
)
AGENT_TYPE = os.environ.get("COMPASS_AGENT_TYPE", "claude-code-compass-dialog")
TIMEOUT_S = 12


def _already_pushed(session_name: str) -> bool:
    if not SIDECAR.exists():
        return False
    try:
        for line in SIDECAR.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("session_name") == session_name:
                return True
    except Exception:
        pass
    return False


def _record_push(session_name: str, result: dict) -> None:
    SIDECAR.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "session_name": session_name,
        "ts": int(time.time()),
        "ok": bool(result.get("ok")),
        "cloud_path": result.get("session_path"),
        "agent_type": result.get("agent_type"),
    }
    with open(SIDECAR, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _extract_summary(body: str) -> str:
    """Return first non-empty non-frontmatter line · used as description."""
    in_fm = False
    for line in body.splitlines():
        s = line.strip()
        if s == "---":
            in_fm = not in_fm
            continue
        if in_fm or not s or s.startswith("#"):
            continue
        return s[:200]
    return body[:200]


def _read_drift_for(session_name: str) -> str:
    """Pull drift label from drift_sidecar if present · else 'green'."""
    sidecar = PLUGIN_DIR / ".cache" / "drift_sidecar.jsonl"
    if not sidecar.exists():
        return "green"
    try:
        for line in sidecar.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("session_name") == session_name:
                d = obj.get("drift") or {}
                if d.get("should_alert"):
                    return "red"
                score = d.get("score", 0)
                if isinstance(score, (int, float)) and score < -0.03:
                    return "yellow"
                return "green"
    except Exception:
        pass
    return "green"


def ingest_session_to_cloud(session_path: Path) -> Optional[dict]:
    """SSH inline POST one session_*.md to cloud /v1/v14/ingest_obs.

    Returns response dict on success · None on any failure (fail-soft).
    """
    if not session_path.exists():
        return None
    if _already_pushed(session_path.name):
        return None

    try:
        body = session_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None

    name = session_path.stem[:80]
    description = _extract_summary(body)
    drift = _read_drift_for(session_path.name)

    payload = {
        "name": name,
        "content": body[:8000],
        "description": description,
        "drift": drift,
        "thread_role": "self_note",
    }
    payload_json = json.dumps(payload, ensure_ascii=False)

    # SSH inline: pipe payload to curl on cloud. Avoids needing a local tunnel.
    # curl --data-binary @- reads stdin · we pipe via ssh stdin.
    cmd = [
        "ssh",
        "-o", "ConnectTimeout=8",
        "-o", "ServerAliveInterval=5",
        CLOUD_HOST,
        # POST via curl on cloud localhost · trust X-Tenant-ID for auth
        f"curl -s -X POST {CLOUD_URL} "
        f"-H 'X-Tenant-ID: {AGENT_TYPE}' "
        f"-H 'X-User-ID: {AGENT_TYPE}' "
        f"-H 'Content-Type: application/json' "
        f"--data-binary @- --max-time 10",
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=payload_json.encode("utf-8"),
            capture_output=True,
            timeout=TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"[cloud_ingest] timeout · session={session_path.name}\n")
        return None
    except Exception as e:
        sys.stderr.write(f"[cloud_ingest] ssh fail: {e}\n")
        return None

    if proc.returncode != 0:
        sys.stderr.write(
            f"[cloud_ingest] ssh rc={proc.returncode} · stderr={proc.stderr.decode(errors='replace')[:200]}\n"
        )
        return None

    try:
        result = json.loads(proc.stdout.decode("utf-8", errors="replace"))
    except Exception:
        sys.stderr.write(
            f"[cloud_ingest] parse fail · stdout={proc.stdout[:200].decode(errors='replace')}\n"
        )
        return None

    if not result.get("ok"):
        sys.stderr.write(f"[cloud_ingest] cloud returned ok=False · {result}\n")
        return None

    _record_push(session_path.name, result)
    return result


def push_recent(within_hours: float = 24.0, project_dir: Optional[Path] = None) -> tuple[int, int]:
    """Push 24h-glob un-pushed sessions to cloud.

    Returns (pushed_count, total_candidates).
    """
    if project_dir is None:
        # Default: scan all project memory dirs under .claude/projects/<proj>/memory/
        roots = list((Path.home() / ".claude" / "projects").glob("C--*/memory"))
    else:
        roots = [project_dir]

    cutoff = time.time() - within_hours * 3600
    pushed = 0
    total = 0
    for root in roots:
        for f in root.glob("session_*.md"):
            try:
                if f.stat().st_mtime < cutoff:
                    continue
                if _already_pushed(f.name):
                    continue
                total += 1
                result = ingest_session_to_cloud(f)
                if result and result.get("ok"):
                    pushed += 1
            except Exception as e:
                sys.stderr.write(f"[cloud_ingest] push {f.name} fail: {e}\n")
    return pushed, total


if __name__ == "__main__":
    # CLI smoke: python cloud_ingest.py <session_path>
    if len(sys.argv) > 1:
        result = ingest_session_to_cloud(Path(sys.argv[1]))
        print(json.dumps(result, indent=2) if result else "FAIL")
    else:
        pushed, total = push_recent(within_hours=24.0)
        print(f"pushed {pushed} / {total} session(s) within 24h")
