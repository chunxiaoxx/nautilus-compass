"""Tests for the arm-3 decomposed solver orchestration (Phase 4 Task 10).

arm 3 = decompose the workflow into localize -> edit -> test stages, each a fresh
agent context seeded ONLY with the prior stage's curated handoff (its submission),
NOT the prior stage's full transcript. All stages share the SAME container env
(file edits persist) and the SAME token budget. The ONLY difference from arm 1
(mono) is context isolation — same generic bash tool, same total budget. If this
discipline slips, arm 3 collapses into arm 1 (design §2 operationalization risk).

These tests pin the orchestration + the isolation invariant with an injected
``run_stage`` (no real container / LLM needed).
"""
import pytest

from budget import BudgetExceeded
from decomp_solver import solve_decomp, STAGES


def _recording_runner(submissions):
    """run_stage stub: records every call, returns scripted submissions per stage."""
    calls = []

    def run_stage(stage, task, handoffs):
        calls.append({"stage": stage, "task": task, "handoffs": dict(handoffs)})
        return {"submission": submissions.get(stage, f"{stage}-done"), "exit_status": "Submitted"}

    return run_stage, calls


def test_stages_run_in_canonical_order():
    run_stage, calls = _recording_runner({})
    solve_decomp("fix the bug", run_stage=run_stage)
    assert [c["stage"] for c in calls] == list(STAGES) == ["localize", "edit", "test"]


def test_each_stage_sees_only_prior_handoffs_not_transcripts():
    run_stage, calls = _recording_runner(
        {"localize": "FILE: src/x.py:42", "edit": "changed x.py line 42"}
    )
    solve_decomp("fix the bug", run_stage=run_stage)
    loc, edt, tst = calls
    # localize starts clean
    assert loc["handoffs"] == {}
    # edit sees ONLY the localize handoff (a submission string), nothing else
    assert edt["handoffs"] == {"localize_handoff": "FILE: src/x.py:42"}
    # test sees localize + edit handoffs, both submission strings
    assert tst["handoffs"] == {
        "localize_handoff": "FILE: src/x.py:42",
        "edit_handoff": "changed x.py line 42",
    }
    # ISOLATION: no handoff value is a message list / transcript — all are strings
    for c in calls:
        for v in c["handoffs"].values():
            assert isinstance(v, str)


def test_returns_final_stage_result():
    run_stage, _ = _recording_runner({"test": "PATCH-OK"})
    out = solve_decomp("fix", run_stage=run_stage)
    assert out["submission"] == "PATCH-OK"


def test_budget_exceeded_midway_degrades_and_stops():
    calls = []

    def run_stage(stage, task, handoffs):
        calls.append(stage)
        if stage == "edit":
            raise BudgetExceeded("cap hit")
        return {"submission": f"{stage}-done", "exit_status": "Submitted"}

    out = solve_decomp("fix", run_stage=run_stage)
    assert calls == ["localize", "edit"]          # test never runs
    assert out["exit_status"] == "budget_exceeded"
    # whatever patch existed before the cap is preserved (here localize's, empty patch)
    assert "submission" in out


def test_empty_submission_propagates_empty_handoff():
    run_stage, calls = _recording_runner({"localize": "", "edit": "", "test": ""})
    out = solve_decomp("fix", run_stage=run_stage)
    assert calls[1]["handoffs"]["localize_handoff"] == ""
    assert out["submission"] == ""
