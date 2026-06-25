"""B3 · no-progress 空转检测 smoke tests · 本 session 亲踩 15 次'idle gated'空转."""
import sys
import os

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from drift.no_progress import detect_no_progress


def test_flags_repeated_identical_output():
    hist = ["Idle·gated 无变化·等你明示信号"] * 4
    r = detect_no_progress(hist, window=3)
    assert r["stuck"] is True
    assert r["repeats"] >= 3
    assert "hint" in r and r["hint"]
    print("✅ repeated identical output → stuck")


def test_near_identical_still_stuck():
    # 措辞微变但实质相同 → 仍算空转(normalized 相似度高)
    hist = [
        "Idle·gated 无变化·等你明示信号。",
        "Idle · gated 无变化 · 等你明示信号",
        "idle gated 无变化 等你明示信号",
    ]
    r = detect_no_progress(hist, window=3)
    assert r["stuck"] is True
    print("✅ near-identical (whitespace/punct) → stuck")


def test_progress_when_output_changes():
    hist = ["did task A and committed", "found bug B, fixed it", "deployed C, verified live"]
    r = detect_no_progress(hist, window=3)
    assert r["stuck"] is False
    print("✅ genuinely different outputs → not stuck")


def test_tool_call_signals_progress():
    # 即使文本相似·只要这轮有新 tool 调用 → 不算空转
    hist = ["Idle·gated", "Idle·gated", "Idle·gated"]
    r = detect_no_progress(hist, window=3, made_tool_call=True)
    assert r["stuck"] is False
    print("✅ new tool call → progress (not stuck)")


def test_short_history_not_stuck():
    assert detect_no_progress(["a"], window=3)["stuck"] is False
    assert detect_no_progress([], window=3)["stuck"] is False
    print("✅ insufficient history → not stuck")


if __name__ == "__main__":
    tests = [
        test_flags_repeated_identical_output,
        test_near_identical_still_stuck,
        test_progress_when_output_changes,
        test_tool_call_signals_progress,
        test_short_history_not_stuck,
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
    print(f"\n✅ {len(tests)}/{len(tests)} no-progress tests pass")
