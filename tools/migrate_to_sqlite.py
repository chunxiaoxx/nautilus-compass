"""compass v0.9.1 · migrate file-based memory/*.md → sqlite observations table.

Reads ~/.claude/projects/<project>/memory/*.md and inserts rows into
the v0.9 observations table. Used for one-time migration when a user
upgrades from v0.7.2 / v0.8 to v0.9.

Schema target: see paper/V09_USER_SCHEMA.md / paper/V10_FINAL_SPEC.md §3.

Usage:
  python tools/migrate_to_sqlite.py [--dry-run] [--user-id u_xxx] \
                                     [--db /var/lib/compass/compass.db] \
                                     [--projects ~/.claude/projects]

Behavior:
  · Reads all session_*.md and existing memory/*.md files
  · Parses YAML frontmatter (name · description · type · concept · drift · drift_signals)
  · Generates obs_id from filename hash
  · Generates agent_id from frontmatter `agent_type` field (or 'claude-code' default)
  · INSERT OR IGNORE (idempotent · safe to re-run)

Output: count of inserted / skipped / failed rows.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

DEFAULT_DB = Path(os.environ.get("COMPASS_DB_PATH", "/var/lib/compass/compass.db"))
DEFAULT_PROJECTS = Path.home() / ".claude" / "projects"
DEFAULT_REGION = os.environ.get("COMPASS_REGION", "cn-shanghai")


@contextmanager
def db(path: Path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_schema(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with db(path) as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                region TEXT NOT NULL,
                passphrase_hash TEXT,
                encryption_salt BLOB,
                plan TEXT DEFAULT 'free',
                created_at TEXT NOT NULL,
                last_login_at TEXT
            );
            CREATE TABLE IF NOT EXISTS agents (
                agent_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                device_id TEXT,
                workspace TEXT,
                metadata TEXT,
                created_at TEXT NOT NULL,
                last_seen_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_agents_user ON agents(user_id);
            CREATE TABLE IF NOT EXISTS observations (
                obs_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                ts TEXT NOT NULL,
                type TEXT,
                concept TEXT,
                drift TEXT,
                drift_signals TEXT,
                region TEXT NOT NULL,
                content_plain TEXT,
                encrypted_body BLOB,
                encryption_version TEXT,
                indexed BOOLEAN DEFAULT 0,
                source_path TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_obs_user_ts ON observations(user_id, ts DESC);
            CREATE INDEX IF NOT EXISTS idx_obs_drift ON observations(user_id, drift);
            CREATE INDEX IF NOT EXISTS idx_obs_type ON observations(user_id, type);
        """)


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Returns (frontmatter_dict, body_text)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text
    fm_block = text[4:end]
    body = text[end + 4:].strip()
    fm: dict = {}
    in_signals = False
    signals: list = []
    for line in fm_block.splitlines():
        if in_signals:
            m = re.match(r"\s*-\s*(.+)", line)
            if m:
                signals.append(m.group(1).strip().strip('"').strip("'"))
                continue
            in_signals = False
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            k = k.strip(); v = v.strip().strip('"').strip("'")
            if k == "drift_signals":
                if v == "[]":
                    fm["drift_signals"] = []
                elif v.startswith("["):
                    inner = v.strip("[]").strip()
                    fm["drift_signals"] = ([x.strip().strip('"').strip("'")
                                            for x in inner.split(",") if x.strip()] if inner else [])
                elif v == "":
                    in_signals = True
                    fm["drift_signals"] = []
                else:
                    fm["drift_signals"] = [v]
            else:
                fm[k] = v
    if in_signals or signals:
        fm["drift_signals"] = signals
    return fm, body


def gen_obs_id(file_path: Path) -> str:
    """Deterministic obs_id from file path · idempotent re-run."""
    h = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:10]
    return f"ob_{h}"


def gen_agent_id(user_id: str, agent_type: str) -> str:
    """Deterministic agent_id per user × agent_type."""
    h = hashlib.sha256(f"{user_id}::{agent_type}".encode("utf-8")).hexdigest()[:8]
    return f"ag_{agent_type}_{h}"


def load_session_files(projects_dir: Path) -> Iterable[tuple[str, Path]]:
    """Yield (project_name, file_path) for all memory/*.md files."""
    for proj in projects_dir.iterdir():
        if not proj.is_dir():
            continue
        memdir = proj / "memory"
        if not memdir.exists():
            continue
        for f in sorted(memdir.glob("*.md")):
            yield proj.name, f


def ensure_user(conn: sqlite3.Connection, user_id: str, region: str):
    """If user not exists · create as system user (no passphrase · plan=free)."""
    row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
    if row:
        return
    conn.execute("""
        INSERT INTO users (user_id, region, plan, created_at)
        VALUES (?, ?, 'free', ?)
    """, (user_id, region, datetime.now(timezone.utc).isoformat()))


def ensure_agent(conn: sqlite3.Connection, agent_id: str, user_id: str,
                 agent_type: str, workspace: str):
    row = conn.execute("SELECT agent_id FROM agents WHERE agent_id = ?",
                       (agent_id,)).fetchone()
    if row:
        return
    conn.execute("""
        INSERT INTO agents (agent_id, user_id, agent_type, workspace, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (agent_id, user_id, agent_type, workspace,
          datetime.now(timezone.utc).isoformat()))


def migrate_one(conn: sqlite3.Connection, file_path: Path, project: str,
                user_id: str, region: str, dry_run: bool = False) -> str:
    """Returns: 'inserted' | 'skipped' | 'failed:<reason>'."""
    try:
        text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return f"failed:read_error:{e}"

    fm, body = parse_frontmatter(text)
    name = fm.get("name") or file_path.stem
    description = fm.get("description") or ""
    type_ = fm.get("type") or "discovery"
    concept = fm.get("concept") or "pattern"
    drift = fm.get("drift") or "?"
    drift_signals = fm.get("drift_signals") or []
    agent_type = fm.get("agent_type") or "claude-code"

    obs_id = gen_obs_id(file_path)
    agent_id = gen_agent_id(user_id, agent_type)
    mtime = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()

    content = json.dumps({"name": name, "description": description, "body": body},
                         ensure_ascii=False)

    if dry_run:
        return f"inserted (dry · {file_path.name})"

    try:
        ensure_user(conn, user_id, region)
        ensure_agent(conn, agent_id, user_id, agent_type, project)
        conn.execute("""
            INSERT OR IGNORE INTO observations
            (obs_id, user_id, agent_id, ts, type, concept, drift, drift_signals,
             region, content_plain, indexed, source_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """, (
            obs_id, user_id, agent_id, mtime, type_, concept, drift,
            json.dumps(drift_signals, ensure_ascii=False), region, content,
            str(file_path),
        ))
        # Was it actually inserted (not skipped)?
        if conn.total_changes >= 1:  # this is loose · could be off if multi-stmt
            return "inserted"
        return "skipped"
    except sqlite3.IntegrityError:
        return "skipped"
    except Exception as e:
        return f"failed:{type(e).__name__}:{e}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=Path, default=DEFAULT_DB)
    p.add_argument("--projects", type=Path, default=DEFAULT_PROJECTS)
    p.add_argument("--user-id", default=os.environ.get("COMPASS_USER_ID", "u_local"))
    p.add_argument("--region", default=DEFAULT_REGION)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--limit", type=int, default=0)
    args = p.parse_args()

    if not args.dry_run:
        init_schema(args.db)
        print(f"[migrate] schema OK at {args.db}")

    counts = {"inserted": 0, "skipped": 0, "failed": 0}
    failures = []

    files = list(load_session_files(args.projects))
    if args.limit:
        files = files[:args.limit]
    print(f"[migrate] found {len(files)} memory files across projects")

    if args.dry_run:
        for project, fp in files[:5]:  # sample 5
            print(f"  · [{project}] {fp.name}")
        print(f"  ... ({len(files)} total · dry-run · use --limit 0 to do all)")
        return 0

    with db(args.db) as conn:
        for i, (project, fp) in enumerate(files):
            result = migrate_one(conn, fp, project, args.user_id, args.region)
            kind = result.split(":")[0]
            counts[kind] = counts.get(kind, 0) + 1
            if "failed" in kind:
                failures.append((fp, result))
        conn.commit()

    print(f"\n[migrate] complete:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    if failures:
        print(f"\nfailures (first 5):")
        for fp, r in failures[:5]:
            print(f"  · {fp.name}: {r}")

    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
