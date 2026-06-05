"""v3.5+ · central registry for opt-in LLM features.

Sprint 0 deliverable (per plan_compass_v35_full_fusion §2.0 / §3).

CRITICAL CONSTRAINT (per user 2026-04-28 rule + daemon.py:12-13 verbatim):
  "永远只 BGE local · 不读 LLM key 默认情况 · 完全本地"

All flags here default OFF. v2.0.1 byte-equal behavior preserved when no
flag is set. Each Sprint (3-7) wires its own feature behind one flag and
adds gate-tests in tests/test_<flag>.py. Disabling all flags reverts to
v2.0.1 semantics — this invariant is checked by the Sprint 0 README block
("default-off byte-equal" promise) and Sprint 8 release gate.

Pattern (mirrors judges/gemini_flash.py:30-33):
  · OPT_IN env truthy = "1" | "true" | "yes" | "on" (case-insensitive · stripped)
  · Anything else = disabled
  · Never reads the flag at import time · always read per-call (so tests can
    monkey-patch os.environ between assertions)

NEVER call enabled-path code from ingest · NEVER from default recall ·
CALL ONLY when explicit Sprint feature explicitly opts in.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List

# ---------------------------------------------------------------------------
# Flag registry · 5 v3.5 opt-in LLM features + gemini_flash mirror for audit.
# Adding a flag here costs nothing — wire-up happens in the owning Sprint.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OptInFlag:
    name: str             # short stable identifier (used in logs / get_active_flags)
    env_var: str          # environment variable that activates the flag
    sprint: int           # owning Sprint per plan_compass_v35_full_fusion §2
    tier: int             # tier 1-4 per plan §3 (1=session-end · 4=runtime hot path)
    description: str      # one-line what it does
    paper_claim: str      # which paper3 v2 claim it backs (for §6 audit reconcile)


_FLAGS: Dict[str, OptInFlag] = {
    "llm_resolve": OptInFlag(
        name="llm_resolve",
        env_var="COMPASS_USE_LLM_RESOLVE",
        sprint=3,
        tier=1,
        description="Session-end LLM contradiction resolution · writes confidence.contradicted_by",
        paper_claim="§6(a) cross-session truth maintenance",
    ),
    "llm_verify": OptInFlag(
        name="llm_verify",
        env_var="COMPASS_USE_LLM_VERIFY",
        sprint=4,
        tier=4,
        description="Anti-confabulation · LLM must cite memory id · refuse if confidence<0.5",
        paper_claim="§6(c) first verifiable cite trail",
    ),
    "llm_drift_pay": OptInFlag(
        name="llm_drift_pay",
        env_var="COMPASS_USE_LLM_DRIFT_PAY",
        sprint=5,
        tier=4,
        description="Drift × outcome feedback · LLM adjusts anchor weights",
        paper_claim="§6(d) first dynamic anchor system",
    ),
    "llm_reflect": OptInFlag(
        name="llm_reflect",
        env_var="COMPASS_USE_LLM_REFLECT",
        sprint=6,
        tier=3,
        description="Periodic self-reflection · LLM emits tier=semantic meta-entries",
        paper_claim="§6(b) emergent semantic memory layer",
    ),
    "llm_econ": OptInFlag(
        name="llm_econ",
        env_var="COMPASS_USE_LLM_ECON",
        sprint=7,
        tier=4,
        description="Memory-as-economy · per-entry NAU read cost · budget-gated access",
        paper_claim="§6(e) economic memory pressure",
    ),
    # Mirrored for audit completeness · owned by judges/gemini_flash.py:23
    "gemini_flash_judge": OptInFlag(
        name="gemini_flash_judge",
        env_var="COMPASS_USE_GEMINI_FLASH",
        sprint=0,
        tier=0,
        description="Benchmark/paper judge only (v1.7.1+) · NOT for runtime recall",
        paper_claim="paper1/paper2 cross-LLM ablation",
    ),
    # v2.3.0 · opt-in gemini query rewrite before recall · owned by query_rewrite.py
    "query_rewrite": OptInFlag(
        name="query_rewrite",
        env_var="COMPASS_PROD_QUERY_REWRITE",
        sprint=0,
        tier=4,
        description="Rewrite recall query via Gemini Flash before retrieval · "
                    "also requires COMPASS_USE_GEMINI_FLASH · fails back to original query",
        paper_claim="recall-quality wiring (not a paper3 claim)",
    ),
}


# Public stable names · external code should import these · not the dict
RESOLVE = "llm_resolve"
VERIFY = "llm_verify"
DRIFT_PAY = "llm_drift_pay"
REFLECT = "llm_reflect"
ECON = "llm_econ"
GEMINI_FLASH_JUDGE = "gemini_flash_judge"
QUERY_REWRITE = "query_rewrite"


_TRUTHY = ("1", "true", "yes", "on")


def _is_truthy(value: str) -> bool:
    return value.strip().lower() in _TRUTHY


def is_enabled(flag: str) -> bool:
    """Return True iff the flag's env var is set to a truthy value.

    Reads os.environ on every call (no caching) so tests can flip flags
    between assertions without module-reload tricks.
    """
    spec = _FLAGS.get(flag)
    if spec is None:
        raise KeyError(
            f"Unknown opt-in flag {flag!r} · registered: {sorted(_FLAGS)}"
        )
    return _is_truthy(os.environ.get(spec.env_var, ""))


def get_flag(flag: str) -> OptInFlag:
    """Return the OptInFlag spec · raises KeyError if unknown."""
    spec = _FLAGS.get(flag)
    if spec is None:
        raise KeyError(
            f"Unknown opt-in flag {flag!r} · registered: {sorted(_FLAGS)}"
        )
    return spec


def list_flags() -> List[OptInFlag]:
    """Return all registered flags · stable order by Sprint then name."""
    return sorted(_FLAGS.values(), key=lambda f: (f.sprint, f.name))


def get_active_flags() -> List[str]:
    """Return list of currently-enabled flag names · for logging / audit."""
    return [name for name in _FLAGS if is_enabled(name)]


def default_off_invariant() -> bool:
    """True iff *no* opt-in flag is currently set.

    Sprint 8 release gate calls this in CI · default-off byte-equal promise
    requires the test harness to run with the invariant True (otherwise the
    'v2.0.1 byte-equal' assertion is vacuous).
    """
    return len(get_active_flags()) == 0


__all__ = [
    "OptInFlag",
    "RESOLVE",
    "VERIFY",
    "DRIFT_PAY",
    "REFLECT",
    "ECON",
    "GEMINI_FLASH_JUDGE",
    "is_enabled",
    "get_flag",
    "list_flags",
    "get_active_flags",
    "default_off_invariant",
]
