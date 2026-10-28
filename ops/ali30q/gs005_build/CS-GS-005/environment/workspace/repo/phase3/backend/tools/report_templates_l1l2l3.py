"""Validation-report templates (flywheel spec v0).

One shared section tree, three progressive render levels.

Levels:
    L1 -> sections 0..3
    L2 -> sections 0..4
    L3 -> sections 0..7

Each section holds numbered slots.  A slot is a dict::

    {"key": str, "required": bool, "dtype": str, "fill_hint": str}

``render(level, fills)`` returns Markdown.  Slots absent from ``fills``
render as ``[SLOT key]`` so reviewers can see what is still missing.
"""

from typing import Dict, List, Mapping


# --- slot factory --------------------------------------------------------

def _slot(key: str, required: bool, dtype: str, hint: str) -> dict:
    return {
        "key": key,
        "required": required,
        "dtype": dtype,
        "fill_hint": hint,
    }


# --- shared section tree -------------------------------------------------
# Index -> {"title": str, "slots": [slot, ...]}
# Slot keys use ``"<section>.<field>"`` so they read cleanly when rendered.

_SUMMARY = {
    "title": "Summary",
    "slots": [
        _slot("summary.usable", True, "bool", "Pass/fail headline verdict."),
        _slot("summary.price_range", False, "tuple", "(low, high) numeric band."),
        _slot("summary.gaps", False, "list[str]", "Known data or method gaps."),
    ],
}

_SCOPE = {
    "title": "Scope",
    "slots": [
        _slot("scope.client", True, "str", "Client identifier."),
        _slot("scope.batch_id", True, "str", "Batch or job id."),
        _slot("scope.license", True, "str", "Licence clause code."),
        _slot("scope.exclusions", False, "list[str]", "Explicitly out of scope."),
    ],
}

_DATA_PROFILE = {
    "title": "Data Profile",
    "slots": [
        _slot("data_profile.scale", True, "int", "Sample count."),
        _slot("data_profile.composition", False, "str", "Class / segment mix."),
        _slot("data_profile.spec_check", False, "str", "Schema conformance note."),
    ],
}

_QUALITY = {
    "title": "Quality",
    "slots": [
        _slot("quality.d2_frame_integrity", True, "float", "Frame-level integrity score."),
        _slot("quality.d3_traj_integrity", True, "float", "Trajectory integrity score."),
        _slot("quality.guardrail_fallbacks", False, "int", "Number of guardrail fallbacks."),
    ],
}

_UTILITY = {
    "title": "Utility",
    "slots": [
        _slot("utility.mapping_signals", False, "dict", "Probe result per mapping."),
        _slot("utility.trainability_probe", False, "float", "Trainability probe score."),
        _slot("utility.cross_findings", False, "list[str]", "Findings from cross-checks."),
    ],
}

_VERIFICATION = {
    "title": "Verification",
    "slots": [
        _slot("verification.wm_a_design", True, "str", "Watermark-A design summary."),
        _slot("verification.gain_reading", True, "float", "Watermark gain measurement."),
    ],
}

_VALUATION = {
    "title": "Valuation",
    "slots": [
        _slot("valuation.price_range", True, "tuple", "Final price band."),
        _slot("valuation.gap_list", False, "list[str]", "Items blocking close."),
        _slot("valuation.stop_line", False, "str", "Hard stop / do-not-cross."),
    ],
}

_METHOD = {
    "title": "Method",
    "slots": [
        _slot("method.criteria_version", True, "str", "Criteria spec version."),
        _slot("method.compass_receipt", False, "str", "Compass tool receipt hash."),
        _slot("method.audit", False, "str", "Audit trail reference."),
    ],
}


SECTIONS: Dict[int, dict] = {
    0: _SUMMARY,
    1: _SCOPE,
    2: _DATA_PROFILE,
    3: _QUALITY,
    4: _UTILITY,
    5: _VERIFICATION,
    6: _VALUATION,
    7: _METHOD,
}


# --- levels --------------------------------------------------------------
# Each level names the section indices it includes.

LEVELS: Dict[str, List[int]] = {
    "L1": [0, 1, 2, 3],
    "L2": [0, 1, 2, 3, 4],
    "L3": [0, 1, 2, 3, 4, 5, 6, 7],
}


# --- renderer ------------------------------------------------------------

def render(level: str, fills: Mapping[str, object]) -> str:
    """Render the validation report for ``level`` using ``fills``.

    Unfilled slots are rendered as ``[SLOT key]``.
    Raises ``ValueError`` for unknown levels (e.g. ``"L4"``).
    """
    if level not in LEVELS:
        raise ValueError(
            f"unknown level: {level!r}; valid={sorted(LEVELS)}"
        )

    # tolerate non-mutable mappings without mutating the caller's input
    fills_map = dict(fills)

    out: List[str] = [f"# Validation Report — {level}", ""]

    for idx in LEVELS[level]:
        section = SECTIONS[idx]
        out.append(f"## {idx}. {section['title']}")
        out.append("")
        for slot in section["slots"]:
            key = slot["key"]
            short = key.split(".", 1)[-1]
            value = fills_map.get(key)
            if value is None:
                marker = f"[SLOT {key}]"
                out.append(
                    f"- **{short}**: {marker}  _hint: {slot['fill_hint']}_"
                )
            else:
                out.append(f"- **{short}**: {value}")
        out.append("")

    return "\n".join(out).rstrip() + "\n"


__all__ = ["LEVELS", "SECTIONS", "render"]