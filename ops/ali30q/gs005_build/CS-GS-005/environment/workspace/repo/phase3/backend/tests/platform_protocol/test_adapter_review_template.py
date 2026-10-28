from __future__ import annotations

from pathlib import Path

TEMPLATE_PATH = (
    Path(__file__).parents[4]
    / "docs"
    / "plans"
    / "2026-08-03-platform-protocol-v2-adapter-review-template.md"
)


def test_adapter_review_template_is_complete_and_fail_closed() -> None:
    content = TEMPLATE_PATH.read_text(encoding="utf-8")

    for required_section in (
        "Source authority",
        "Eligible source event",
        "Opaque reference derivation",
        "Allowed Protocol operation kind",
        "Receipt interpretation",
        "Write-back authority",
        "Source read-back proof",
        "Retention policy",
        "Rollback path",
        "Rejection conditions",
    ):
        assert required_section in content

    for required_rejection in (
        "raw source evidence",
        "Platform protocol state as a domain decision",
        "source read-back proof",
        "Platform decide a domain write-back",
    ):
        assert required_rejection in content

    assert (
        "No adapter is authorized without an approved owner-domain proposal." in content
    )
