"""compass · FDE avoidance-corpus batch build driver (W6 substrate · Task A1).

Turns every real FDE verdict+checklist pair into recallable per-RUBRIC-dimension
avoid-pitfall (失败 item) / proven-approach (通过 item) knowledge atoms that
accumulate across tasks. This is the W6 substrate: before solving the next buyer
task v5's copilot recalls `fde-dim-<dimension>` and is grounded by every prior
task's mistakes on that dimension — the dogfood loop that turns external buyer
verdicts into compounding capability (anchor #1 agent-first).

Two seams (so compass core stays decoupled from the vtf capsule module — design §3):
  · load_fde_tasks — pure on-disk loader (picks the LATEST verdict per task; a
    rescored verdict supersedes its predecessor; UTF-8 — the files are CJK).
  · build_corpus — feeds the (injected) vtf capsule callables through the existing
    proof.fde_batch_ingest flywheel (atoms accumulate + dimensions earn PoI).

main() resolves the vtf toolbox (sibling repo or $COMPASS_VTF_DIR) and wires
fde_knowledge_capsule.{build_dimension_atoms, ingest_atoms, map_to_rubric_dimension}.
NO LLM (the dimension mapper is deterministic keyword). Material only fingerprinted.

Run:
  python ops/fde_avoidance_corpus_build.py            # build atoms into the fde-knowledge memory dir
  python ops/fde_avoidance_corpus_build.py --dry-run  # load + report tasks, write nothing
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))
from proof.fde_batch_ingest import batch_ingest_and_credit  # noqa: E402
from proof.fde_poi_adapter import DEFAULT_DIM_PROJECT  # noqa: E402

# `_v5_<something>_real_verdict_<YYYYMMDD>.json` — the date suffix orders rescored
# verdicts (a higher date wins). The authoritative task_uid is read from the file,
# not parsed from the name (the name uses `data003`, the uid is `data_002`-style).
_VERDICT_GLOB = "_v5_*_real_verdict_*.json"
_DATE_RE = re.compile(r"_(\d{8})\.json$")
# `_v5_<token>_real_verdict_<date>.json` → <token> (e.g. `data001`)
_TOKEN_RE = re.compile(r"^_v5_(.+?)_real_verdict_\d{8}\.json$")
# normalize a filename token `data001` → canonical uid `data_001` (alpha_numeric)
_UID_NORM_RE = re.compile(r"^([A-Za-z]+)(\d+)$")


def _read_json(path: str) -> dict:
    """UTF-8 read (the FDE files are CJK; the Windows gbk default crashes)."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _verdict_date(path: str) -> str:
    """Sort key for picking the latest verdict — the YYYYMMDD filename suffix, or
    '' so an undated file never beats a dated rescore."""
    m = _DATE_RE.search(os.path.basename(path))
    return m.group(1) if m else ""


def _uid_from_filename(path: str) -> str:
    """Fallback task_uid when the verdict JSON omits the field (real case:
    data_001's verdict carries answer_len, not task_uid). Extract the filename
    token and normalize `data001` → `data_001` so it joins the checklist key."""
    m = _TOKEN_RE.match(os.path.basename(path))
    if not m:
        return ""
    token = m.group(1)
    nm = _UID_NORM_RE.match(token)
    return f"{nm.group(1)}_{nm.group(2)}" if nm else token


def load_fde_tasks(verdict_dir, checklist_dir, task_ids=None):
    """Discover {task_id, checklist, verdict} tuples from disk.

    For each verdict file (`_v5_*_real_verdict_*.json`) the task_uid is read from
    the file; the LATEST verdict per task_uid wins (by YYYYMMDD filename suffix).
    The matching `<task_uid>_checklist.json` is loaded from checklist_dir; a task
    whose checklist is missing is skipped (warned to stderr). Optionally filtered
    to `task_ids`. Returns the list sorted by task_id."""
    latest: dict = {}  # task_uid -> (date, verdict, path)
    for path in glob.glob(os.path.join(verdict_dir, _VERDICT_GLOB)):
        try:
            verdict = _read_json(path)
        except (OSError, ValueError) as e:
            print(f"[corpus] skip unreadable verdict {path}: {e}", file=sys.stderr)
            continue
        uid = str(verdict.get("task_uid") or "").strip() or _uid_from_filename(path)
        if not uid:
            print(f"[corpus] skip verdict without task_uid: {path}", file=sys.stderr)
            continue
        date = _verdict_date(path)
        if uid not in latest or date > latest[uid][0]:
            latest[uid] = (date, verdict, path)

    tasks = []
    for uid, (_date, verdict, _path) in latest.items():
        if task_ids is not None and uid not in task_ids:
            continue
        cl_path = os.path.join(checklist_dir, f"{uid}_checklist.json")
        if not os.path.exists(cl_path):
            print(f"[corpus] skip {uid}: no checklist at {cl_path}", file=sys.stderr)
            continue
        try:
            checklist = _read_json(cl_path)
        except (OSError, ValueError) as e:
            print(f"[corpus] skip {uid}: unreadable checklist {cl_path}: {e}", file=sys.stderr)
            continue
        tasks.append({"task_id": uid, "checklist": checklist, "verdict": verdict})

    return sorted(tasks, key=lambda t: t["task_id"])


def build_corpus(tasks, mem_dir, conn, now_iso, *, build_atoms, ingest_atoms,
                 dimension_for, placeholder="?", project=DEFAULT_DIM_PROJECT,
                 pass_score=None):
    """Run the dimension flywheel over `tasks`: accumulate avoidance atoms into
    `mem_dir` (one `fde-dim-<dimension>.md` per dimension) and credit per-dimension
    PoI into `conn`. The vtf capsule callables are injected (compass core never
    imports vtf). Delegates to proof.fde_batch_ingest.batch_ingest_and_credit;
    returns its {per_task, credit_snapshot, dimension_events, atom_paths}."""
    return batch_ingest_and_credit(
        conn, tasks, now_iso, placeholder,
        dimension_for=dimension_for, build_atoms=build_atoms,
        ingest_atoms=ingest_atoms, mem_dir=mem_dir, project=project,
        pass_score=pass_score)


# ─── main() · resolve vtf + wire ─────────────────────────────────────────────

def _resolve_vtf():
    """Locate the vtf fde-toolbox (env override or sibling repo) and return its
    capsule callables. main()-only; the unit tests inject stubs instead."""
    candidates = []
    env = os.environ.get("COMPASS_VTF_DIR")
    if env:
        candidates.append(Path(env))
    candidates.append(_HERE.parent.parent / "vertical-task-factory" / "fde-toolbox")
    for c in candidates:
        if (c / "fde_knowledge_capsule.py").exists():
            spec = importlib.util.spec_from_file_location(
                "fde_knowledge_capsule", c / "fde_knowledge_capsule.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod, c
    raise SystemExit(
        "[corpus] vtf fde-toolbox not found — set COMPASS_VTF_DIR to the dir "
        "containing fde_knowledge_capsule.py")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build the FDE avoidance corpus (W6 substrate).")
    ap.add_argument("--verdict-dir", help="dir with _v5_*_real_verdict_*.json (default: vtf root)")
    ap.add_argument("--checklist-dir", help="dir with <uid>_checklist.json (default: vtf root)")
    ap.add_argument("--mem-dir", help="atoms output dir (default: ~/.claude/projects/fde-knowledge/memory)")
    ap.add_argument("--credit-db", help="sqlite path for dimension PoI (default: in-memory)")
    ap.add_argument("--dry-run", action="store_true", help="load + report tasks, write nothing")
    args = ap.parse_args(argv)

    mod, vtf_dir = _resolve_vtf()
    verdict_dir = args.verdict_dir or str(vtf_dir.parent)
    checklist_dir = args.checklist_dir or str(vtf_dir.parent)
    mem_dir = args.mem_dir or os.path.expanduser(
        "~/.claude/projects/fde-knowledge/memory")
    now_iso = os.environ.get("COMPASS_CORPUS_NOW") or _utc_now()

    tasks = load_fde_tasks(verdict_dir, checklist_dir)
    print(f"[corpus] loaded {len(tasks)} tasks: {[t['task_id'] for t in tasks]}")
    if args.dry_run:
        return 0

    conn = sqlite3.connect(args.credit_db or ":memory:")
    conn.execute("CREATE TABLE IF NOT EXISTS poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()

    res = build_corpus(
        tasks, mem_dir, conn, now_iso,
        build_atoms=mod.build_dimension_atoms, ingest_atoms=mod.ingest_atoms,
        dimension_for=mod.map_to_rubric_dimension)
    print(f"[corpus] dimensions: {res['dimension_events']}")
    print(f"[corpus] atom files: {len(res['atom_paths'])} → {mem_dir}")
    for dim, p in sorted(res["atom_paths"].items()):
        print(f"  · {dim}: {p}")
    return 0


def _utc_now():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
