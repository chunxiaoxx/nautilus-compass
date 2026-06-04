# PoI writer role tightening (Phase 2) — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move `compass.poi_credit` writes off the shared read-only `compass_sub` account onto a dedicated least-privilege `poi_writer` role, with the reconcile cron using one ssh tunnel and two connections (compass_sub read / poi_writer write).

**Architecture:** Additive SQL 005 creates `poi_writer` + grants (does not touch the running reconciler). The poller's `db_connection` is refactored into a reusable tunnel CM + a `connect_via` helper so one tunnel can host two connections under different roles. The cron loads a separate `.poi_writer_db_secret`, fetches outcomes on the read conn, settles/snapshots on the write conn. Only after a verified e2e run does SQL 006 REVOKE compass_sub's write + compass-schema access, gated by a negative permission test.

**Tech Stack:** Python 3.13 (psycopg2 probe; pure logic importable without driver), PostgreSQL (nautilus_production, cloud, via ssh tunnel), pytest + sqlite in-memory mocks (placeholder `?`).

**Design ref:** `docs/plans/2026-06-04-poi-writer-role-tightening-design.md`

**Conventions (match existing):**
- Tests load ops modules via `importlib.util.spec_from_file_location` (see `tests/test_poi_reconcile_cron_wire.py`).
- sqlite mock table DDL: `CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, cumulative_impact REAL NOT NULL DEFAULT 0, event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)`.
- Run a single test: `python -m pytest tests/test_X.py::test_Y -v` (Bash tool — PowerShell is broken here).
- Secret format: `key: value` lines, parsed by `_poller.parse_secret`.

**R-guardrails:** Production DDL. SQL 006 (REVOKE) runs ONLY after step-by-step e2e verify (Task 7). Each task commits specific files (no `-A`, no push, no amend). main is clean now.

---

### Task 1: SQL 005 — additive poi_writer role (no compass_sub change)

**Files:**
- Create: `sql/005_poi_writer_role.sql`

**Step 1: Write the SQL file**

```sql
-- 005 · PoI Phase 2 · dedicated poi_writer role (ADDITIVE — does not touch
-- compass_sub). Apply on cloud (nautilus_production) AFTER 004. Pairs with
-- 006_poi_writer_revoke_compass_sub.sql, which is run ONLY after the split code
-- is deployed and a real reconcile run is verified.
-- Reference: docs/plans/2026-06-04-poi-writer-role-tightening-design.md §1/§4
--
-- The password is a placeholder. Provision the real one out-of-band and store it
-- in ~/.claude/plugins/nautilus-compass/.cache/.poi_writer_db_secret (never commit
-- a real password). To set/rotate: ALTER ROLE poi_writer PASSWORD '...';

DO $$
BEGIN
   IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'poi_writer') THEN
      CREATE ROLE poi_writer LOGIN PASSWORD 'CHANGE_ME_PROVISION_OUT_OF_BAND';
   END IF;
END
$$;

GRANT USAGE ON SCHEMA compass TO poi_writer;
GRANT SELECT, INSERT, UPDATE ON compass.poi_credit TO poi_writer;
```

**Step 2: Add a cheap guard test that the file exists and has the key statements**

File: `tests/test_poi_writer_sql.py`

```python
from pathlib import Path

_SQL = Path(__file__).resolve().parents[1] / "sql"


def test_005_creates_role_and_grants_writer_only():
    txt = (_SQL / "005_poi_writer_role.sql").read_text(encoding="utf-8")
    assert "CREATE ROLE poi_writer" in txt
    assert "GRANT USAGE ON SCHEMA compass TO poi_writer" in txt
    assert "GRANT SELECT, INSERT, UPDATE ON compass.poi_credit TO poi_writer" in txt
    # 005 is additive: it must NOT revoke or grant anything on compass_sub
    assert "compass_sub" not in txt


def test_006_revokes_compass_sub_write_and_usage():
    txt = (_SQL / "006_poi_writer_revoke_compass_sub.sql").read_text(encoding="utf-8")
    assert "REVOKE INSERT, UPDATE ON compass.poi_credit FROM compass_sub" in txt
    assert "REVOKE USAGE ON SCHEMA compass FROM compass_sub" in txt
```

**Step 3: Run — `test_006...` fails (file not yet created), `test_005...` passes**

Run: `python -m pytest tests/test_poi_writer_sql.py -v`
Expected: `test_005...` PASS, `test_006...` FAIL (FileNotFoundError).

**Step 4: Write SQL 006 (REVOKE — staged, NOT applied until Task 7)**

File: `sql/006_poi_writer_revoke_compass_sub.sql`

```sql
-- 006 · PoI Phase 2 · revoke compass_sub's write + compass-schema access.
-- Run ONLY after 005 is applied, the poi_writer secret is provisioned, the split
-- code is deployed, and a real reconcile run is verified green (the writer
-- authenticates as poi_writer and settles/snapshots correctly).
-- Reference: docs/plans/2026-06-04-poi-writer-role-tightening-design.md §4
--
-- Rollback to Phase 1 if the reconciler breaks after this:
--   GRANT INSERT, UPDATE ON compass.poi_credit TO compass_sub;
--   GRANT USAGE ON SCHEMA compass TO compass_sub;

REVOKE INSERT, UPDATE ON compass.poi_credit FROM compass_sub;
REVOKE USAGE ON SCHEMA compass FROM compass_sub;
```

**Step 5: Run — both pass**

Run: `python -m pytest tests/test_poi_writer_sql.py -v`
Expected: both PASS.

**Step 6: Commit**

```bash
git add sql/005_poi_writer_role.sql sql/006_poi_writer_revoke_compass_sub.sql tests/test_poi_writer_sql.py
git commit -m "feat(sql): poi_writer role 005 (additive) + 006 (compass_sub revoke, staged)"
```

---

### Task 2: Refactor poller db_connection → tunnel CM + connect_via (backward compatible)

**Files:**
- Modify: `ops/cross_agent_outcome_poller.py` (the `db_connection` CM, ~line 302-349)
- Test: `tests/test_cross_agent_poller.py` (add)

**Step 1: Write the failing test — connect_via passes the right user/password**

Add to `tests/test_cross_agent_poller.py` (it already loads the module as `poller`):

```python
def test_connect_via_passes_user_and_password(monkeypatch):
    poller = _load()  # match the existing loader helper name in this file
    captured = {}

    class _FakeConn:
        def set_session(self, **kw): captured["session"] = kw
        def close(self): pass

    def _fake_connect(**kw):
        captured.update(kw)
        return _FakeConn()

    import sys
    fake_pg = type(sys)("psycopg2")
    fake_pg.connect = _fake_connect
    monkeypatch.setitem(sys.modules, "psycopg2", fake_pg)

    conn = poller.connect_via(5439, {"password": "PW", "dbname": "db"},
                              user="poi_writer", password="WPW", readonly=False)
    assert captured["user"] == "poi_writer"
    assert captured["password"] == "WPW"
    assert captured["session"] == {"readonly": False, "autocommit": True}
```

> NOTE: check the existing loader helper in `tests/test_cross_agent_poller.py` (it
> may be named `_load`/`_poller`/inline). Reuse it; do not add a second loader.

**Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_cross_agent_poller.py::test_connect_via_passes_user_and_password -v`
Expected: FAIL (`module has no attribute 'connect_via'`).

**Step 3: Refactor db_connection into three pieces**

In `ops/cross_agent_outcome_poller.py`, replace the single `db_connection` CM with:

```python
@contextmanager
def ssh_tunnel(cfg: dict, local_port: int = LOCAL_PORT):
    """Open ssh -L tunnel to the platform DB, wait for the port, tear it down.
    Yields the local_port once the forward is accepting connections."""
    remote_host = cfg.get("host", "localhost")
    remote_port = cfg.get("port", "5432")
    tunnel = subprocess.Popen(
        ["ssh", "-N", "-o", "ExitOnForwardFailure=yes", "-o", "ConnectTimeout=10",
         "-L", f"{local_port}:{remote_host}:{remote_port}", SSH_HOST],
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
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
        yield local_port
    finally:
        tunnel.terminate()
        try:
            tunnel.wait(timeout=5)
        except Exception:
            tunnel.kill()


def connect_via(local_port: int, cfg: dict, *, user: str = DB_USER,
                password: str | None = None, readonly: bool = True):
    """psycopg2 connect to the already-open tunnel port as `user`.
    Caller owns closing the returned connection."""
    import psycopg2
    conn = psycopg2.connect(
        host="127.0.0.1", port=local_port, dbname=cfg.get("dbname", "nautilus_production"),
        user=user, password=password if password is not None else cfg["password"],
        connect_timeout=10, client_encoding="UTF8")
    conn.set_session(readonly=readonly, autocommit=True)
    return conn


@contextmanager
def db_connection(cfg: dict, local_port: int = LOCAL_PORT, readonly: bool = True,
                  user: str = DB_USER, password: str | None = None):
    """Backward-compat: one tunnel, one connection (the original single-conn API).
    Existing callers (poller.main, notifier) keep working unchanged."""
    with ssh_tunnel(cfg, local_port):
        conn = connect_via(local_port, cfg, user=user, password=password, readonly=readonly)
        try:
            yield conn
        finally:
            try:
                conn.close()
            except Exception:
                pass
```

> Keep `from contextlib import contextmanager` (already imported). The `str | None`
> annotation is fine on 3.13.

**Step 4: Run — new test passes, existing poller tests still green**

Run: `python -m pytest tests/test_cross_agent_poller.py -v`
Expected: all PASS (old + new).

**Step 5: Commit**

```bash
git add ops/cross_agent_outcome_poller.py tests/test_cross_agent_poller.py
git commit -m "refactor: split db_connection into ssh_tunnel + connect_via (backward compat)"
```

---

### Task 3: poi_writer secret loading in the cron (honest skip when absent)

**Files:**
- Modify: `ops/poi_reconcile_cron.py` (add secret path const + loader near the other config consts, ~line 36-44)
- Test: `tests/test_poi_reconcile_cron_roles.py` (create)

**Step 1: Write the failing test**

File: `tests/test_poi_reconcile_cron_roles.py`

```python
import importlib.util
from pathlib import Path

_HERE = Path(__file__).resolve().parents[1]


def _load_cron():
    spec = importlib.util.spec_from_file_location(
        "poi_reconcile_cron", _HERE / "ops" / "poi_reconcile_cron.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_load_writer_cfg_reads_secret(tmp_path):
    cron = _load_cron()
    sf = tmp_path / ".poi_writer_db_secret"
    sf.write_text("password: WPW\n", encoding="utf-8")
    cfg = cron.load_writer_cfg(str(sf))
    assert cfg["password"] == "WPW"


def test_load_writer_cfg_missing_returns_none(tmp_path):
    cron = _load_cron()
    cfg = cron.load_writer_cfg(str(tmp_path / "nope"))
    assert cfg is None
```

**Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_poi_reconcile_cron_roles.py -v`
Expected: FAIL (`module has no attribute 'load_writer_cfg'`).

**Step 3: Implement**

In `ops/poi_reconcile_cron.py`, after the existing config consts (near line 44), add:

```python
# Phase 2: dedicated poi_writer credential (separate file from the read secret).
# Missing file → honest skip (same as the cross_agent_outcome_poller no-secret path).
POI_WRITER_SECRET = os.environ.get(
    "COMPASS_POI_WRITER_SECRET",
    str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache"
        / ".poi_writer_db_secret"))


def load_writer_cfg(path: str = POI_WRITER_SECRET):
    """Parse the poi_writer secret, or None if absent (honest skip)."""
    try:
        return _poller.parse_secret(path)
    except (FileNotFoundError, ValueError):
        return None
```

**Step 4: Run — passes**

Run: `python -m pytest tests/test_poi_reconcile_cron_roles.py -v`
Expected: both PASS.

**Step 5: Commit**

```bash
git add ops/poi_reconcile_cron.py tests/test_poi_reconcile_cron_roles.py
git commit -m "feat: poi_writer secret loader in reconcile cron (honest skip when absent)"
```

---

### Task 4: Extract reconcile_with_conns (read conn / write conn responsibility split)

**Files:**
- Modify: `ops/poi_reconcile_cron.py` (extract orchestration from `main`)
- Test: `tests/test_poi_reconcile_cron_roles.py` (add)

**Step 1: Write the failing test — outcomes read on read_conn, UPSERT on write_conn**

Add to `tests/test_poi_reconcile_cron_roles.py`:

```python
import sqlite3

CREATE = ("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, cumulative_impact REAL "
          "NOT NULL DEFAULT 0, event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")


def _cand(actor="a1", project="proj", memory="m.md", creator="other",
          ts="2026-06-03T00:00:00+00:00"):
    return {"kind": "candidate", "actor": actor, "project": project, "memory": memory,
            "creator": creator, "query_hash": "q", "ts": ts, "rank": 0, "score": 0.9}


class _SpyReadConn:
    """Stands in for the compass_sub read conn. Records SQL, serves outcomes,
    and raises if anyone tries to write poi_credit through it."""
    def __init__(self, rows):
        self.rows = rows
        self.sql = []

    def cursor(self):
        outer = self

        class _Cur:
            def execute(self, q, params=None):
                outer.sql.append(q)
                if "poi_credit" in q.lower():
                    raise AssertionError("read conn must not touch poi_credit")
                self._rows = outer.rows if "agent_tool_calls" in q.lower() else []
            def fetchall(self):
                return self._rows
        return _Cur()


def test_reconcile_with_conns_splits_read_and_write(tmp_path):
    cron = _load_cron()
    # write conn = real sqlite poi_credit table
    write = sqlite3.connect(":memory:"); write.execute(CREATE)
    # read conn = spy serving one agent_tool_calls outcome row (agent_id, success, ts)
    read = _SpyReadConn([("a1", True, "2026-06-03T00:10:00+00:00")])
    snap = tmp_path / "poi_credit_cache.json"

    res = cron.reconcile_with_conns(
        read, write, [_cand()], set(), snapshot_path=snap, placeholder="?")

    assert res["settled"] == 1
    # the outcome query went to the READ conn
    assert any("agent_tool_calls" in q.lower() for q in read.sql)
    # the credit landed in the WRITE conn
    row = write.execute(
        "SELECT cumulative_impact FROM poi_credit WHERE memory_key='proj/m.md'").fetchone()
    assert row and row[0] > 0
```

> The spy returns rows as tuples `(agent_id, success, ts)` to match
> `_fetch_outcomes_for`'s `SELECT agent_id, success, ts` shape. If the real ts is
> a datetime in prod, `_fetch_outcomes_for` already handles `.isoformat()`; the
> string here passes through `str(r[2])`.

**Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_poi_reconcile_cron_roles.py::test_reconcile_with_conns_splits_read_and_write -v`
Expected: FAIL (`no attribute 'reconcile_with_conns'`).

**Step 3: Implement — extract the orchestration**

In `ops/poi_reconcile_cron.py`, add a function that takes the two connections explicitly (read for outcomes, write for settle+snapshot). Reuse the existing `_fetch_outcomes_for`, `settle_and_snapshot`, and local-outcome logic:

```python
def reconcile_with_conns(read_conn, write_conn, pending, settled_keys, *,
                         snapshot_path, window_s=WINDOW_S, placeholder="%s",
                         dry_run=False, memory_root=None):
    """Read outcomes on read_conn (compass_sub · agent_tool_calls in public),
    settle + snapshot on write_conn (poi_writer · compass.poi_credit).
    Returns (res, n_outcomes, n_local) or None if there is nothing to settle."""
    actors = sorted({c.get("actor") for c in pending if c.get("actor")})
    since = min(str(c.get("ts", "")) for c in pending)

    outcomes = list(_fetch_outcomes_for(read_conn, actors, since, window_s))
    n_local = 0
    if memory_root and os.environ.get("COMPASS_POI_LOCAL_OUTCOMES", "1") != "0":
        try:
            from proof import local_outcomes as _LO
            for actor in actors:
                lo = _LO.local_outcomes(memory_root, actor, since_iso=since)
                outcomes += lo
                n_local += len(lo)
        except Exception as e:
            sys.stderr.write(
                f"local outcomes skipped · {type(e).__name__}: {str(e)[:160]}\n")

    if not outcomes:
        return None, 0, n_local

    work_keys = set(settled_keys) if dry_run else settled_keys
    res = settle_and_snapshot(write_conn, pending, outcomes, work_keys,
                              snapshot_path=snapshot_path, window_s=window_s,
                              placeholder=placeholder, dry_run=dry_run)
    return res, len(outcomes), n_local
```

Do NOT rewire `main` yet (Task 5). Just add the function so the unit test passes.

**Step 4: Run — passes**

Run: `python -m pytest tests/test_poi_reconcile_cron_roles.py -v`
Expected: all PASS.

**Step 5: Commit**

```bash
git add ops/poi_reconcile_cron.py tests/test_poi_reconcile_cron_roles.py
git commit -m "feat: reconcile_with_conns splits read (compass_sub) and write (poi_writer) conns"
```

---

### Task 5: Wire main() — one tunnel, two connections; honest skip without writer secret

**Files:**
- Modify: `ops/poi_reconcile_cron.py` (`main`, ~line 79-166)
- Test: `tests/test_poi_reconcile_cron_roles.py` (add)

**Step 1: Write the failing test — main honest-skips when writer secret absent**

Add to `tests/test_poi_reconcile_cron_roles.py`:

```python
def test_main_skips_when_writer_secret_absent(tmp_path, monkeypatch, capsys):
    cron = _load_cron()
    # candidates present so we get past the early "no candidates" return
    cand_dir = tmp_path / "cache"; cand_dir.mkdir()
    import json
    (cand_dir / cron.R.CANDIDATE_SIDECAR).write_text(
        json.dumps(_cand()) + "\n", encoding="utf-8")
    monkeypatch.setattr(cron, "CANDIDATE_DIR", cand_dir)
    # read secret present, writer secret absent
    monkeypatch.setattr(cron._poller, "SECRET_FILE", str(tmp_path / "read_secret"))
    (tmp_path / "read_secret").write_text("password: RPW\n", encoding="utf-8")
    monkeypatch.setattr(cron, "POI_WRITER_SECRET", str(tmp_path / "nope_writer"))

    rc = cron.main()
    assert rc == 0
    assert "poi_writer secret" in capsys.readouterr().err.lower()
```

> Confirm the const names against the real module after Task 3/4 (`CANDIDATE_DIR`,
> `R.CANDIDATE_SIDECAR`, `_poller.SECRET_FILE`, `POI_WRITER_SECRET`). Adjust the
> monkeypatch targets if a name differs.

**Step 2: Run to verify it fails**

Run: `python -m pytest tests/test_poi_reconcile_cron_roles.py::test_main_skips_when_writer_secret_absent -v`
Expected: FAIL (main still uses the old single-conn path / no writer-secret check).

**Step 3: Rewire main() to open one tunnel + two conns**

Replace the DB section of `main()` (currently the `try: cfg = _poller.parse_secret(...)` through the single `with _poller.db_connection(...)` block) with:

```python
    # read credential (compass_sub) — same as before
    try:
        read_cfg = _poller.parse_secret(_poller.SECRET_FILE)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(
            f"reconcile skipped · read DB secret unavailable · {e}\n")
        return 0

    # write credential (poi_writer) — Phase 2 least privilege. Absent → honest skip.
    write_cfg = load_writer_cfg()
    if write_cfg is None:
        sys.stderr.write(
            "reconcile skipped · poi_writer secret unavailable · central credit "
            "needs the dedicated writer role (Phase 2)\n")
        return 0

    memory_root = Path(MEMORY_ROOT) if MEMORY_ROOT else None
    res = None
    n_outcomes = 0
    n_local = 0
    try:
        with _poller.ssh_tunnel(read_cfg, _poller.LOCAL_PORT) as port:
            read_conn = _poller.connect_via(
                port, read_cfg, user=_poller.DB_USER, readonly=True)
            # write conn authenticates as poi_writer; readonly mirrors dry_run so a
            # dry-run physically cannot mutate the cloud.
            write_conn = _poller.connect_via(
                port, write_cfg, user="poi_writer",
                password=write_cfg["password"], readonly=dry_run)
            try:
                write_conn.cursor().execute("SET search_path TO compass, public")
                out = reconcile_with_conns(
                    read_conn, write_conn, pending, settled_keys,
                    snapshot_path=SNAPSHOT_PATH, window_s=WINDOW_S,
                    placeholder="%s", dry_run=dry_run, memory_root=memory_root)
                if out is None or out[0] is None:
                    print("no outcomes (platform + local) · nothing to settle yet")
                    return 0
                res, n_outcomes, n_local = out
            finally:
                for c in (read_conn, write_conn):
                    try:
                        c.close()
                    except Exception:
                        pass
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        sys.stderr.write(f"reconcile skipped · DB connect failed · {e}\n")
        return 0
    except Exception as e:
        sys.stderr.write(f"reconcile failed · {type(e).__name__}: {str(e)[:200]}\n")
        return 1
```

Remove the now-dead inline `_fetch_outcomes_for`/`settle_and_snapshot` calls in
`main` (they moved into `reconcile_with_conns`). Keep the post-block
`R.save_settled` + final `print(...)` summary, which reference `res`, `n_outcomes`,
`n_local`.

> `_fetch_outcomes_for` and `settle_and_snapshot` stay as module-level functions
> (still used by `reconcile_with_conns` and the existing wire test).

**Step 4: Run — full reconcile-cron suite green**

Run: `python -m pytest tests/test_poi_reconcile_cron_wire.py tests/test_poi_reconcile_cron_roles.py -v`
Expected: all PASS (old wire tests for `settle_and_snapshot` unchanged + new role tests).

**Step 5: Full suite regression**

Run: `python -m pytest -q`
Expected: all green (no other caller of the changed functions broke).

**Step 6: Commit**

```bash
git add ops/poi_reconcile_cron.py tests/test_poi_reconcile_cron_roles.py
git commit -m "feat: reconcile main uses one tunnel + compass_sub read / poi_writer write conns"
```

---

### Task 6: Update sql/004 TODO comment (Phase 2 done marker) + dry-run docs

**Files:**
- Modify: `sql/004_poi_credit.sql:16-17` (TODO comment)

**Step 1: Update the TODO**

Replace the `TODO(Phase 2)` comment block in `sql/004_poi_credit.sql` with a
pointer that Phase 1's compass_sub grant is superseded by 005/006:

```sql
-- Phase 1 reused compass_sub as the writer (below). Phase 2 (sql/005 + sql/006)
-- introduces a dedicated poi_writer role and REVOKEs compass_sub's write here.
-- After 006 is applied, the two GRANT lines below are historical (compass_sub is
-- read-only again). See docs/plans/2026-06-04-poi-writer-role-tightening-design.md.
```

(Leave the actual GRANT lines — they document the Phase-1 state and 006 revokes them; do not delete history.)

**Step 2: Commit**

```bash
git add sql/004_poi_credit.sql
git commit -m "docs(sql): mark 004 compass_sub grant superseded by Phase 2 poi_writer (005/006)"
```

---

### Task 7: Cloud e2e + staged REVOKE (MANUAL — gated, verification-before-completion)

> **NOT a unit-test task.** This is the production runbook. Do each step, verify
> its output, and STOP if anything is off. SQL 006 (REVOKE) runs only after step 4
> verifies. Probe with Python 3.13 (3.14 has no psycopg2). Upload files via
> `local Write tmp → single-line scp`, never multi-line heredoc.

**Step 1 — Apply SQL 005 (additive).** On cloud, as a superuser, run
`sql/005_poi_writer_role.sql`, then `ALTER ROLE poi_writer PASSWORD '<provisioned>'`.
Verify: `\du poi_writer` shows LOGIN; `\dp compass.poi_credit` shows poi_writer
has arw. The running reconciler is untouched → confirm it still settles on the
next cron tick (or run `python ops/poi_reconcile_cron.py --dry-run`).

**Step 2 — User provisions the secret.** Write the poi_writer password into
`~/.claude/plugins/nautilus-compass/.cache/.poi_writer_db_secret` (local) and the
cloud equivalent. **Pause here for the user** to provide/confirm the password.

**Step 3 — Deploy split code** to wherever the reconcile cron runs (plugin copy
+ cloud). Confirm the module imports (`python -c "import ops.poi_reconcile_cron"`
from repo root, or the importlib smoke).

**Step 4 — Verify a real run (writer = poi_writer):**
- `python ops/poi_reconcile_cron.py --dry-run` → settled count sane, no error,
  physically read-only.
- `python ops/poi_reconcile_cron.py` → `settled=N`, snapshot written, no error.
- Confirm the write authenticated as poi_writer (cloud: `SELECT usename FROM
  pg_stat_activity WHERE datname='nautilus_production'` during a run, or a
  temporary log line — remove after).
- **GATE:** only proceed if this run is green.

**Step 5 — Apply SQL 006 (REVOKE compass_sub write + compass USAGE).** Run
`sql/006_poi_writer_revoke_compass_sub.sql` as superuser.

**Step 6 — Closing verification (the whole point):**
- Reconciler still green: `python ops/poi_reconcile_cron.py` settles via poi_writer.
- **Negative test:** as compass_sub, attempt a write — expect `permission denied`:
  ```python
  # Python 3.13 + tunnel as compass_sub
  cur.execute("SET search_path TO compass, public")
  try:
      cur.execute("INSERT INTO poi_credit (memory_key, cumulative_impact, event_count) "
                  "VALUES ('__negtest__', 0, 0)")
      print("FAIL · compass_sub could still write")
  except Exception as e:
      print("OK · compass_sub denied:", str(e)[:120])  # expect 'permission denied'
  ```
  Expect `OK · ... permission denied for table poi_credit` (or for schema compass).
- Also confirm the daemon boost still works (snapshot regen cron unaffected — it
  reads the table via its own path; poi_writer/compass_sub split doesn't touch it,
  but spot-check the snapshot file refreshes).

**Step 7 — Record outcome** in a session memory: 005/006 applied, negative test
result, reconciler-still-green proof. Close any related note.

> Rollback at any point before step 5: nothing to undo (005 is additive). After
> step 5, if the reconciler breaks: `GRANT INSERT, UPDATE ON compass.poi_credit TO
> compass_sub; GRANT USAGE ON SCHEMA compass TO compass_sub;` → back to Phase 1.

---

## Done criteria

- [ ] SQL 005 (additive) + 006 (staged revoke) written, guard test green.
- [ ] db_connection refactored to ssh_tunnel + connect_via, backward compatible, all poller tests green.
- [ ] reconcile cron loads poi_writer secret (honest skip absent), uses read/write conn split.
- [ ] Full `pytest -q` green.
- [ ] (Manual/gated) 005 applied, secret provisioned, e2e verified, 006 applied, negative write test passes, reconciler still green.
