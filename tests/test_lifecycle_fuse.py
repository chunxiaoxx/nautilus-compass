"""
v1.7.1 · llm-wiki2 fuse smoke tests · 真 deterministic · 真 LLM-free verify

5 spec cases + 3 edge cases = 8 total.
See paper/LLM_WIKI2_FUSE_DESIGN.md §6.

Run:
    python tests/test_lifecycle_fuse.py
"""
import sys
import os
from datetime import datetime, timedelta

# Make repo root importable (tests/ → parent)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall import promote_lifecycle_tier, verify_cascade_closure


def test_1_tier_promotion_by_access():
    """Case 1 · tier promotion: working + reinforce_count=5 + promote_after=5_access → episodic."""
    entry = {
        "tier": "working",
        "reinforce_count": 5,
        "promote_after": "5_access",
    }
    result = promote_lifecycle_tier(entry)
    assert result["tier"] == "episodic", f"expected episodic · got {result['tier']}"
    assert result["promoted"] is True, "expected promoted=True"
    assert result["archived"] is False, "expected archived=False"
    print("✅ Case 1 · tier promotion by access count")


def test_2_no_promote_below_threshold():
    """Case 2 · no promotion when reinforce_count < threshold."""
    entry = {
        "tier": "working",
        "reinforce_count": 3,
        "promote_after": "5_access",
    }
    result = promote_lifecycle_tier(entry)
    assert result["tier"] == "working", f"expected working · got {result['tier']}"
    assert result["promoted"] is False
    print("✅ Case 2 · no promote below threshold")


def test_3_forget_at_expiry():
    """Case 3 · forget_at reached → archive flag set."""
    entry = {
        "tier": "working",
        "reinforce_count": 0,
        "forget_at": "2020-01-01T00:00:00Z",  # past
    }
    result = promote_lifecycle_tier(entry)
    assert result["archived"] is True, "expected archived=True for past forget_at"
    print("✅ Case 3 · forget_at expiry")


def test_4_forget_at_future_not_archived():
    """Case 4 (edge) · forget_at in future → NOT archived."""
    entry = {
        "tier": "working",
        "reinforce_count": 0,
        "forget_at": "2099-12-31T23:59:59Z",
    }
    result = promote_lifecycle_tier(entry)
    assert result["archived"] is False, "expected archived=False for future forget_at"
    print("✅ Case 4 (edge) · forget_at future not archived")


def test_5_procedural_no_promote():
    """Case 5 · procedural tier (top) does NOT promote even with high reinforce_count."""
    entry = {
        "tier": "procedural",
        "reinforce_count": 999,
        "promote_after": "1_access",
    }
    result = promote_lifecycle_tier(entry)
    assert result["tier"] == "procedural"
    assert result["promoted"] is False
    print("✅ Case 5 · procedural top tier no promote")


def test_6_duration_promotion():
    """Case 6 (edge) · promote_after as duration · old created_at → promote."""
    entry = {
        "tier": "working",
        "reinforce_count": 0,
        "promote_after": "7d",
        "created_at": (datetime.now() - timedelta(days=8)).isoformat(),
    }
    result = promote_lifecycle_tier(entry)
    assert result["tier"] == "episodic", f"expected episodic · got {result['tier']}"
    assert result["promoted"] is True
    print("✅ Case 6 (edge) · duration-based promotion")


def test_7_cascade_closure_unaffected():
    """Case 7 · existing verify_cascade_closure 真 NOT regressed by lifecycle fields."""
    top = [
        (0.9, {"path": "session_A.md", "declaration_type": "cascade",
               "depends_on": ["session_B.md"], "tier": "working",
               "decay_rate": 0.5, "reinforce_count": 0}),
        (-1.0, {"path": "session_B.md", "declaration_type": "none",
                "tier": "semantic", "reinforce_count": 10}),
    ]
    result = verify_cascade_closure(top)
    assert result["complete"] is True, f"expected complete · got missing={result['missing']}"
    assert result["cascade_hits"] == 1
    print("✅ Case 7 · cascade closure 不破 (regression guard)")


def test_8_default_promote_after_by_tier():
    """Case 8 (edge) · default promote_after when entry omits explicit value."""
    # working tier default is "1_access" · 1 reinforce → promote
    entry = {
        "tier": "working",
        "reinforce_count": 1,
    }
    result = promote_lifecycle_tier(entry)
    assert result["tier"] == "episodic", f"expected episodic by default · got {result['tier']}"
    assert result["promoted"] is True
    print("✅ Case 8 (edge) · default promote_after by tier")


if __name__ == "__main__":
    tests = [
        test_1_tier_promotion_by_access,
        test_2_no_promote_below_threshold,
        test_3_forget_at_expiry,
        test_4_forget_at_future_not_archived,
        test_5_procedural_no_promote,
        test_6_duration_promotion,
        test_7_cascade_closure_unaffected,
        test_8_default_promote_after_by_tier,
    ]
    failures = []
    for t in tests:
        try:
            t()
        except AssertionError as e:
            failures.append((t.__name__, str(e)))
            print(f"❌ {t.__name__}: {e}")
    if failures:
        print(f"\n❌ {len(failures)}/{len(tests)} failures")
        sys.exit(1)
    print(f"\n✅ {len(tests)}/{len(tests)} lifecycle fuse smoke tests pass")
