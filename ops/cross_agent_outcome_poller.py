"""compass · L4 cross-agent outcome poller.

Polls two read-only tables on the platform DB (nautilus_production) and turns
new rows into compass-recallable `session_*.md` observations, plus aggregate
drift signals per agent. This is the L4 substrate data pipeline that feeds L3
(Proof-of-Impact) and L1 (persona/drift) — without it, PoI emits 0 events.

Source tables (compass_sub · GRANT SELECT only):
  · engine_cycle_outcomes  (a2 · Soul engine cycle outcomes · PK cycle_id text)
  · agent_tool_calls       (b2 · every agent tool dispatch · PK id bigint · 125k+ rows)

Access path mirrors the verified probe: an ssh tunnel
  ssh -L <localport>:localhost:5432 cloud
then psycopg2 to 127.0.0.1:<localport>. compass_sub is not superuser (cannot set
GUCs like lc_messages). We connect with client_encoding=UTF8 — the platform DB
stores Chinese (UTF-8) data, so LATIN1 would raise UntranslatableCharacter on
read; UTF8 carries both the data and server error messages correctly.

Watermark (idempotent · incremental):
  · b2 by integer id  (WHERE id > last_b2_id ORDER BY id ASC LIMIT batch)
  · a2 by created_at  (WHERE created_at > last_a2_ts ORDER BY created_at ASC LIMIT batch)

Direct file write (no MCP call) · cron/background-safe · the BGE daemon scans
the memory dir anyway · matches platform_results_ingest_cron.py rationale.

Credentials: password read ONLY from the secret file (key:value format) · never
logged · never passed on a command line.
"""
from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------- config
SECRET_FILE = os.environ.get(
    "COMPASS_SOUL_DB_SECRET",
    str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache" / ".soul_db_secret"),
)
SSH_HOST = os.environ.get("COMPASS_SOUL_SSH_HOST", "cloud")
LOCAL_PORT = int(os.environ.get("COMPASS_SOUL_LOCAL_PORT", "5439"))
DB_USER = os.environ.get("COMPASS_SOUL_DB_USER", "compass_sub")
BATCH = int(os.environ.get("COMPASS_SOUL_BATCH", "500"))

STATE_FILE = Path(os.environ.get(
    "COMPASS_SOUL_WATERMARK",
    str(Path.home() / ".cache" / "compass" / "cross-agent-outcome-watermark.json"),
))
PROJECTS_BASE = Path.home() / ".claude" / "projects"
DEFAULT_PROJECT = os.environ.get("COMPASS_SOUL_INGEST_PROJECT", "C--Users-chunx")

# drift aggregation
DRIFT_MIN_SAMPLES = int(os.environ.get("COMPASS_SOUL_DRIFT_MIN_SAMPLES", "5"))
DRIFT_SUCCESS_FLOOR = float(os.environ.get("COMPASS_SOUL_DRIFT_FLOOR", "0.5"))


# ---------------------------------------------------------------- secret parse
def parse_secret(path: str) -> dict:
    """Parse a `key: value` secret file into a lowercased dict.

    Non `key:value` lines (e.g. a comment header) are ignored. Raises ValueError
    if no password key is present (a poller without a password is useless).
    """
    cfg: dict = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^\s*([A-Za-z_]+)\s*:\s*(.+?)\s*$", line)
            if m:
                cfg[m.group(1).lower()] = m.group(2)
    if "password" not in cfg:
        raise ValueError(f"secret file {path} has no 'password' key")
    return cfg


# ---------------------------------------------------------------------- slug
def _slug(s, n: int = 40) -> str:
    out = "".join(c if (c.isascii() and (c.isalnum() or c in "-_")) else "_"
                  for c in str(s)[:n])
    return out.strip("_") or "x"


def _ts_compact(value) -> str:
    """datetime or ISO string -> YYYYMMDD-HHMM (UTC-local stamp from the row)."""
    if isinstance(value, datetime):
        dt = value
    else:
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except Exception:
            return "00000000-0000"
    return dt.strftime("%Y%m%d-%H%M")


# ------------------------------------------------------- b2: agent_tool_calls
def build_b2_session_md(row: dict) -> tuple[str, str]:
    """agent_tool_calls row -> (filename, session_md). Deterministic filename."""
    rid = row.get("id", "x")
    agent_id = row.get("agent_id") or "unknown-agent"
    tool_name = row.get("tool_name") or "unknown-tool"
    success = bool(row.get("success"))
    args_summary = (row.get("args_summary") or "")[:400]
    output_summary = (row.get("output_summary") or "")[:600]
    elapsed_ms = row.get("elapsed_ms")
    phase = row.get("phase") or ""
    ts = row.get("ts")

    drift = "green" if success else "yellow"
    filename = f"session_{_ts_compact(ts)}_xacall_{_slug(agent_id, 24)}_{rid}.md"
    desc = (f"{agent_id} · {tool_name} · "
            f"{'ok' if success else 'FAIL'}").replace("\n", " ")[:200]
    ts_iso = ts.isoformat() if isinstance(ts, datetime) else str(ts)

    body = f"""---
name: cross-agent tool call · {agent_id} · {tool_name} · #{rid}
description: {desc}
type: cross-agent-tool-call
concept: l4-cross-agent-substrate
drift: {drift}
agent_type: {agent_id}
tool_name: {tool_name}
success: {str(success).lower()}
ingested_via: cross_agent_outcome_poller (L4 b2 agent_tool_calls)
thread_role: observation
thread_id: l4-agent-tool-calls
---

# Cross-agent tool call · {agent_id} · `{tool_name}` · #{rid}

**ts**: {ts_iso}
**agent**: `{agent_id}`
**tool**: `{tool_name}`
**success**: `{success}`
**phase**: `{phase}`
**elapsed_ms**: `{elapsed_ms}`
**drift**: `{drift}`

## args
{args_summary or '_(none)_'}

## output
{output_summary or '_(none)_'}
"""
    return filename, body


# ------------------------------------------------- a2: engine_cycle_outcomes
def build_a2_session_md(row: dict) -> tuple[str, str]:
    """engine_cycle_outcomes row -> (filename, session_md). Deterministic."""
    cycle_id = row.get("cycle_id") or "cyc_unknown"
    spec = (row.get("spec") or "")[:300]
    ship_status = row.get("ship_status") or "unknown"
    # keep raw (may be None) · None must not be read as a failed check (cry-wolf)
    semantic_pass = row.get("semantic_pass")
    tests_pass = row.get("tests_pass")
    composite_score = row.get("composite_score")
    drift_ratio = row.get("drift_ratio")
    git_sha = row.get("git_sha") or ""
    created_at = row.get("created_at")
    goal_source = row.get("goal_source") or ""
    fitness_delta = row.get("fitness_delta")

    # ship_status is the primary health signal (sem/tests are often NULL in
    # real data); an explicit False check is an additional negative signal.
    SUCCESS = ("success", "shipped", "ship", "done", "ok", "passed")
    healthy = (ship_status in SUCCESS
               and semantic_pass is not False
               and tests_pass is not False)
    drift = "green" if healthy else "yellow"
    filename = f"session_{_ts_compact(created_at)}_xcycle_{_slug(cycle_id, 32)}.md"
    desc = (f"cycle {cycle_id} · {ship_status} · "
            f"sem={semantic_pass} tests={tests_pass}").replace("\n", " ")[:200]
    created_iso = created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)

    body = f"""---
name: cross-agent cycle outcome · {cycle_id}
description: {desc}
type: cross-agent-cycle-outcome
concept: l4-cross-agent-substrate
drift: {drift}
agent_type: platform-soul-engine
ship_status: {ship_status}
composite_score: {composite_score}
ingested_via: cross_agent_outcome_poller (L4 a2 engine_cycle_outcomes)
thread_role: observation
thread_id: l4-cycle-outcomes
---

# Cross-agent cycle outcome · {cycle_id}

**created_at**: {created_iso}
**ship_status**: `{ship_status}`
**semantic_pass**: `{semantic_pass}` · **tests_pass**: `{tests_pass}`
**composite_score**: `{composite_score}` · **drift_ratio**: `{drift_ratio}`
**fitness_delta**: `{fitness_delta}` · **goal_source**: `{goal_source}`
**git_sha**: `{git_sha}`
**drift**: `{drift}`

## spec
{spec or '_(none)_'}
"""
    return filename, body


# -------------------------------------------------------- drift aggregation
def compute_drift_signal(agent_id: str, rows: list) -> dict:
    """Rolling success-rate signal for one agent across recent tool calls.

    Alerts only when there are enough samples (>= DRIFT_MIN_SAMPLES) AND the
    success rate falls below DRIFT_SUCCESS_FLOOR — deliberately conservative to
    avoid the cry-wolf failure mode (n=1 never alerts).
    """
    n = len(rows)
    successes = sum(1 for r in rows if bool(r.get("success")))
    rate = (successes / n) if n else 1.0
    alert = (n >= DRIFT_MIN_SAMPLES) and (rate < DRIFT_SUCCESS_FLOOR)
    return {"agent_id": agent_id, "n": n, "successes": successes,
            "success_rate": rate, "alert": alert}


# -------------------------------------------------------------- watermark io
def load_watermark(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        return {"last_b2_id": 0, "last_a2_ts": None, "ingested": 0}
    try:
        wm = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"last_b2_id": 0, "last_a2_ts": None, "ingested": 0}
    wm.setdefault("last_b2_id", 0)
    wm.setdefault("last_a2_ts", None)
    wm.setdefault("ingested", 0)
    return wm


def save_watermark(path: str, wm: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(wm, indent=2, default=str), encoding="utf-8")


# ------------------------------------------------------------------ db layer
@contextmanager
def db_connection(cfg: dict, local_port: int = LOCAL_PORT):
    """Open ssh tunnel + psycopg2 read-only connection · tear both down."""
    import psycopg2  # local import · pure functions importable without driver

    remote_host = cfg.get("host", "localhost")
    remote_port = cfg.get("port", "5432")
    dbname = cfg.get("dbname", "nautilus_production")

    tunnel = subprocess.Popen(
        ["ssh", "-N", "-o", "ExitOnForwardFailure=yes", "-o", "ConnectTimeout=10",
         "-L", f"{local_port}:{remote_host}:{remote_port}", SSH_HOST],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    conn = None
    try:
        opened = False
        for _ in range(60):
            if tunnel.poll() is not None:
                break
            try:
                with socket.create_connection(("127.0.0.1", local_port), timeout=0.5):
                    opened = True
                    break
            except OSError:
                time.sleep(0.25)
        if not opened:
            err = tunnel.stderr.read().decode("utf-8", "replace") if tunnel.stderr else ""
            raise RuntimeError(f"ssh tunnel did not open: {err[:200]}")
        conn = psycopg2.connect(
            host="127.0.0.1", port=local_port, dbname=dbname,
            user=DB_USER, password=cfg["password"],
            connect_timeout=10, client_encoding="UTF8")
        conn.set_session(readonly=True, autocommit=True)
        yield conn
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass
        tunnel.terminate()
        try:
            tunnel.wait(timeout=5)
        except Exception:
            tunnel.kill()


def _fetch_b2(conn, last_id: int, batch: int = BATCH) -> list:
    cols = ["id", "agent_id", "tool_name", "args_summary", "output_summary",
            "success", "elapsed_ms", "ts", "phase"]
    cur = conn.cursor()
    cur.execute(
        f"SELECT {', '.join(cols)} FROM agent_tool_calls "
        "WHERE id > %s ORDER BY id ASC LIMIT %s", (last_id, batch))
    return [dict(zip(cols, r)) for r in cur.fetchall()]


def _fetch_a2(conn, last_ts, batch: int = BATCH) -> list:
    cols = ["cycle_id", "spec", "ship_status", "semantic_pass", "tests_pass",
            "actual_lines_added", "actual_lines_removed", "drift_ratio",
            "composite_score", "git_sha", "created_at", "goal_source", "fitness_delta"]
    cur = conn.cursor()
    if last_ts:
        cur.execute(
            f"SELECT {', '.join(cols)} FROM engine_cycle_outcomes "
            "WHERE created_at > %s ORDER BY created_at ASC LIMIT %s", (last_ts, batch))
    else:
        cur.execute(
            f"SELECT {', '.join(cols)} FROM engine_cycle_outcomes "
            "ORDER BY created_at ASC LIMIT %s", (batch,))
    return [dict(zip(cols, r)) for r in cur.fetchall()]


# ----------------------------------------------------------------------- main
def main() -> int:
    try:
        cfg = parse_secret(SECRET_FILE)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"secret unavailable · {e}\n")
        return 0  # not an error · credential simply not provisioned here

    dry_run = "--dry-run" in sys.argv
    wm = load_watermark(str(STATE_FILE))
    mem_dir = PROJECTS_BASE / DEFAULT_PROJECT / "memory"

    written = 0
    new_b2_id = wm["last_b2_id"]
    new_a2_ts = wm["last_a2_ts"]
    by_agent: dict = {}

    try:
        with db_connection(cfg) as conn:
            b2_rows = _fetch_b2(conn, wm["last_b2_id"])
            a2_rows = _fetch_a2(conn, wm["last_a2_ts"])
    except Exception as e:
        sys.stderr.write(f"db poll failed · {type(e).__name__}: {str(e)[:200]}\n")
        return 1

    if not dry_run:
        mem_dir.mkdir(parents=True, exist_ok=True)

    for row in b2_rows:
        fn, content = build_b2_session_md(row)
        if not dry_run:
            (mem_dir / fn).write_text(content, encoding="utf-8")
        written += 1
        new_b2_id = max(new_b2_id, int(row["id"]))
        by_agent.setdefault(row.get("agent_id") or "unknown", []).append(row)

    for row in a2_rows:
        fn, content = build_a2_session_md(row)
        if not dry_run:
            (mem_dir / fn).write_text(content, encoding="utf-8")
        written += 1
        ca = row.get("created_at")
        ca_iso = ca.isoformat() if isinstance(ca, datetime) else str(ca)
        if new_a2_ts is None or ca_iso > new_a2_ts:
            new_a2_ts = ca_iso

    signals = [compute_drift_signal(a, rows) for a, rows in by_agent.items()]
    alerts = [s for s in signals if s["alert"]]

    if not dry_run:
        wm["last_b2_id"] = new_b2_id
        wm["last_a2_ts"] = new_a2_ts
        wm["ingested"] = int(wm.get("ingested", 0)) + written
        save_watermark(str(STATE_FILE), wm)

    print(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} · "
          f"b2={len(b2_rows)} a2={len(a2_rows)} written={written} "
          f"last_b2_id={new_b2_id} drift_alerts={len(alerts)}"
          + (" · DRY-RUN" if dry_run else ""))
    for s in alerts:
        print(f"  DRIFT ALERT · agent={s['agent_id']} "
              f"success_rate={s['success_rate']:.2f} n={s['n']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
