"""Tests for the SWE-bench-Lite core-subset loader (Phase 4 Task 4).

Joins the locked N=110 subset ids with the HF dataset rows to surface the fields
the solver + official harness need. Dataset is injected so the unit test needs no
network/Docker.
"""
import pytest

from subset_loader import load_subset_instances

REQUIRED = {"repo", "base_commit", "problem_statement", "test_patch",
            "FAIL_TO_PASS", "PASS_TO_PASS"}


def _fake_rows(n=5):
    return [
        {"instance_id": f"x-{i}", "repo": "r", "base_commit": "c",
         "problem_statement": "p", "patch": "d", "test_patch": "t",
         "FAIL_TO_PASS": "[]", "PASS_TO_PASS": "[]"}
        for i in range(n)
    ]


def test_loads_only_subset_ids_in_subset_order():
    rows = load_subset_instances(
        subset=[{"instance_id": "x-3"}, {"instance_id": "x-1"}],
        dataset=_fake_rows(),
    )
    assert [r["instance_id"] for r in rows] == ["x-3", "x-1"]


def test_required_fields_present():
    rows = load_subset_instances(subset=[{"instance_id": "x-0"}],
                                 dataset=_fake_rows())
    assert REQUIRED <= rows[0].keys()


def test_missing_id_raises():
    with pytest.raises(KeyError):
        load_subset_instances(subset=[{"instance_id": "nope"}],
                              dataset=_fake_rows())


def test_accepts_bare_string_ids():
    rows = load_subset_instances(subset=["x-2"], dataset=_fake_rows())
    assert rows[0]["instance_id"] == "x-2"
