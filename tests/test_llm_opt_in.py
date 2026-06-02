"""Sprint 0 deliverable · tests for llm_opt_in central registry.

Per plan_compass_v35_full_fusion §2.0 gate:
  · branch built ✅ (Step 1 / #1)
  · env-gated infra exists ← THIS file
  · baseline snapshot ⏳
  · README behavior diff block ⏳
  · subset size verdict ✅ (n=133 multi-session > 50 noise floor)

These tests must all pass before Sprint 1 starts. They also serve as the
"default-off byte-equal" CI gate referenced by Sprint 8 release.
"""
from __future__ import annotations

import pytest

import llm_opt_in as opt_in


# ---------------------------------------------------------------------------
# Helpers · isolate env per test so prior state doesn't leak.
# ---------------------------------------------------------------------------

ALL_ENVS = [f.env_var for f in opt_in.list_flags()]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for env in ALL_ENVS:
        monkeypatch.delenv(env, raising=False)
    yield


# ---------------------------------------------------------------------------
# _is_truthy
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "YES", "on", "On", " 1 ", "true\n"])
def test_is_truthy_accepts_canonical_truthy(value):
    assert opt_in._is_truthy(value) is True


@pytest.mark.parametrize("value", ["0", "false", "no", "off", "", "  ", "2", "enabled", "y"])
def test_is_truthy_rejects_anything_else(value):
    assert opt_in._is_truthy(value) is False


# ---------------------------------------------------------------------------
# is_enabled · default off · honors env · KeyError on unknown
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("flag", [
    opt_in.RESOLVE, opt_in.VERIFY, opt_in.DRIFT_PAY,
    opt_in.REFLECT, opt_in.ECON, opt_in.GEMINI_FLASH_JUDGE,
])
def test_is_enabled_default_off(flag):
    assert opt_in.is_enabled(flag) is False


def test_is_enabled_honors_env_var(monkeypatch):
    monkeypatch.setenv("COMPASS_USE_LLM_VERIFY", "1")
    assert opt_in.is_enabled(opt_in.VERIFY) is True


def test_is_enabled_rejects_non_truthy_env(monkeypatch):
    monkeypatch.setenv("COMPASS_USE_LLM_RESOLVE", "0")
    monkeypatch.setenv("COMPASS_USE_LLM_VERIFY", "maybe")
    assert opt_in.is_enabled(opt_in.RESOLVE) is False
    assert opt_in.is_enabled(opt_in.VERIFY) is False


def test_is_enabled_unknown_flag_raises():
    with pytest.raises(KeyError, match="Unknown opt-in flag"):
        opt_in.is_enabled("llm_telepathy")


def test_is_enabled_reads_env_per_call(monkeypatch):
    """Must NOT cache · tests rely on flipping env mid-run."""
    assert opt_in.is_enabled(opt_in.ECON) is False
    monkeypatch.setenv("COMPASS_USE_LLM_ECON", "1")
    assert opt_in.is_enabled(opt_in.ECON) is True
    monkeypatch.delenv("COMPASS_USE_LLM_ECON")
    assert opt_in.is_enabled(opt_in.ECON) is False


# ---------------------------------------------------------------------------
# get_flag / list_flags · registry shape
# ---------------------------------------------------------------------------

def test_get_flag_returns_spec():
    flag = opt_in.get_flag(opt_in.DRIFT_PAY)
    assert flag.env_var == "COMPASS_USE_LLM_DRIFT_PAY"
    assert flag.sprint == 5
    assert flag.tier == 4


def test_get_flag_unknown_raises():
    with pytest.raises(KeyError):
        opt_in.get_flag("llm_imaginary")


def test_list_flags_includes_all_v35_features():
    names = {f.name for f in opt_in.list_flags()}
    expected = {opt_in.RESOLVE, opt_in.VERIFY, opt_in.DRIFT_PAY,
                opt_in.REFLECT, opt_in.ECON, opt_in.GEMINI_FLASH_JUDGE}
    assert expected.issubset(names), f"missing: {expected - names}"


def test_list_flags_sorted_by_sprint_then_name():
    flags = opt_in.list_flags()
    keys = [(f.sprint, f.name) for f in flags]
    assert keys == sorted(keys)


def test_every_public_const_resolves_to_registered_flag():
    """Catches typo in module-level RESOLVE/VERIFY/... constants."""
    for const in (opt_in.RESOLVE, opt_in.VERIFY, opt_in.DRIFT_PAY,
                  opt_in.REFLECT, opt_in.ECON, opt_in.GEMINI_FLASH_JUDGE):
        assert opt_in.get_flag(const).name == const


def test_env_var_names_unique():
    envs = [f.env_var for f in opt_in.list_flags()]
    assert len(envs) == len(set(envs)), "duplicate env var registered"


# ---------------------------------------------------------------------------
# get_active_flags · default-off byte-equal invariant
# ---------------------------------------------------------------------------

def test_get_active_flags_empty_by_default():
    assert opt_in.get_active_flags() == []


def test_default_off_invariant_holds_when_no_env_set():
    assert opt_in.default_off_invariant() is True


def test_default_off_invariant_breaks_when_any_flag_set(monkeypatch):
    monkeypatch.setenv("COMPASS_USE_LLM_REFLECT", "yes")
    assert opt_in.default_off_invariant() is False
    assert opt_in.get_active_flags() == [opt_in.REFLECT]


def test_get_active_flags_returns_multiple(monkeypatch):
    monkeypatch.setenv("COMPASS_USE_LLM_RESOLVE", "1")
    monkeypatch.setenv("COMPASS_USE_LLM_ECON", "on")
    active = set(opt_in.get_active_flags())
    assert active == {opt_in.RESOLVE, opt_in.ECON}
