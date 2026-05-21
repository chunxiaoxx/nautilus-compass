"""Gemini Flash opt-in judge smoke tests · NO actual API call (env disabled)."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ensure env not set during test
os.environ.pop("COMPASS_USE_GEMINI_FLASH", None)

from judges.gemini_flash import (
    GeminiFlashJudge, is_enabled, get_credentials_path,
    OPT_IN_ENV, DEFAULT_MODEL, DEFAULT_PROJECT, DEFAULT_LOCATION,
)


def test_1_default_disabled():
    os.environ.pop(OPT_IN_ENV, None)
    assert not is_enabled()
    print("OK 1 default disabled")


def test_2_env_enabled():
    os.environ[OPT_IN_ENV] = "1"
    try:
        assert is_enabled()
    finally:
        os.environ.pop(OPT_IN_ENV, None)
    print("OK 2 env=1 enables")


def test_3_env_truthy_variants():
    for val in ("1", "true", "yes", "on", "True", "YES"):
        os.environ[OPT_IN_ENV] = val
        try:
            assert is_enabled(), f"failed for {val!r}"
        finally:
            os.environ.pop(OPT_IN_ENV, None)
    print("OK 3 truthy variants accepted")


def test_4_env_falsy_disabled():
    for val in ("0", "false", "no", "off", ""):
        os.environ[OPT_IN_ENV] = val
        try:
            assert not is_enabled(), f"should be disabled for {val!r}"
        finally:
            os.environ.pop(OPT_IN_ENV, None)
    print("OK 4 falsy values disabled")


def test_5_constants():
    assert DEFAULT_MODEL == "gemini-2.5-flash"
    assert DEFAULT_PROJECT == "chunxiao-vm-260414"
    assert DEFAULT_LOCATION == "us-central1"
    print("OK 5 constants match SPEC")


def test_6_judge_init_lazy():
    j = GeminiFlashJudge()
    assert j._client is None  # lazy
    assert j.model == DEFAULT_MODEL
    assert not j.enabled  # env not set
    print("OK 6 judge init lazy + disabled by default")


def test_7_generate_returns_none_when_disabled():
    os.environ.pop(OPT_IN_ENV, None)
    j = GeminiFlashJudge()
    r = j.generate("hello")
    assert r is None
    assert j._init_error is not None
    assert OPT_IN_ENV in j._init_error
    print("OK 7 generate returns None when disabled")


def test_8_judge_method_returns_none_when_disabled():
    os.environ.pop(OPT_IN_ENV, None)
    j = GeminiFlashJudge()
    r = j.judge("Q?", "candidate", reference="ref")
    assert r is None
    print("OK 8 judge() returns None when disabled")


def test_9_credentials_path_env_priority():
    # COMPASS_GEMINI_SA_PATH should NOT be picked if file missing
    os.environ["COMPASS_GEMINI_SA_PATH"] = "/nonexistent/sa.json"
    try:
        p = get_credentials_path()
        assert p is None or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    finally:
        os.environ.pop("COMPASS_GEMINI_SA_PATH", None)
    print("OK 9 credentials path nonexistent returns None")


def test_10_lazy_init_does_not_crash_when_disabled():
    os.environ.pop(OPT_IN_ENV, None)
    j = GeminiFlashJudge()
    # Calling _lazy_init when disabled should set error · not raise
    ok = j._lazy_init()
    assert ok is False
    assert "disabled" in (j._init_error or "")
    print("OK 10 lazy init no crash when disabled")


if __name__ == "__main__":
    tests = [test_1_default_disabled, test_2_env_enabled, test_3_env_truthy_variants,
             test_4_env_falsy_disabled, test_5_constants, test_6_judge_init_lazy,
             test_7_generate_returns_none_when_disabled,
             test_8_judge_method_returns_none_when_disabled,
             test_9_credentials_path_env_priority, test_10_lazy_init_does_not_crash_when_disabled]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} gemini_flash judge smoke pass")
