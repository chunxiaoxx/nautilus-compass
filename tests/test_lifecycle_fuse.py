"""
v1.7.1 · llm-wiki2 fuse smoke tests · 真 deterministic · 真 LLM-free verify

5 spec cases + 3 edge cases = 8 total.
See paper/LLM_WIKI2_FUSE_DESIGN.md §6.

Run:
    python tests/test_lifecycle_fuse.py
"""
import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Make repo root importable (tests/ → parent)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall import (
    promote_lifecycle_tier,
    verify_cascade_closure,
    reinforce_on_recall_hit,
    apply_tier_weight,
)


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


# ──────────────────────────────────────────────────────────────────────────
# Task 1 (Phase 1 · 2026-06-23) · access-event closure:
# reinforce_count +1 on recall hit · feeds promote_lifecycle_tier Rule A.
# ──────────────────────────────────────────────────────────────────────────

_SESSION_TPL = """---
name: {name}
tier: working
reinforce_count: {rc}
---

body text
"""

_NO_RC_TPL = """---
name: {name}
tier: working
---

body text
"""


def _mk_mem_dir():
    d = Path(tempfile.mkdtemp(prefix="compass_reinforce_test_"))
    return d


def test_9_reinforce_bump_on_hit():
    """Recall hit → that file's reinforce_count goes 0 → 1 in frontmatter."""
    d = _mk_mem_dir()
    try:
        f = d / "session_hit.md"
        f.write_text(_SESSION_TPL.format(name="session_hit", rc=0), encoding="utf-8")
        recall = [{"path": "session_hit.md", "score": 0.9}]
        bumped = reinforce_on_recall_hit(d, recall)
        text = f.read_text(encoding="utf-8")
        assert "reinforce_count: 1" in text, f"expected reinforce_count: 1 · got:\n{text}"
        assert any("session_hit.md" in str(p) for p, _ in bumped), "expected file in bumped list"
        print("✅ Case 9 · reinforce_count +1 on recall hit")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_10_reinforce_accumulates_and_inserts_missing():
    """Two hits → 2; field absent in frontmatter → inserted as 1 then 2."""
    d = _mk_mem_dir()
    try:
        f = d / "session_norc.md"
        f.write_text(_NO_RC_TPL.format(name="session_norc"), encoding="utf-8")
        recall = [{"path": "session_norc.md", "score": 0.8}]
        reinforce_on_recall_hit(d, recall)
        assert "reinforce_count: 1" in f.read_text(encoding="utf-8"), "missing field should insert as 1"
        reinforce_on_recall_hit(d, recall)
        text = f.read_text(encoding="utf-8")
        assert "reinforce_count: 2" in text, f"expected accumulate to 2 · got:\n{text}"
        print("✅ Case 10 · reinforce accumulates + inserts missing field")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_11_reinforce_safe_on_bad_input():
    """No raise on: nonexistent path · file without frontmatter · string-form hit."""
    d = _mk_mem_dir()
    try:
        # nonexistent path → skipped, no raise
        reinforce_on_recall_hit(d, [{"path": "session_ghost.md"}])
        # file without frontmatter → skipped, no raise
        nofront = d / "session_nofront.md"
        nofront.write_text("just body, no frontmatter\n", encoding="utf-8")
        reinforce_on_recall_hit(d, [{"path": "session_nofront.md"}])
        assert "reinforce_count" not in nofront.read_text(encoding="utf-8"), \
            "no-frontmatter file must NOT be mutated"
        # string-form hit (defensive) → no raise
        reinforce_on_recall_hit(d, ["session_ghost.md"])
        print("✅ Case 11 · reinforce safe on bad input (never raises)")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_12_tier_weight_reranks_ties_only():
    """Task 4 · tier weight: higher tier wins ties · but never flips a real cosine gap."""
    # tie on cosine → semantic outranks working
    top = [
        (0.5, {"path": "w.md", "tier": "working"}),
        (0.5, {"path": "s.md", "tier": "semantic"}),
    ]
    out = apply_tier_weight(top)
    assert out[0][1]["path"] == "s.md", f"semantic should win tie · got {out[0][1]['path']}"
    # output score is the ORIGINAL cosine (bonus is ranking-only, not written)
    assert out[0][0] == 0.5, f"output score must stay original cosine · got {out[0][0]}"
    # a real 0.4 cosine gap must NOT be flipped by the small tier bonus
    top2 = [
        (0.9, {"path": "w.md", "tier": "working"}),
        (0.5, {"path": "p.md", "tier": "procedural"}),
    ]
    out2 = apply_tier_weight(top2)
    assert out2[0][1]["path"] == "w.md", "0.4 cosine gap must not be flipped by tier bonus"
    # missing tier defaults to working (no raise)
    out3 = apply_tier_weight([(0.5, {"path": "x.md"}), (0.5, {"path": "e.md", "tier": "episodic"})])
    assert out3[0][1]["path"] == "e.md", "episodic should outrank tier-less (working) on tie"
    print("✅ Case 12 · tier-weight re-rank (ties only · gap-preserving)")


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
        test_9_reinforce_bump_on_hit,
        test_10_reinforce_accumulates_and_inserts_missing,
        test_11_reinforce_safe_on_bad_input,
        test_12_tier_weight_reranks_ties_only,
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
