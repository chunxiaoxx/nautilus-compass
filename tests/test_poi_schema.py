"""S4 module 1 · poi_schema smoke tests."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proof.poi_schema import (
    ProofOfImpact, validate_iso8601,
    VALID_OUTCOMES, VALID_DECLARATIONS,
)


def _make(**overrides):
    base = dict(
        action_id="b-test",
        agent_id="hr-agent-web",
        cited_memory_paths=["session_x.md"],
        action_outcome="success",
        timestamp_action="2026-05-21T12:00:00Z",
        timestamp_outcome="2026-05-21T12:05:00Z",
    )
    base.update(overrides)
    return ProofOfImpact(**base)


def test_1_construct_valid():
    poi = _make()
    assert poi.action_outcome == "success"
    assert poi.declaration_type == "supports"
    print("OK 1 construct valid")


def test_2_invalid_outcome_raises():
    try:
        _make(action_outcome="bogus")
    except ValueError as e:
        assert "action_outcome" in str(e)
        print("OK 2 invalid outcome raises")
        return
    raise AssertionError("should have raised")


def test_3_invalid_declaration_raises():
    try:
        _make(declaration_type="bogus")
    except ValueError:
        print("OK 3 invalid declaration raises")
        return
    raise AssertionError("should have raised")


def test_4_empty_action_id_raises():
    try:
        _make(action_id="")
    except ValueError:
        print("OK 4 empty action_id raises")
        return
    raise AssertionError("should have raised")


def test_5_notes_truncated():
    poi = _make(notes="x" * 500)
    assert len(poi.notes) == 200
    print("OK 5 notes truncated to 200")


def test_6_to_dict():
    poi = _make()
    d = poi.to_dict()
    assert d["agent_id"] == "hr-agent-web"
    assert "impact_score" in d
    print("OK 6 to_dict")


def test_7_iso8601_validation():
    assert validate_iso8601("2026-05-21T12:00:00Z")
    assert not validate_iso8601("2026/05/21")
    assert not validate_iso8601("")
    assert not validate_iso8601(None)
    print("OK 7 ISO8601 validation")


def test_8_valid_outcomes_complete():
    assert set(VALID_OUTCOMES) == {"success", "failure", "partial", "pending"}
    print("OK 8 valid outcomes match SPEC")


if __name__ == "__main__":
    tests = [test_1_construct_valid, test_2_invalid_outcome_raises,
             test_3_invalid_declaration_raises, test_4_empty_action_id_raises,
             test_5_notes_truncated, test_6_to_dict,
             test_7_iso8601_validation, test_8_valid_outcomes_complete]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} poi_schema smoke pass")
