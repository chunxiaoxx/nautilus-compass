"""compass · FDE verdict-bus → task-level PoI settle runner (G-platform-spine live wire).

Reads the platform verdict-bus (`fde_verdicts` · FDE_VERDICT_BUS_CONTRACT.md) over
the SAME ssh tunnel + read-only compass_sub creds as the PoI reconciler, credits
task-level PoI (fde-capsule-<task_uid>) into compass.poi_credit, advances a
created_at watermark (no double-credit), and exports the atomic snapshot the
daemon reads for boost. The verdict = the EXTERNAL buyer-acceptance fitness
signal (anchor #3) — the only fitness that escapes the internal self-referential
economy.

GATED on G-cloud: until the platform applies the DDL + `GRANT SELECT ON
fde_verdicts TO compass_sub`, this skips HONESTLY (no secret → skip; missing
table / no grant → psycopg2 error → skip rc 0). Mirrors ops/poi_reconcile_cron.py.
Idempotent · cron-safe · NO LLM.

Run:
  python ops/fde_verdict_reconcile.py --dry-run   # read-only · verify the GRANT, settle nothing
  python ops/fde_verdict_reconcile.py             # settle + snapshot (needs write on compass.poi_credit)
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# reuse the poller's verified ssh-tunnel + compass_sub connection & secret parsing
_spec = importlib.util.spec_from_file_location(
    "cross_agent_outcome_poller", _HERE / "cross_agent_outcome_poller.py")
_poller = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_poller)

sys.path.insert(0, str(_HERE.parent))
from proof import fde_verdict_bus_reader as BUS  # noqa: E402
from proof import poi_credit_store as CS  # noqa: E402

CACHE_DIR = Path(os.environ.get(
    "COMPASS_POI_CACHE_DIR",
    str(Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache")))
WATERMARK_PATH = Path(os.environ.get(
    "COMPASS_FDE_VERDICT_WATERMARK", str(CACHE_DIR / "fde_verdict_watermark.json")))
SNAPSHOT_PATH = Path(os.environ.get(
    "COMPASS_POI_CREDIT_SNAPSHOT", str(CACHE_DIR / "poi_credit_cache.json")))


def load_since(path) -> "str | None":
    """Exclusive created_at watermark of the last settled verdict (None = start)."""
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8")).get("last_created_at")
    except (json.JSONDecodeError, OSError):
        return None


def save_since(path, last_created_at) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"last_created_at": last_created_at}, default=str),
                 encoding="utf-8")


def settle_once(conn, since, checklist_dir, placeholder="%s", dimension_for=None,
                project=BUS.DEFAULT_DIM_PROJECT):
    """One settle pass over the bus: task-level spine (fde-capsule-<uid>) AND —
    when `checklist_dir` is given — dimension-level PoI (fde-dim-<dim> joined to
    local checklists), both over the SAME `since` watermark. The task spine is the
    authoritative watermark (it reads every row; a missing checklist only skips
    that row's dimension credit, never the spine). Returns {task, dimension,
    last_created_at}."""
    task = BUS.from_fde_verdicts(conn, conn, since=since, placeholder=placeholder)
    if checklist_dir:
        dimension = BUS.credit_dimensions_from_bus(
            conn, conn, checklist_dir, since=since, placeholder=placeholder,
            dimension_for=dimension_for, project=project)
    else:
        dimension = {"processed": 0, "credited": [], "skipped_no_checklist": [],
                     "last_created_at": since}
    return {"task": task, "dimension": dimension,
            "last_created_at": task["last_created_at"]}


def _resolve_dimension_for():
    """Best-effort vtf RUBRIC mapper for dimension granularity. Returns None
    (adapter falls back to its generic mapper) when vtf is not co-located — the
    dimension credit then degrades gracefully instead of failing."""
    vtf = os.environ.get("COMPASS_VTF_DIR")
    candidates = [Path(vtf)] if vtf else []
    candidates.append(_HERE.parent.parent / "vertical-task-factory" / "fde-toolbox")
    for c in candidates:
        cap = c / "fde_knowledge_capsule.py"
        if cap.exists():
            spec = importlib.util.spec_from_file_location("fde_knowledge_capsule", cap)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.map_to_rubric_dimension
    return None


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    checklist_dir = os.environ.get("COMPASS_FDE_CHECKLIST_DIR")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

    try:
        cfg = _poller.parse_secret(_poller.SECRET_FILE)
    except (FileNotFoundError, ValueError) as e:
        sys.stderr.write(f"fde verdict reconcile skipped · DB secret unavailable "
                         f"(G-cloud / compass_sub credential) · {e}\n")
        return 0

    since = load_since(WATERMARK_PATH)
    try:
        # dry-run stays strictly read-only (peek only · physically cannot mutate)
        with _poller.db_connection(cfg, readonly=dry_run) as conn:
            # compass.poi_credit lives in the compass schema · fde_verdicts in public
            conn.cursor().execute("SET search_path TO compass, public")
            if dry_run:
                rows = BUS.peek_fde_verdicts(conn, since=since, placeholder="%s")
                print(f"{stamp} · DRY-RUN · would settle {len(rows)} verdict(s) "
                      f"since={since}: {[r['task_uid'] for r in rows]}")
                return 0
            combined = settle_once(conn, since, checklist_dir, placeholder="%s",
                                   dimension_for=_resolve_dimension_for())
            res = combined["task"]
            if res["processed"]:
                save_since(WATERMARK_PATH, combined["last_created_at"])
                CS.write_snapshot_atomic(SNAPSHOT_PATH, CS.fetch_all_credits(conn))
    except (FileNotFoundError, ValueError, RuntimeError) as e:
        # tunnel/secret/connect failure → honest skip (gated, not a hard error)
        sys.stderr.write(f"fde verdict reconcile skipped · connect failed · {e}\n")
        return 0
    except Exception as e:
        # missing table / no GRANT → psycopg2 ProgrammingError → skip until G-cloud
        sys.stderr.write(f"fde verdict reconcile · {type(e).__name__}: "
                         f"{str(e)[:200]} · (likely G-cloud: table/GRANT pending)\n")
        return 0

    dim = combined["dimension"]
    print(f"{stamp} · fde verdicts processed={res['processed']} since={since} "
          f"-> {combined['last_created_at']} · task_credited="
          f"{[(c['task_uid'], c['delta']) for c in res['credited']]} · "
          f"dim_processed={dim['processed']} dim_skipped={dim['skipped_no_checklist']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
