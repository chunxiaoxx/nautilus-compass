"""T3 · batch dimension-flywheel pipeline · multi-task accumulation + compounding.

Runs the dimension capsule flywheel over a batch of (task_id, checklist, verdict)
tasks. Per task it credits per-dimension PoI (proof.fde_poi_adapter) and —
optionally, via INJECTED vtf capsule callables (build_atoms / ingest_atoms) —
ingests the dimension atoms accumulatively (append, never overwrite). The SAME
RUBRIC dimension key therefore accrues BOTH PoI credit (central table) AND
evidence (atom file) ACROSS tasks → cross-domain compounding: the more tasks, the
richer that dimension's recall for the next task's copilot.

Decoupling: the capsule callables and the item→dimension mapper are injected, so
compass core never imports the vtf toolbox. PoI-only batch (capsule callables
omitted) is fully supported. NO LLM. design §3 data-flow.
"""
from __future__ import annotations

from .fde_poi_adapter import (
    DEFAULT_DIM_PROJECT, credit_dimensions_from_verdict)
from .poi_credit_store import fetch_all_credits


def batch_ingest_and_credit(conn, tasks, now_iso, placeholder="%s",
                            dimension_for=None, build_atoms=None,
                            ingest_atoms=None, mem_dir=None,
                            project=DEFAULT_DIM_PROJECT, pass_score=None):
    """Run the flywheel over `tasks` (iterable of {task_id, checklist, verdict}).

    For each task:
      · credit per-dimension PoI via credit_dimensions_from_verdict
      · if build_atoms + ingest_atoms + mem_dir given → build the dimension atoms
        and ingest them accumulatively into mem_dir (one file per dimension,
        evidence appended across tasks)

    Returns {per_task:[credit-summary+task_id...], credit_snapshot:{ledger_key:
    cumulative}, dimension_events:{dim:total_count}, atom_paths:{dim:path}}.
    """
    per_task = []
    dimension_events: dict = {}
    atom_paths: dict = {}

    for t in tasks:
        task_id = t["task_id"]
        checklist = t["checklist"]
        verdict = t["verdict"]

        summary = credit_dimensions_from_verdict(
            conn, task_id, checklist, verdict, now_iso, placeholder,
            dimension_for=dimension_for, pass_score=pass_score, project=project)
        summary = {**summary, "task_id": task_id}
        per_task.append(summary)

        for dim, cnt in summary["events"].items():
            dimension_events[dim] = dimension_events.get(dim, 0) + cnt

        if build_atoms is not None and ingest_atoms is not None and mem_dir:
            atoms = build_atoms(task_id, checklist, verdict)
            paths = ingest_atoms(atoms, mem_dir)  # accumulative
            atom_paths.update(paths)

    return {
        "per_task": per_task,
        "credit_snapshot": fetch_all_credits(conn),
        "dimension_events": dimension_events,
        "atom_paths": atom_paths,
    }
