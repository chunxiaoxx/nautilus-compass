"""v1.7.1+ · GBrain-paradigm minimal job queue runtime · SQLite-backed.

Upgrades add_worker (Phase 2.B · spec-only) into a real queue with enqueue/dequeue/
status/list/process_due API.

Design:
  - SQLite single-file DB (.cache/job_queue.db) · no external deps
  - jobs table: id PK, worker_name, payload (JSON), status, scheduled_at, claimed_at,
    completed_at, result, attempts, max_attempts, error
  - workers table: name PK, spec_type, config (JSON), registered_at, enabled
  - Status state machine: pending → claimed → (completed|failed|retry_pending)
  - Cron-driven invocation (not long-running daemon) · process_due() called by
    external scheduler (systemd timer, Claude Code Stop hook, manual CLI)

Reference: GBrain "BullMQ-shaped, Postgres-native job queue" paradigm · clean-room
Python+SQLite implementation. NO LLM. Reference: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md.
"""
from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Callable

DEFAULT_DB_PATH = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "job_queue.db"
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_CLAIM_TIMEOUT_SEC = 300  # claimed jobs expire if not completed within 5min

STATUS_PENDING = "pending"
STATUS_CLAIMED = "claimed"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_RETRY_PENDING = "retry_pending"

VALID_STATUSES = (STATUS_PENDING, STATUS_CLAIMED, STATUS_COMPLETED,
                  STATUS_FAILED, STATUS_RETRY_PENDING)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _now_epoch() -> float:
    return time.time()


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Open SQLite connection · create schema if missing.

    NOTE: caller is responsible for closing (use _db() context manager · sqlite3
    builtin __exit__ commits but does NOT close · Windows holds file lock).
    """
    if db_path is None:
        db_path = DEFAULT_DB_PATH
    if not isinstance(db_path, Path):
        db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            name TEXT PRIMARY KEY,
            spec_type TEXT NOT NULL,
            config TEXT NOT NULL DEFAULT '{}',
            registered_at TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            worker_name TEXT NOT NULL,
            payload TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending',
            scheduled_at REAL NOT NULL,
            claimed_at REAL,
            completed_at REAL,
            result TEXT,
            attempts INTEGER NOT NULL DEFAULT 0,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            error TEXT,
            created_at REAL NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status_scheduled ON jobs(status, scheduled_at)")
    conn.commit()
    return conn


@contextlib.contextmanager
def _db(db_path: Optional[Path] = None):
    """Context manager · ensures connection is closed on exit (Windows safe)."""
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def register_worker(name: str, spec_type: str = "custom",
                    config: Optional[dict] = None,
                    db_path: Optional[Path] = None) -> dict:
    """Register a worker · idempotent (updates spec_type/config on conflict)."""
    if not name or not isinstance(name, str):
        return {"ok": False, "reason": "name required"}
    if spec_type not in ("cron", "pubsub", "queue", "http", "custom"):
        spec_type = "custom"
    config_json = json.dumps(config or {}, ensure_ascii=False)
    with _db(db_path) as conn:
        conn.execute("""
            INSERT INTO workers(name, spec_type, config, registered_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET spec_type=excluded.spec_type, config=excluded.config
        """, (name, spec_type, config_json, _now_iso()))
        conn.commit()
    return {"ok": True, "name": name, "spec_type": spec_type}


def enqueue(worker_name: str, payload: Optional[dict] = None,
            scheduled_at: Optional[float] = None,
            max_attempts: int = DEFAULT_MAX_ATTEMPTS,
            db_path: Optional[Path] = None) -> int:
    """Insert a new job · returns job id."""
    payload_json = json.dumps(payload or {}, ensure_ascii=False)
    sched = scheduled_at if scheduled_at is not None else _now_epoch()
    now = _now_epoch()
    with _db(db_path) as conn:
        cur = conn.execute("""
            INSERT INTO jobs(worker_name, payload, status, scheduled_at,
                             max_attempts, created_at)
            VALUES(?, ?, 'pending', ?, ?, ?)
        """, (worker_name, payload_json, sched, max_attempts, now))
        conn.commit()
        return cur.lastrowid


def claim_due(worker_name: Optional[str] = None,
              limit: int = 10,
              db_path: Optional[Path] = None) -> list:
    """Atomically claim due jobs · sets status='claimed' + claimed_at.

    If worker_name None · claims jobs across all workers.
    Returns list of job dicts.
    """
    now = _now_epoch()
    claimed: list = []
    with _db(db_path) as conn:
        # Find due jobs
        if worker_name:
            rows = conn.execute("""
                SELECT * FROM jobs
                WHERE status IN ('pending', 'retry_pending')
                  AND scheduled_at <= ?
                  AND worker_name = ?
                ORDER BY scheduled_at ASC LIMIT ?
            """, (now, worker_name, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM jobs
                WHERE status IN ('pending', 'retry_pending')
                  AND scheduled_at <= ?
                ORDER BY scheduled_at ASC LIMIT ?
            """, (now, limit)).fetchall()
        for row in rows:
            conn.execute("""
                UPDATE jobs SET status='claimed', claimed_at=?, attempts=attempts+1
                WHERE id=? AND status IN ('pending', 'retry_pending')
            """, (now, row["id"]))
            claimed.append(_row_to_dict(row, status_override="claimed",
                                         claimed_at=now,
                                         attempts=row["attempts"] + 1))
        conn.commit()
    return claimed


def complete(job_id: int, result: Optional[dict] = None,
             db_path: Optional[Path] = None) -> bool:
    """Mark job completed · stores result JSON."""
    result_json = json.dumps(result or {}, ensure_ascii=False) if result else None
    with _db(db_path) as conn:
        cur = conn.execute("""
            UPDATE jobs SET status='completed', completed_at=?, result=?
            WHERE id=? AND status='claimed'
        """, (_now_epoch(), result_json, job_id))
        conn.commit()
        return cur.rowcount > 0


def fail(job_id: int, error: str = "",
         retry_after_sec: float = 60.0,
         db_path: Optional[Path] = None) -> dict:
    """Mark job failed · retry if attempts < max_attempts, else final fail."""
    with _db(db_path) as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            return {"ok": False, "reason": "job not found"}
        if row["attempts"] >= row["max_attempts"]:
            conn.execute("""
                UPDATE jobs SET status='failed', error=?, completed_at=?
                WHERE id=?
            """, (error[:1000], _now_epoch(), job_id))
            conn.commit()
            return {"ok": True, "status": "failed", "final": True}
        # Schedule retry
        new_sched = _now_epoch() + retry_after_sec
        conn.execute("""
            UPDATE jobs SET status='retry_pending', error=?, scheduled_at=?, claimed_at=NULL
            WHERE id=?
        """, (error[:1000], new_sched, job_id))
        conn.commit()
        return {"ok": True, "status": "retry_pending", "retry_in_sec": retry_after_sec}


def reap_stale_claims(claim_timeout_sec: float = DEFAULT_CLAIM_TIMEOUT_SEC,
                      db_path: Optional[Path] = None) -> int:
    """Move stale 'claimed' jobs back to 'retry_pending' · returns count reaped."""
    cutoff = _now_epoch() - claim_timeout_sec
    with _db(db_path) as conn:
        cur = conn.execute("""
            UPDATE jobs SET status='retry_pending', claimed_at=NULL,
                            scheduled_at=?, error='stale claim reaped'
            WHERE status='claimed' AND claimed_at < ?
        """, (_now_epoch(), cutoff))
        conn.commit()
        return cur.rowcount


def list_jobs(status: Optional[str] = None,
              worker_name: Optional[str] = None,
              limit: int = 50,
              db_path: Optional[Path] = None) -> list:
    """List jobs filtered by status/worker_name."""
    with _db(db_path) as conn:
        q = "SELECT * FROM jobs WHERE 1=1"
        params: list = []
        if status:
            q += " AND status=?"
            params.append(status)
        if worker_name:
            q += " AND worker_name=?"
            params.append(worker_name)
        q += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(q, tuple(params)).fetchall()
    return [_row_to_dict(r) for r in rows]


def stats(db_path: Optional[Path] = None) -> dict:
    """Return job counts by status."""
    with _db(db_path) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS n FROM jobs GROUP BY status"
        ).fetchall()
    return {r["status"]: r["n"] for r in rows}


def process_due(handler: Callable[[dict], dict],
                worker_name: Optional[str] = None,
                limit: int = 10,
                db_path: Optional[Path] = None) -> dict:
    """Claim + invoke handler + complete/fail · cron-driven invocation.

    Args:
        handler: callable(job_dict) → result_dict (raises on failure)
        worker_name: filter by worker
        limit: max jobs per invocation

    Returns:
        {"claimed": N, "completed": N, "failed": N}
    """
    reaped = reap_stale_claims(db_path=db_path)
    claimed = claim_due(worker_name=worker_name, limit=limit, db_path=db_path)
    completed_count = 0
    failed_count = 0
    for job in claimed:
        try:
            result = handler(job)
            if complete(job["id"], result=result, db_path=db_path):
                completed_count += 1
        except Exception as e:
            fail(job["id"], error=str(e), db_path=db_path)
            failed_count += 1
    return {
        "claimed": len(claimed),
        "completed": completed_count,
        "failed": failed_count,
        "reaped_stale": reaped,
    }


def _row_to_dict(row, status_override=None, claimed_at=None, attempts=None) -> dict:
    if row is None:
        return {}
    try:
        payload = json.loads(row["payload"]) if row["payload"] else {}
    except (json.JSONDecodeError, TypeError):
        payload = {}
    try:
        result = json.loads(row["result"]) if row["result"] else None
    except (json.JSONDecodeError, TypeError):
        result = None
    return {
        "id": row["id"],
        "worker_name": row["worker_name"],
        "payload": payload,
        "status": status_override or row["status"],
        "scheduled_at": row["scheduled_at"],
        "claimed_at": claimed_at if claimed_at is not None else row["claimed_at"],
        "completed_at": row["completed_at"],
        "result": result,
        "attempts": attempts if attempts is not None else row["attempts"],
        "max_attempts": row["max_attempts"],
        "error": row["error"],
    }
