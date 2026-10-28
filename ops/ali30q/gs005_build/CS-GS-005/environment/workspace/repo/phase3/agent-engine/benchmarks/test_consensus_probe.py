"""Tests for the consensus reliability probe.

The probe compares single-LLM baseline accuracy against RAID consensus
accuracy on a bug-detection classification dataset. The pure glue worth
testing first is `parse_label`: extract a discrete label (e.g. buggy/clean)
out of free-form LLM / RAID output so it can feed `evaluate_classification`.
"""
import pytest

from consensus_reliability_probe import (
    build_bug_detection_prompt,
    build_judge_prompt,
    majority_vote_label,
    parse_label,
    run_probe,
)


VALID = ["buggy", "clean"]


def test_parse_label_from_verdict_marker():
    out = "Let me analyze the loop bounds.\nVERDICT: buggy"
    assert parse_label(out, VALID) == "buggy"


def test_parse_label_from_plain_statement():
    out = "After reviewing, this function is clean and behaves correctly."
    assert parse_label(out, VALID) == "clean"


def _items():
    return [
        {"id": 1, "text": "def a(): ...", "ground_truth": "buggy"},
        {"id": 2, "text": "def b(): ...", "ground_truth": "clean"},
        {"id": 3, "text": "def c(): ...", "ground_truth": "buggy"},
    ]


def test_run_probe_computes_accuracy_and_delta():
    # single gets item 1 wrong (2/3); consensus gets all right (3/3).
    single = {1: "VERDICT: clean", 2: "VERDICT: clean", 3: "VERDICT: buggy"}
    consensus = {1: "VERDICT: buggy", 2: "VERDICT: clean", 3: "VERDICT: buggy"}

    res = run_probe(
        _items(),
        single_labeler=lambda it: single[it["id"]],
        consensus_labeler=lambda it: consensus[it["id"]],
        valid_labels=VALID,
    )

    assert res["total"] == 3
    assert res["single_correct"] == 2
    assert res["consensus_correct"] == 3
    assert res["single_accuracy"] == pytest.approx(2 / 3)
    assert res["consensus_accuracy"] == pytest.approx(1.0)
    assert res["delta"] == pytest.approx(1 / 3)


def test_build_prompt_requests_verdict_line_and_includes_code():
    item = {"id": 1, "text": "def foo():\n    return 1 / 0", "ground_truth": "buggy"}
    prompt = build_bug_detection_prompt(item, VALID)
    assert "def foo()" in prompt            # the code under inspection is present
    assert "VERDICT:" in prompt             # instructs the parseable marker
    assert "buggy" in prompt and "clean" in prompt  # constrains the label space


def test_majority_vote_picks_dominant_label():
    outputs = ["VERDICT: buggy", "VERDICT: clean", "VERDICT: buggy"]
    assert majority_vote_label(outputs, VALID) == "buggy"


def test_majority_vote_ignores_unparseable_samples():
    # One sample is noise; the two parseable ones agree.
    outputs = ["I am not sure honestly", "VERDICT: clean", "the code looks clean"]
    assert majority_vote_label(outputs, VALID) == "clean"


def test_majority_vote_tie_returns_none():
    outputs = ["VERDICT: buggy", "VERDICT: clean"]
    assert majority_vote_label(outputs, VALID) is None


def test_build_judge_prompt_includes_code_samples_and_verdict():
    item = {"id": 1, "text": "def foo():\n    return 1 / 0", "ground_truth": "buggy"}
    samples = ["Reviewer A: division by zero, looks buggy",
               "Reviewer B: seems clean to me"]
    p = build_judge_prompt(item, samples, VALID)
    assert "def foo()" in p                                  # the code under review
    assert "Reviewer A: division by zero, looks buggy" in p  # candidate analyses present
    assert "Reviewer B: seems clean to me" in p
    assert "VERDICT:" in p                                   # judge must emit parseable verdict
    assert "buggy" in p and "clean" in p
