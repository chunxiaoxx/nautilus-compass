"""B5 · 写入时 cross-frame 矛盾检测 · 拦截方向写反(本 session 亲踩 valid_rate 0→0.22 读反)."""
import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from proof.contradiction_check import check_contradiction


def test_flags_reversed_direction_same_metric():
    # 本 session 真案例: 我写"掉到0"·soul 权威入站"涨到0.22" → 必 flag
    new = "soul 第2测 valid_rate 从 0.22 掉到 0.0(不是涨)"
    recent = ["soul LOO gen2: valid_rate 0→0.22 在涨·第一个真泛化信号"]
    warns = check_contradiction(new, recent)
    assert warns, f"reversed direction on valid_rate must flag · got {warns}"
    assert any("valid_rate" in w for w in warns)
    print("✅ reversed direction same metric → flag (本 session 真案例)")


def test_no_flag_different_metric():
    new = "win_rate 破 0.6 了"
    recent = ["valid_rate 0→0.22 在涨"]
    assert check_contradiction(new, recent) == []
    print("✅ different metric → no flag")


def test_no_flag_same_direction():
    new = "valid_rate 0→0.3 继续涨"
    recent = ["valid_rate 0→0.22 在涨"]
    assert check_contradiction(new, recent) == []
    print("✅ same direction → no flag")


def test_empty_recent_no_flag():
    assert check_contradiction("valid_rate 0.22→0 掉", []) == []
    assert check_contradiction("anything", None) == []
    print("✅ empty/none recent → no flag")


def test_never_raises_on_garbage():
    assert check_contradiction(None, ["x"]) == []
    assert check_contradiction("no numbers here", ["也没有数字"]) == []
    print("✅ garbage input → no raise")


if __name__ == "__main__":
    tests = [
        test_flags_reversed_direction_same_metric,
        test_no_flag_different_metric,
        test_no_flag_same_direction,
        test_empty_recent_no_flag,
        test_never_raises_on_garbage,
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
    print(f"\n✅ {len(tests)}/{len(tests)} contradiction-check tests pass")
