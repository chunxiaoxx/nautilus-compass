"""B1 · 价值证明门 smoke tests · 每个记忆功能上线前必须绑可测 downstream uplift."""
import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from proof.value_gate import admit_feature, ValueClaim


def test_feature_without_measurable_claim_rejected():
    errs = admit_feature(ValueClaim(name="shiny", helps_whom="", on_task="", measured_by=""))
    assert errs, "empty claim must be rejected"
    print("✅ empty claim rejected")


def test_feature_with_full_claim_admitted():
    errs = admit_feature(ValueClaim(
        name="tier_weight",
        helps_whom="recall consumer",
        on_task="cross-agent peer learning",
        measured_by="PoI cumulative_impact delta",
    ))
    assert errs == [], f"full valid claim should pass · got {errs}"
    print("✅ full claim admitted")


def test_unmeasurable_signal_rejected():
    # measured_by 必须引用真实可测信号 · 含糊词("感觉更好")→ 拒
    errs = admit_feature(ValueClaim(
        name="vibes", helps_whom="users", on_task="recall", measured_by="感觉更好",
    ))
    assert errs, "unmeasurable signal must be rejected"
    assert any("measured_by" in e for e in errs)
    print("✅ unmeasurable signal rejected")


def test_recognized_signals_pass():
    for sig in ["PoI cumulative_impact", "win_rate", "recall-hit rate", "tier mutation count"]:
        errs = admit_feature(ValueClaim(
            name="f", helps_whom="x", on_task="y", measured_by=sig))
        assert errs == [], f"signal '{sig}' should be recognized · got {errs}"
    print("✅ recognized measurable signals pass")


if __name__ == "__main__":
    tests = [
        test_feature_without_measurable_claim_rejected,
        test_feature_with_full_claim_admitted,
        test_unmeasurable_signal_rejected,
        test_recognized_signals_pass,
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
    print(f"\n✅ {len(tests)}/{len(tests)} value-gate tests pass")
