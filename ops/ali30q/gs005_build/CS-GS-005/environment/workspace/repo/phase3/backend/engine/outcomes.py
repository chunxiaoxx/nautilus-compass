"""Stage 1 · engine cycle outcome metric helpers.

Per docs/plans/2026-05-25-engine-metric-loop-stage1-design.md.

Three pure functions:
  - parse_spec_meta · extract optional Spec-Meta block from task string
  - compute_composite · null-degrade composite score 0-1
  - classify · 4-status outcome from ShipResult + tests + drift

Invariant: all functions are pure / no I/O / no exceptions raised.
"""
from __future__ import annotations

import re
from typing import Any

# Match a 'Spec-Meta:' block followed by indented `<key>: <value>` lines.
_SPEC_META_RE = re.compile(
    r"Spec-Meta:[ \t]*\n((?:[ \t]+[A-Za-z_][\w]*:[ \t]*\S+[ \t]*\n?)+)",
    re.MULTILINE,
)
_SPEC_FIELD_RE = re.compile(r"[ \t]+([A-Za-z_][\w]*)[ \t]*:[ \t]*(\S+)")


def parse_spec_meta(task: str) -> dict[str, int | None]:
    """Permissive parser per plan-phase decision #3 · malformed → NULL.

    Recognised fields: expected_added · expected_removed.
    Returns {"expected_added": int|None, "expected_removed": int|None}.
    """
    out: dict[str, int | None] = {"expected_added": None, "expected_removed": None}
    if not task:
        return out
    m = _SPEC_META_RE.search(task)
    if not m:
        return out
    body = m.group(1)
    for fm in _SPEC_FIELD_RE.finditer(body):
        key, val = fm.group(1), fm.group(2)
        if key in out:
            try:
                out[key] = int(val)
            except ValueError:
                # Permissive: leave as None on parse failure.
                pass
    return out


def compute_composite(
    semantic: bool | None,
    tests: bool | None,
    drift: float | None,
) -> float:
    """Composite 0-1 score · null-degrade · drift deviation-from-1 clamped.

    - All three signals available → mean of 3
    - Some signals None → mean over available
    - All None → 0.0 (nothing measured)

    Drift signal · drift_ratio = actual_lines / max(1, expected_lines):
        drift = 1.0 (perfect match)        → contribute 1.0
        drift = 0.5 (under-shipped 50%)    → contribute 0.5
        drift = 2.0 (over-shipped 2x)      → contribute 0.0 (clamped)
        drift = 0.0 (nothing shipped)      → contribute 0.0
    Formula: 1 - abs(1 - drift) clamped to [0, 1].
    """
    signals: list[float] = []
    if semantic is not None:
        signals.append(1.0 if semantic else 0.0)
    if tests is not None:
        signals.append(1.0 if tests else 0.0)
    if drift is not None:
        signals.append(max(0.0, min(1.0, 1.0 - abs(1.0 - drift))))
    if not signals:
        return 0.0
    return round(sum(signals) / len(signals), 3)


def classify(
    result: Any,
    tests_pass: bool | None,
    drift: float | None,
) -> str:
    """4-status outcome from ShipResult + side signals.

    Statuses (mutually exclusive):
      - deadletter · ship pipeline could not even parse / runtime crash
      - fail · LLM produced blocks but apply gate refused (check failed)
      - partial · applied but at least one quality signal red
      - success · applied + all available signals green
    """
    # ShipResult is a dataclass; access attributes defensively.
    errors = getattr(result, "errors", None) or []
    err_str = " ".join(errors).lower()
    if "no parseable file blocks" in err_str or "runtime_crash" in err_str:
        return "deadletter"

    applied = bool(getattr(result, "applied", False))
    check_result = getattr(result, "check_result", {}) or {}
    check_passed = bool(check_result.get("passed", False))

    if not applied:
        return "fail"

    # applied = True · grade quality
    if not check_passed:
        return "partial"
    if tests_pass is False:
        return "partial"
    if drift is not None and drift > 1.5:
        # Over-shipping: > 1.5x expected diff size.
        return "partial"
    return "success"


def is_deadletter(result: Any) -> bool:
    """True iff classify(result, *) would route to deadletter regardless of signals."""
    return classify(result, None, None) == "deadletter"


def compute_drift_ratio(
    actual_added: int | None,
    actual_removed: int | None,
    expected_added: int | None,
    expected_removed: int | None,
) -> float | None:
    """drift_ratio = actual_total / max(1, expected_total) · None if signal unavailable."""
    if expected_added is None or actual_added is None:
        return None
    expected_total = (expected_added or 0) + (expected_removed or 0)
    actual_total = (actual_added or 0) + (actual_removed or 0)
    return round(actual_total / max(1, expected_total), 3)