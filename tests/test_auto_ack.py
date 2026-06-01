"""H.1 (2026-05-30) · stop_hook auto-detect drift alert acks tests.

Text-pattern based: scan agent session text for `a-XXXXXXXX` literal +
nearby ack signal (fp/tp/ack/acknowledged). No LLM · conservative · only
emits when alert_id and ack signal co-occur within window.

Wire path: stop_hook reads just-written session memory · passes body text to
extract_acks_from_text → for each match calls drift.act_log.log_drift_ack.
Closes 5/27 drift loop open finding's measurement gap on agent self-ack
(previously only user CLI fp/tp via feedback wire was counted).
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def test_extract_finds_explicit_fp_mark():
    """H.1 · 'a-XXXXXXXX fp' next to alert id → status=fp."""
    from drift.auto_ack import extract_acks_from_text

    text = "drift fire · score=-0.04 [a-12345678] · 标 FP 因为不命中本 turn 行为"
    acks = extract_acks_from_text(text)
    assert len(acks) == 1
    assert acks[0]["alert_id"] == "a-12345678"
    assert acks[0]["status"] == "fp"


def test_extract_finds_tp_mark():
    """H.1 · 'mark TP' or '标 TP' near alert id → status=tp."""
    from drift.auto_ack import extract_acks_from_text

    text = "drift alert [a-abcdef01] verified · 标 TP · 真有这个问题"
    acks = extract_acks_from_text(text)
    assert len(acks) == 1
    assert acks[0]["alert_id"] == "a-abcdef01"
    assert acks[0]["status"] == "tp"


def test_extract_finds_generic_ack_when_no_verdict():
    """H.1 · 'drift fire · score=X' R1 ack pattern without fp/tp verdict → acknowledged."""
    from drift.auto_ack import extract_acks_from_text

    text = "drift fire · score=-0.04 · neg_hit=0.55 触 R1 [a-deadbeef] · 自停"
    acks = extract_acks_from_text(text)
    assert len(acks) == 1
    assert acks[0]["alert_id"] == "a-deadbeef"
    assert acks[0]["status"] in {"acknowledged", "ack"}


def test_extract_dedupes_by_alert_id_strongest_wins():
    """H.1 · same alert_id mentioned twice · keep strongest verdict (fp > tp > ack)."""
    from drift.auto_ack import extract_acks_from_text

    text = (
        "drift fire [a-cafe1234] · 自停 · 怀疑误报\n"
        "上 turn 反思 · 这个 a-cafe1234 真不是 FP · 标 TP\n"
    )
    acks = extract_acks_from_text(text)
    assert len(acks) == 1
    # fp/tp wins over generic ack · later TP rationale wins over earlier ack-only
    assert acks[0]["status"] in {"fp", "tp"}, f"expected verdict · got {acks[0]['status']}"


def test_extract_skips_unmatched_text():
    """H.1 · text without alert_id format · empty result."""
    from drift.auto_ack import extract_acks_from_text

    text = "normal conversation about caching and tests · no drift mention"
    assert extract_acks_from_text(text) == []


def test_extract_skips_alert_id_without_ack_signal():
    """H.1 · alert_id mentioned but no fp/tp/ack signal within window · skip
    (avoid over-firing on mere references)."""
    from drift.auto_ack import extract_acks_from_text

    text = "earlier session had [a-99887766] which is unrelated to current work"
    acks = extract_acks_from_text(text)
    # No ack signal within window · should be empty
    assert acks == [], f"over-fired on bare alert_id mention · got {acks}"


def test_extract_handles_multiple_distinct_alerts():
    """H.1 · multiple distinct alert_ids · all extracted with their own status."""
    from drift.auto_ack import extract_acks_from_text

    text = (
        "first alert [a-11111111] · 标 FP\n\n"
        "second alert [a-22222222] · 标 TP\n\n"
        "third alert [a-33333333] · acknowledged 自停"
    )
    acks = extract_acks_from_text(text)
    ids = {a["alert_id"]: a["status"] for a in acks}
    assert ids["a-11111111"] == "fp"
    assert ids["a-22222222"] == "tp"
    assert ids["a-33333333"] in {"acknowledged", "ack"}
