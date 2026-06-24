"""B2 · LIVE-state 自省自检 smoke tests · NO 假装 live · 永不抛."""
import sys
import os

# Windows GBK console crashes on emoji prints · force utf-8 (永久修 · 见 GBK fix memory)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from ops.live_state_check import check_feature_live, report, FEATURES


def test_features_registry_nonempty():
    # 每个被宣称的功能必须有一条 live 判据(命令+期望)
    assert len(FEATURES) >= 4
    for f in FEATURES:
        assert "name" in f and "probe" in f and "expect" in f
    print("✅ FEATURES registry well-formed")


def test_check_reports_dormant_for_absent_timer():
    # 不存在的 systemd unit → live=False·status∈{dormant,error}(不抛)
    r = check_feature_live({
        "name": "ghost",
        "probe": ["systemctl", "is-active", "compass-ghost-xyz.timer"],
        "expect": "active",
    })
    assert r["live"] is False
    assert r["status"] in ("dormant", "error")
    print("✅ absent timer → dormant/error (no raise)")


def test_check_gt_expectation_counts():
    # expect '>0' · grep -c 命中 → live True
    r = check_feature_live({
        "name": "self_present",
        "probe": ["grep", "-c", "FEATURES", "ops/live_state_check.py"],
        "expect": ">0",
    })
    assert r["live"] is True, f"expected live · got {r}"
    print("✅ '>0' expectation works")


def test_check_never_raises_on_bad_probe():
    # 乱命令 → status=error·live=False·不抛
    r = check_feature_live({"name": "bad", "probe": ["___nonexistent_cmd___"], "expect": "x"})
    assert r["live"] is False and r["status"] == "error"
    print("✅ bad probe → error (no raise)")


def test_report_returns_list_for_all_features():
    rep = report()
    assert isinstance(rep, list) and len(rep) == len(FEATURES)
    print("✅ report() covers all FEATURES")


if __name__ == "__main__":
    tests = [
        test_features_registry_nonempty,
        test_check_reports_dormant_for_absent_timer,
        test_check_gt_expectation_counts,
        test_check_never_raises_on_bad_probe,
        test_report_returns_list_for_all_features,
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
    print(f"\n✅ {len(tests)}/{len(tests)} live-state-check tests pass")
