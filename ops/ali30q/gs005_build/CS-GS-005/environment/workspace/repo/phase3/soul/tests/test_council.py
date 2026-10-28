"""Tests for soul.council — multi-persona propose + chairman converge.

TDD: written BEFORE council.py exists. These must initially fail (RED).
Design decisions tested here:
- propose returns one dict per persona with keys: persona, proposal, raw
- a persona returning "NONE" is kept in the list with proposal="NONE" (not filtered)
- converge returns the winning proposal dict augmented with score + reason
- converge fail-safe: unparseable chairman output -> returns proposals[0] with fallback marker
"""

import pytest
from soul import council
from soul.council import PERSONAS, propose, converge


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_generate_fn(response_map: dict):
    """Return a generate_fn that echoes responses keyed by the first keyword found
    in the system prompt. Fallback to a generic response."""
    def generate_fn(prompt: str, system: str = "") -> str:
        for key, resp in response_map.items():
            if key in system:
                return resp
        return "generic response"
    return generate_fn


# ---------------------------------------------------------------------------
# PERSONAS constant
# ---------------------------------------------------------------------------

def test_personas_tuple_has_four_entries():
    assert len(PERSONAS) == 4


def test_personas_contains_expected_roles():
    assert "performance" in PERSONAS
    assert "robustness" in PERSONAS
    assert "readability" in PERSONAS
    assert "correctness" in PERSONAS


# ---------------------------------------------------------------------------
# propose()
# ---------------------------------------------------------------------------

def test_propose_returns_one_dict_per_persona():
    gen = make_generate_fn({
        "performance": "Use a dict instead of a list for O(1) lookup.",
        "robustness": "Add None check before indexing.",
        "readability": "Rename `x` to `item_count` for clarity.",
        "correctness": "Off-by-one in slice: use [:-1] not [:-2].",
    })
    results = propose(gen, task="Improve parse_csv", context="def parse_csv(): ...")
    assert len(results) == len(PERSONAS)


def test_propose_dicts_have_required_keys():
    gen = make_generate_fn({p: f"Proposal from {p}" for p in PERSONAS})
    results = propose(gen, task="Improve foo", context="code here")
    for item in results:
        assert "persona" in item, f"Missing 'persona' key in {item}"
        assert "proposal" in item, f"Missing 'proposal' key in {item}"
        assert "raw" in item, f"Missing 'raw' key in {item}"


def test_propose_persona_values_match_personas_constant():
    gen = make_generate_fn({p: f"{p} output" for p in PERSONAS})
    results = propose(gen, task="t", context="c")
    returned_personas = {r["persona"] for r in results}
    assert returned_personas == set(PERSONAS)


def test_propose_proposal_field_contains_generated_text():
    gen = make_generate_fn({"performance": "Cache the result in a module-level dict."})
    results = propose(gen, task="t", context="c")
    perf = next(r for r in results if r["persona"] == "performance")
    assert "Cache the result" in perf["proposal"]


def test_propose_raw_field_is_the_full_generate_fn_output():
    gen = make_generate_fn({"readability": "  Rename `n` to `num_retries`.  "})
    results = propose(gen, task="t", context="c")
    read = next(r for r in results if r["persona"] == "readability")
    # raw should be exactly what generate_fn returned (may be stripped, but at
    # minimum must contain the core text)
    assert "Rename" in read["raw"]


def test_propose_none_response_is_kept_not_filtered():
    """A persona returning 'NONE' must still appear in results."""
    def gen(prompt, system=""):
        return "NONE"
    results = propose(gen, task="t", context="c")
    assert len(results) == len(PERSONAS)
    for r in results:
        assert r["proposal"] == "NONE"


def test_propose_accepts_custom_personas_subset():
    custom = ("performance", "correctness")
    gen = make_generate_fn({p: f"{p} text" for p in custom})
    results = propose(gen, task="t", context="c", personas=custom)
    assert len(results) == 2
    assert {r["persona"] for r in results} == set(custom)


def test_propose_calls_generate_fn_once_per_persona():
    call_count = [0]
    def gen(prompt, system=""):
        call_count[0] += 1
        return "proposal text"
    propose(gen, task="t", context="c")
    assert call_count[0] == len(PERSONAS)


# ---------------------------------------------------------------------------
# converge()
# ---------------------------------------------------------------------------

def _sample_proposals():
    return [
        {"persona": "performance", "proposal": "Use a set for O(1) lookup.", "raw": "Use a set for O(1) lookup."},
        {"persona": "robustness", "proposal": "Validate input is not None.", "raw": "Validate input is not None."},
        {"persona": "readability", "proposal": "Rename `v` to `value`.", "raw": "Rename `v` to `value`."},
        {"persona": "correctness", "proposal": "Fix slice off-by-one.", "raw": "Fix slice off-by-one."},
    ]


def test_converge_returns_dict():
    proposals = _sample_proposals()
    gen = make_generate_fn({"chairman": "INDEX: 2\nSCORE: 8\nREASON: best readability fix"})
    result = converge(gen, proposals, task="Improve foo")
    assert isinstance(result, dict)


def test_converge_augments_winning_proposal_with_score_and_reason():
    proposals = _sample_proposals()
    gen = make_generate_fn({"chairman": "INDEX: 2\nSCORE: 8\nREASON: best readability fix"})
    result = converge(gen, proposals, task="Improve foo")
    assert "score" in result
    assert "reason" in result


def test_converge_selects_correct_index():
    proposals = _sample_proposals()
    # Chairman picks index 2 -> readability proposal
    gen = make_generate_fn({"chairman": "INDEX: 2\nSCORE: 8\nREASON: best readability fix"})
    result = converge(gen, proposals, task="Improve foo")
    assert result["persona"] == "readability"
    assert result["proposal"] == "Rename `v` to `value`."


def test_converge_score_parsed_correctly():
    proposals = _sample_proposals()
    gen = make_generate_fn({"chairman": "INDEX: 0\nSCORE: 9\nREASON: critical correctness"})
    result = converge(gen, proposals, task="t")
    # score may be int or float
    assert float(result["score"]) == 9.0


def test_converge_reason_parsed_correctly():
    proposals = _sample_proposals()
    gen = make_generate_fn({"chairman": "INDEX: 1\nSCORE: 7\nREASON: guards against None"})
    result = converge(gen, proposals, task="t")
    assert "guards against None" in result["reason"]


def test_converge_preserves_winning_proposal_fields():
    proposals = _sample_proposals()
    gen = make_generate_fn({"chairman": "INDEX: 3\nSCORE: 6\nREASON: fixes correctness"})
    result = converge(gen, proposals, task="t")
    assert result["persona"] == "correctness"
    assert result["proposal"] == "Fix slice off-by-one."
    assert "raw" in result


def test_converge_calls_generate_fn_once():
    proposals = _sample_proposals()
    call_count = [0]
    def gen(prompt, system=""):
        call_count[0] += 1
        return "INDEX: 0\nSCORE: 5\nREASON: ok"
    converge(gen, proposals, task="t")
    assert call_count[0] == 1


# ---------------------------------------------------------------------------
# converge() fail-safe: unparseable chairman output
# ---------------------------------------------------------------------------

def test_converge_fallback_on_unparseable_output():
    proposals = _sample_proposals()
    def gen(prompt, system=""):
        return "I cannot decide, all proposals are equally good."
    result = converge(gen, proposals, task="t")
    # Must not raise; must return a dict
    assert isinstance(result, dict)
    assert "score" in result
    assert "reason" in result


def test_converge_fallback_returns_first_proposal():
    proposals = _sample_proposals()
    def gen(prompt, system=""):
        return "GARBAGE OUTPUT with no parseable index"
    result = converge(gen, proposals, task="t")
    assert result["persona"] == proposals[0]["persona"]
    assert result["proposal"] == proposals[0]["proposal"]


def test_converge_fallback_reason_indicates_parse_failure():
    proposals = _sample_proposals()
    def gen(prompt, system=""):
        return "completely unparseable"
    result = converge(gen, proposals, task="t")
    # reason should mention fallback or parse failure
    assert "fallback" in result["reason"].lower() or "parse" in result["reason"].lower()


def test_converge_fallback_on_out_of_range_index():
    proposals = _sample_proposals()
    def gen(prompt, system=""):
        return "INDEX: 99\nSCORE: 10\nREASON: out of range"
    result = converge(gen, proposals, task="t")
    # Out-of-range index should also trigger fallback to proposals[0]
    assert result["persona"] == proposals[0]["persona"]


def test_converge_fallback_on_empty_proposals_is_graceful():
    """Edge case: empty proposals list — converge should not crash."""
    def gen(prompt, system=""):
        return "INDEX: 0\nSCORE: 5\nREASON: ok"
    # With empty proposals, fallback behaviour: raise or return None — we
    # choose: raise ValueError so callers know the input is bad.
    with pytest.raises((ValueError, IndexError)):
        converge(gen, [], task="t")
