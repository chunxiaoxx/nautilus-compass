"""compass · L3 PoI reconcile runner · closes the recursive loop.

Joins recall-time PoI candidates (poi_candidates.jsonl · written by the daemon
recall path) with real agent outcomes (agent_tool_calls · via the same ssh
tunnel + read-only compass_sub creds as the cross-agent poller) and settles each
match into a full PoI event that credits cumulative_impact on the cited memory.

  recall surfaces memory → candidate → agent acts → outcome (L4) → reconcile →
  cumulative_impact credited → recall boost_top_k uses it next time.

Pure join logic lives in proof/poi_reconciler.py (unit-tested). This file is the
runtime glue: load candidates, fetch outcomes for the candidates' actors, run
the reconcile, persist the settled-key state. Manual/cron-safe · idempotent ·
NO LLM. Reuses ops/cross_agent_outcome_poller.py for the DB connection.
"""
from __future__ import annotations

import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# reuse the poller's verified DB connection + secret parsing
_spec = importlib.util.spec_from_file_location(
    "cross_agent_outcome_poller", _HERE / "cross_agent_outcome_poller.py")
_poller = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_poller)

sys.path.insert(0, str(_HERE.parent))
from proof import poi_reconciler as R  # noqa: E402
from proof import poi_credit_store as CS  # noqa: E402

CANDIDATE_DIR = Path(os.environ.get(
    "COMPASS_POI_CACHE_DIR",
    str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache")))
WINDOW_S = int(os.environ.get("COMPASS_POI_RECONCILE_WINDOW_S", str(R.DEFAULT_WINDOW_S)))
# memory_root: where cited memory files live (legacy frontmatter path · unused by main)
MEMORY_ROOT = os.environ.get("COMPASS_POI_MEMORY_ROOT", "")
# atomic snapshot of the central poi_credit table · the daemon reads this for boost
SNAPSHOT_PATH = Path(os.environ.get(
    "COMPASS_POI_CREDIT_SNAPSHOT", str(CANDIDATE_DIR / "poi_credit_cache.json")))


def settle_and_snapshot(conn, pending, outcomes, settled_keys, *, snapshot_path,
                        window_s=WINDOW_S, placeholder="%s", dry_run=False):
    """Settle pending candidates into the central poi_credit table, then export
    the full credit table as an atomic snapshot the daemon reads for boost.
    Returns the reconcile_central result dict.

    dry_run=True · reconcile counts what WOULD settle but writes nothing to the DB;
    the snapshot write is skipped entirely (truly read-only)."""
    res = R.reconcile_central(pending, outcomes, conn=conn, settled_keys=settled_keys,
                              window_seconds=window_s, placeholder=placeholder,
                              dry_run=dry_run)
    if dry_run:
        return res
    credits = CS.fetch_all_credits(conn)
    CS.write_snapshot_atomic(snapshot_path, credits)
    return res


def _fetch_outcomes_for(conn, actors: list, since_iso: str, window_s: int) -> list:
    """agent_tool_calls outcomes for the candidate actors, from since_iso forward."""
    if not actors:
        return []
    cur = conn.cursor()
    cur.execute(
        "SELECT agent_id, success, ts FROM agent_tool_calls "
        "WHERE agent_id = ANY(%s) AND ts > %s ORDER BY ts ASC",
        (list(actors), since_iso))
    return [{"agent_id": r[0], "success": r[1],
             "ts": r[2].isoformat() if hasattr(r[2], "isoformat") else str(r[2])}
            for r in cur.fetchall()]


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    cand_path = CANDIDATE_DIR / R.CANDIDATE_SIDECAR
    settled_path = CANDIDATE_DIR / R.SETTLED_STATE

    candidates = R.load_candidates(cand_path)
    if not candidates:
        print(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} · "
              f"no candidates at {cand_path} · nothing to reconcile")
        return 0

    settled_keys = R.load_settled(settled_path)
    pending = [c for c in candidates if R.central_candidate_key(c) not in settled_keys]
    if not pending:
        print(f"all {len(candidates)} candidates already settled")
        return 0

    actors = sorted({c.get("actor") for c in pending if c.get("actor")})
    since = min(str(c.get("ts", "")) for c in pending)
    memory_root = Path(MEMORY_ROOT) if MEMORY_ROOT else None

    # Phase 1 central credit REQUIRES the cloud DB · reconcile_central writes to
    # the poi_credit table (not frontmatter). No secret → no settle, honest skip.
    try:
        cfg = _poller.parse_secret(_poller.SECRET_FILE)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(
            f"reconcile skipped · DB secret unavailable · central credit needs the "
            f"cloud DB · {e}\n")
        return 0

    res = None
    n_local = 0
    n_outcomes = 0
    try:
        with _poller.db_connection(cfg) as conn:
            # Platform outcomes (agent_tool_calls) · credits platform agents.
            outcomes: list = list(_fetch_outcomes_for(conn, actors, since, WINDOW_S))

            # Path B · local outcomes from the user's own session_*.md drift
            # signal · lets local (anon/unknown) recalls self-settle. Gathered
            # BEFORE the settle so they credit via the same conn.
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

            n_outcomes = len(outcomes)
            if not outcomes:
                print("no outcomes (platform + local) · nothing to settle yet")
                return 0

            work_keys = set(settled_keys) if dry_run else settled_keys
            res = settle_and_snapshot(conn, pending, outcomes, work_keys,
                                      snapshot_path=SNAPSHOT_PATH, window_s=WINDOW_S,
                                      placeholder="%s", dry_run=dry_run)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(
            f"reconcile skipped · DB connect failed · central credit needs the "
            f"cloud DB · {e}\n")
        return 0
    except Exception as e:
        sys.stderr.write(f"reconcile failed · {type(e).__name__}: {str(e)[:200]}\n")
        return 1

    if not dry_run:
        R.save_settled(settled_path, settled_keys)

    print(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} · "
          f"candidates={len(candidates)} pending={len(pending)} "
          f"actors={len(actors)} outcomes={n_outcomes} (local={n_local}) "
          f"settled={res['settled']} no_match={res['skipped_no_match']} "
          f"selfcite={res['skipped_selfcite']}"
          + (" · DRY-RUN" if dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
