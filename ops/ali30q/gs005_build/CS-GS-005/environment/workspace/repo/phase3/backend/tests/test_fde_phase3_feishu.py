import json
import importlib.util
import inspect
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import urlparse

import pytest

import services.fde_phase3_feishu as phase3_feishu
from services.fde_phase3_feishu import (
    ExportReadback,
    FieldMap,
    FieldOwner,
    FieldRule,
    PredecessorReadback,
    ReviewContext,
    ReviewStatus,
    Transition,
    probe_schema,
)

EVIDENCE_HASH = "sha256:" + "a" * 64
MANIFEST_HASH = "sha256:" + "b" * 64


def review_context(status, **overrides):
    values = {
        "review_record_id": "rec_review_1",
        "task_record_id": "rec_task_1",
        "attempt_record_id": "rec_attempt_1",
        "validated_reviewer_id": "reviewer_1",
        "review_status": status,
    }
    values.update(overrides)
    return ReviewContext(**values)


def export_readback(**overrides):
    values = {
        "task_record_id": "rec_task_1",
        "attempt_record_id": "rec_attempt_1",
        "review_record_id": "rec_review_1",
        "export_record_id": "rec_export_1",
        "business_status": "accepted",
        "export_status": "canonical_pending",
        "p0_passed": True,
        "feedback_class": "accepted",
        "buyer_verdict": "Gold",
        "redaction_passed": True,
        "is_repair": False,
    }
    values.update(overrides)
    if values["is_repair"] and "buyer_verdict" not in overrides:
        values["buyer_verdict"] = "Repair"
    return ExportReadback(**values)


def predecessor_readback(**overrides):
    values = {
        "task_record_id": "rec_task_1",
        "attempt_record_id": "rec_attempt_1",
        "business_status": "repair_required",
    }
    values.update(overrides)
    return PredecessorReadback(**values)


def field_map_with_phase3_roles():
    return FieldMap(
        [
            FieldRule("submission_text", FieldOwner.EXTERNAL, "专家提交"),
            FieldRule("p0", FieldOwner.INTERNAL, "P0"),
            FieldRule("p0_status", FieldOwner.INTERNAL, "P0状态"),
            FieldRule("feedback_class", FieldOwner.INTERNAL, "反馈分类"),
            FieldRule("verdict", FieldOwner.INTERNAL, "最终判定"),
            FieldRule("buyer_feedback", FieldOwner.BUYER, "甲方反馈"),
            FieldRule("revision_of", FieldOwner.PROHIBITED, "返修血缘"),
            FieldRule("manifest_hash", FieldOwner.V5, "V5 manifest"),
            FieldRule("compass_receipt_hash", FieldOwner.COMPASS, "Compass 回执"),
        ]
    )


def test_field_map_rejects_duplicate_external_owner():
    rules = [
        FieldRule("buyer_verdict", FieldOwner.BUYER, "buyer_verdict"),
        FieldRule("buyer_verdict_copy", FieldOwner.BUYER, "buyer_verdict"),
    ]

    with pytest.raises(ValueError, match="duplicate external field"):
        FieldMap(rules)


def test_field_ownership_contract_cannot_be_mutated_after_approval():
    rule = FieldRule("submission_text", FieldOwner.EXTERNAL, "专家提交")
    mapping = FieldMap([rule])

    with pytest.raises(AttributeError):
        rule.logical_field = "other"
    with pytest.raises(AttributeError):
        mapping._rules = ()


def test_transition_direct_constructor_enforces_identity_and_state_rules():
    with pytest.raises(ValueError, match="record identity"):
        Transition("", "", "draft", "accepted")
    with pytest.raises(ValueError, match="not allowed"):
        Transition("rec_task_1", "rec_attempt_1", "draft", "accepted")


def test_repair_transition_requires_direct_predecessor():
    with pytest.raises(ValueError, match="PredecessorReadback"):
        Transition.repair(
            "rec_task_1",
            "rec_attempt_2",
            predecessor=None,
        )


@pytest.mark.parametrize(
    ("predecessor", "message"),
    [
        (predecessor_readback(task_record_id="rec_task_other"), "same task"),
        (predecessor_readback(business_status="accepted"), "repair_required"),
        (predecessor_readback(attempt_record_id="rec_attempt_2"), "new attempt"),
    ],
)
def test_repair_transition_rejects_invalid_predecessor_readback(predecessor, message):
    with pytest.raises(ValueError, match=message):
        Transition.repair(
            "rec_task_1",
            "rec_attempt_2",
            predecessor=predecessor,
        )


def test_direct_repair_transition_applies_predecessor_readback_rules():
    with pytest.raises(ValueError, match="PredecessorReadback"):
        Transition("rec_task_1", "rec_attempt_2", "repair_required", "assigned")
    with pytest.raises(ValueError, match="same task"):
        Transition(
            "rec_task_1",
            "rec_attempt_2",
            "repair_required",
            "assigned",
            predecessor=predecessor_readback(task_record_id="rec_task_other"),
        )
    with pytest.raises(ValueError, match="repair_required"):
        Transition(
            "rec_task_1",
            "rec_attempt_2",
            "repair_required",
            "assigned",
            predecessor=predecessor_readback(business_status="accepted"),
        )
    with pytest.raises(ValueError, match="new attempt"):
        Transition(
            "rec_task_1",
            "rec_attempt_1",
            "repair_required",
            "assigned",
            predecessor=predecessor_readback(),
        )


def test_advance_cannot_bypass_repair_lineage_validation():
    with pytest.raises(ValueError, match="repair"):
        Transition.advance(
            "rec_task_1",
            "rec_attempt_2",
            from_state="repair_required",
            to_state="assigned",
        )


def test_new_task_requires_explicit_task_specification_fields():
    mapping = FieldMap([])

    with pytest.raises(ValueError, match="missing new-task fields"):
        mapping.validate_new_task(
            {
                "title": "税务边界案例",
                "evidence_pack": "evidence-only-is-not-a-task",
            }
        )


def test_new_task_accepts_complete_specification_and_evidence_pack():
    mapping = FieldMap([])
    submission = {
        "title": "税务边界案例",
        "task_type": "case_analysis",
        "attachment_format_tags": ["pdf"],
        "source_materials": "controlled-attachment-ref",
        "expected_output": "structured-answer",
        "key_steps": "identify facts then calculate",
        "evidence_pack": "controlled-evidence-ref",
    }

    assert mapping.validate_new_task(submission) == submission


@pytest.mark.parametrize(
    ("actor", "updates"),
    [
        (FieldOwner.EXTERNAL, {"submission_text": "six-round summary"}),
        (FieldOwner.BUYER, {"buyer_feedback": "needs revision"}),
        (FieldOwner.V5, {"manifest_hash": MANIFEST_HASH}),
        (FieldOwner.COMPASS, {"compass_receipt_hash": "sha256:receipt"}),
    ],
)
def test_field_map_allows_only_its_owner_to_write_non_review_fields(actor, updates):
    field_map_with_phase3_roles().authorize_write(
        actor=actor,
        record_id="rec_attempt_1",
        updates=updates,
    )


@pytest.mark.parametrize(
    ("actor", "updates"),
    [
        (FieldOwner.EXTERNAL, {"p0": "pass"}),
        (FieldOwner.BUYER, {"submission_text": "overreach"}),
        (FieldOwner.V5, {"buyer_feedback": "overreach"}),
        (FieldOwner.COMPASS, {"verdict": "Gold"}),
        (FieldOwner.AUTOMATION, {"submission_text": "block must not write"}),
    ],
)
def test_field_map_rejects_unauthorized_writes(actor, updates):
    with pytest.raises(PermissionError):
        field_map_with_phase3_roles().authorize_write(
            actor=actor,
            record_id="rec_attempt_1",
            updates=updates,
        )


@pytest.mark.parametrize("field", ["p0", "p0_status"])
def test_p0_fields_require_internal_review_record_at_p0_review(field):
    mapping = field_map_with_phase3_roles()

    with pytest.raises(PermissionError, match="p0_review"):
        mapping.authorize_write(
            actor=FieldOwner.INTERNAL,
            record_id="rec_review_1",
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            updates={field: "pass"},
            review_context=review_context(ReviewStatus.BUYER_REVIEW),
        )

    mapping.authorize_write(
        actor=FieldOwner.INTERNAL,
        record_id="rec_review_1",
        task_record_id="rec_task_1",
        attempt_record_id="rec_attempt_1",
        updates={field: "pass"},
        review_context=review_context(ReviewStatus.P0_REVIEW),
    )


@pytest.mark.parametrize("field", ["feedback_class", "verdict"])
def test_buyer_review_fields_require_internal_review_record_at_buyer_review(field):
    mapping = field_map_with_phase3_roles()

    with pytest.raises(PermissionError, match="buyer_review"):
        mapping.authorize_write(
            actor=FieldOwner.INTERNAL,
            record_id="rec_review_1",
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            updates={field: "value"},
            review_context=review_context(ReviewStatus.P0_REVIEW),
        )

    mapping.authorize_write(
        actor=FieldOwner.INTERNAL,
        record_id="rec_review_1",
        task_record_id="rec_task_1",
        attempt_record_id="rec_attempt_1",
        updates={field: "value"},
        review_context=review_context(ReviewStatus.BUYER_REVIEW),
    )


def test_review_write_requires_matching_validated_context_not_a_boolean():
    mapping = field_map_with_phase3_roles()

    with pytest.raises(PermissionError, match="ReviewContext"):
        mapping.authorize_write(
            actor=FieldOwner.INTERNAL,
            record_id="rec_review_1",
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            updates={"p0": "pass"},
        )
    with pytest.raises(PermissionError, match="matching review record"):
        mapping.authorize_write(
            actor=FieldOwner.INTERNAL,
            record_id="rec_review_other",
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            updates={"p0": "pass"},
            review_context=review_context(ReviewStatus.P0_REVIEW),
        )
    with pytest.raises(ValueError, match="validated reviewer"):
        ReviewContext(
            review_record_id="rec_review_1",
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            validated_reviewer_id="",
            review_status=ReviewStatus.P0_REVIEW,
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"task_record_id": ""}, "task record identity"),
        ({"attempt_record_id": ""}, "attempt record identity"),
    ],
)
def test_review_context_requires_readback_task_and_attempt_anchors(overrides, message):
    with pytest.raises(ValueError, match=message):
        review_context(ReviewStatus.P0_REVIEW, **overrides)


@pytest.mark.parametrize(
    ("task_record_id", "attempt_record_id", "message"),
    [
        ("rec_task_other", "rec_attempt_1", "matching task"),
        ("rec_task_1", "rec_attempt_other", "matching attempt"),
    ],
)
def test_review_write_rejects_context_task_or_attempt_mismatch(
    task_record_id, attempt_record_id, message
):
    with pytest.raises(PermissionError, match=message):
        field_map_with_phase3_roles().authorize_write(
            actor=FieldOwner.INTERNAL,
            record_id="rec_review_1",
            task_record_id=task_record_id,
            attempt_record_id=attempt_record_id,
            updates={"p0_status": "pass"},
            review_context=review_context(ReviewStatus.P0_REVIEW),
        )


def test_revision_can_only_link_a_new_attempt_to_its_direct_predecessor():
    transition = Transition.repair(
        "rec_task_1",
        "rec_attempt_2",
        predecessor=predecessor_readback(),
    )

    assert transition.revision_of == "rec_attempt_1"
    assert transition.predecessor.attempt_record_id == "rec_attempt_1"
    assert transition.attempt_record_id == "rec_attempt_2"
    with pytest.raises(ValueError, match="new attempt"):
        Transition.repair(
            "rec_task_1",
            "rec_attempt_1",
            predecessor=predecessor_readback(),
        )


def test_compass_payload_default_denies_unapproved_business_and_review_fields():
    mapping = FieldMap(
        [
            FieldRule("p0_status", FieldOwner.INTERNAL, "P0"),
            FieldRule("buyer_verdict", FieldOwner.BUYER, "验收"),
            FieldRule("task_summary", FieldOwner.EXTERNAL, "任务摘要"),
        ]
    )

    assert mapping.compass_payload(
        {
            "p0_status": "pass",
            "buyer_verdict": "Gold",
            "task_summary": "redacted summary",
        }
    ) == {}


def test_compass_payload_exports_only_explicit_minimal_v3_fields():
    mapping = FieldMap(
        [
            FieldRule("event_id", FieldOwner.V5, "事件标识", compass_export=True),
            FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True),
            FieldRule("manifest_hash", FieldOwner.V5, "manifest", compass_export=True),
            FieldRule("task_summary", FieldOwner.EXTERNAL, "任务摘要"),
            FieldRule("raw_conversation", FieldOwner.PROHIBITED, "原始对话"),
        ]
    )

    assert mapping.compass_payload(
        {
            "event_id": "evt_1",
            "evidence_hash": EVIDENCE_HASH,
            "manifest_hash": MANIFEST_HASH,
            "task_summary": "redacted summary",
            "raw_conversation": "private transcript",
            "record_id": "rec_internal_only",
            "revision_of": "rec_prior_only",
        }
    ) == {
        "event_id": "evt_1",
        "evidence_hash": EVIDENCE_HASH,
        "manifest_hash": MANIFEST_HASH,
    }


@pytest.mark.parametrize("forbidden_field", ["task_summary", "buyer_identity_alias"])
def test_field_map_rejects_unapproved_or_sensitive_v3_export_aliases(forbidden_field):
    with pytest.raises(ValueError, match="v3|sensitive"):
        FieldMap(
            [
                FieldRule(
                    forbidden_field,
                    FieldOwner.V5,
                    forbidden_field,
                    compass_export=True,
                )
            ]
        )


@pytest.mark.parametrize(
    ("logical_field", "value"),
    [
        ("event_id", ""),
        ("event_id", "evt_raw evidence"),
        ("event_id", "evt_" + "x" * 81),
        ("event_id", "raw-evidence"),
        ("evidence_hash", 7),
        ("evidence_hash", "sha256:raw evidence"),
        ("evidence_hash", "sha256:" + "A" * 64),
        ("manifest_hash", "sha256:" + "a" * 63),
    ],
)
def test_v3_export_rejects_invalid_approved_field_values(logical_field, value):
    mapping = FieldMap(
        [FieldRule(logical_field, FieldOwner.V5, logical_field, compass_export=True)]
    )

    with pytest.raises(ValueError):
        mapping.compass_payload({logical_field: value})


@pytest.mark.parametrize(
    "sensitive_field",
    ["raw_conversation", "conversation_screenshot", "contact_information", "bank_account"],
)
def test_field_map_rejects_any_sensitive_compass_export_binding(sensitive_field):
    with pytest.raises(ValueError, match="sensitive"):
        FieldMap(
            [
                FieldRule(
                    sensitive_field,
                    FieldOwner.EXTERNAL,
                    sensitive_field,
                    compass_export=True,
                )
            ]
        )


def test_compass_receipt_is_writable_by_compass_but_never_reexported():
    mapping = FieldMap(
        [
            FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True),
            FieldRule("compass_receipt_hash", FieldOwner.COMPASS, "Compass 回执"),
        ]
    )

    assert mapping.compass_payload(
        {
            "evidence_hash": EVIDENCE_HASH,
            "compass_receipt_hash": "sha256:receipt",
        }
    ) == {"evidence_hash": EVIDENCE_HASH}


def test_v5_v3_payload_requires_eligible_readback_and_never_exports_identities():
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    with pytest.raises(ValueError, match="attempt record identity"):
        mapping.v5_v3_payload(
            export_readback=export_readback(),
            task_record_id="rec_task_1",
            attempt_record_id="",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id="task_v3_1",
            values={},
        )

    payload = mapping.v5_v3_payload(
        export_readback=export_readback(),
        task_record_id="rec_task_1",
        attempt_record_id="rec_attempt_1",
        review_record_id="rec_review_1",
        export_record_id="rec_export_1",
        task_id="task_v3_1",
        values={"evidence_hash": EVIDENCE_HASH},
    )

    assert payload == {
        "task_id": "task_v3_1",
        "fields": {"evidence_hash": EVIDENCE_HASH},
    }
    assert "record_id" not in payload


@pytest.mark.parametrize(
    "task_id",
    ["rec_task_1", "rec_attempt_1", "rec_review_1", "rec_export_1"],
)
def test_v5_v3_payload_rejects_any_export_readback_identity_as_task_id(task_id):
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    with pytest.raises(ValueError, match="must not equal a Bitable record identity"):
        mapping.v5_v3_payload(
            export_readback=export_readback(),
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id=task_id,
            values={"evidence_hash": EVIDENCE_HASH},
        )


@pytest.mark.parametrize(
    "task_id",
    [
        "",
        "rec_task_unrelated",
        "task_v3_",
        "task_v3_raw evidence",
        "task_v3_" + "x" * 81,
    ],
)
def test_v5_v3_payload_rejects_invalid_derived_task_id_format(task_id):
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    with pytest.raises(ValueError, match="restricted task_v3_ identifier format"):
        mapping.v5_v3_payload(
            export_readback=export_readback(),
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id=task_id,
            values={"evidence_hash": EVIDENCE_HASH},
        )


@pytest.mark.parametrize("identity_name", ["task_record_id", "attempt_record_id"])
def test_v5_v3_payload_rejects_repair_lineage_identity_as_task_id(identity_name):
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )
    predecessor = predecessor_readback()

    with pytest.raises(ValueError, match="must not equal a Bitable record identity"):
        mapping.v5_v3_payload(
            export_readback=export_readback(
                attempt_record_id="rec_attempt_2",
                is_repair=True,
                predecessor=predecessor,
            ),
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_2",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id=getattr(predecessor, identity_name),
            values={"evidence_hash": EVIDENCE_HASH},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"business_status": "p0_failed"}, "business status"),
        ({"business_status": "repair_required"}, "business status"),
        ({"export_status": "canonical_blocked"}, "export status"),
        ({"p0_passed": False}, "P0"),
        ({"feedback_class": ""}, "feedback_class"),
        ({"buyer_verdict": "Reject"}, "buyer verdict"),
        ({"redaction_passed": False}, "redaction"),
    ],
)
def test_v5_v3_payload_rejects_ineligible_readback(overrides, message):
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    with pytest.raises(ValueError, match=message):
        mapping.v5_v3_payload(
            export_readback=export_readback(**overrides),
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_1",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id="task_v3_1",
            values={"evidence_hash": EVIDENCE_HASH},
        )


def test_v5_v3_payload_rejects_readback_anchor_mismatch_and_missing_review():
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    with pytest.raises(ValueError, match="attempt record identity"):
        mapping.v5_v3_payload(
            export_readback=export_readback(),
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_other",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id="task_v3_1",
            values={"evidence_hash": EVIDENCE_HASH},
        )
    with pytest.raises(ValueError, match="review record identity"):
        export_readback(review_record_id="")


@pytest.mark.parametrize(
    ("predecessor", "message"),
    [
        (predecessor_readback(task_record_id="rec_task_other"), "same task"),
        (predecessor_readback(business_status="accepted"), "repair_required"),
        (predecessor_readback(attempt_record_id="rec_attempt_2"), "new attempt"),
    ],
)
def test_v5_v3_payload_rejects_invalid_repair_lineage(predecessor, message):
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    with pytest.raises(ValueError, match=message):
        mapping.v5_v3_payload(
            export_readback=export_readback(
                attempt_record_id="rec_attempt_2",
                is_repair=True,
                predecessor=predecessor,
            ),
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_2",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id="task_v3_1",
            values={"evidence_hash": EVIDENCE_HASH},
        )


def test_v5_v3_payload_accepts_complete_repair_lineage():
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    payload = mapping.v5_v3_payload(
        export_readback=export_readback(
            attempt_record_id="rec_attempt_2",
            is_repair=True,
            predecessor=predecessor_readback(),
        ),
        task_record_id="rec_task_1",
        attempt_record_id="rec_attempt_2",
        review_record_id="rec_review_1",
        export_record_id="rec_export_1",
        task_id="task_v3_2",
        values={"evidence_hash": EVIDENCE_HASH},
    )

    assert payload["fields"] == {"evidence_hash": EVIDENCE_HASH}


def test_v5_v3_payload_rejects_repair_without_predecessor_readback():
    mapping = FieldMap(
        [FieldRule("evidence_hash", FieldOwner.V5, "证据哈希", compass_export=True)]
    )

    with pytest.raises(ValueError, match="repair export requires"):
        mapping.v5_v3_payload(
            export_readback=export_readback(
                attempt_record_id="rec_attempt_2",
                is_repair=True,
            ),
            task_record_id="rec_task_1",
            attempt_record_id="rec_attempt_2",
            review_record_id="rec_review_1",
            export_record_id="rec_export_1",
            task_id="task_v3_2",
            values={"evidence_hash": EVIDENCE_HASH},
        )


def test_transition_allows_only_bounded_state_machine_and_requires_identities():
    transition = Transition.advance(
        "rec_task_1",
        "rec_attempt_1",
        from_state="assigned",
        to_state="evidence_submitted",
    )

    assert transition.to_state == "evidence_submitted"
    with pytest.raises(ValueError, match="not allowed"):
        Transition.advance(
            "rec_task_1",
            "rec_attempt_1",
            from_state="draft",
            to_state="accepted",
        )
    with pytest.raises(ValueError, match="record identity"):
        Transition.advance(
            "",
            "rec_attempt_1",
            from_state="assigned",
            to_state="evidence_submitted",
        )


class FakeSchemaClient:
    """A schema-only client that records every allowed probe call."""

    def __init__(self, tables=None, fields_by_table=None):
        self.calls = []
        self.tables = tables if tables is not None else [
            {
                "table_id": "tbl_task",
                "name": "任务",
                "records": [{"record_id": "rec_hidden", "raw_value": "ignore"}],
            },
            {"table_id": "tbl_review", "name": "审核"},
        ]
        self.fields_by_table = fields_by_table if fields_by_table is not None else {
            "tbl_task": [
                {
                    "field_id": "fld_title",
                    "field_name": "题目名称",
                    "type": 1,
                    "property": {
                        "options": [
                            {"id": "opt_draft", "name": "草稿", "color": 0},
                        ],
                        "raw_value": "ignore",
                    },
                    "raw_value": "ignore",
                },
            ],
            "tbl_review": [
                {
                    "field_id": "fld_p0",
                    "field_name": "P0",
                    "type": 3,
                    "property": {"options": []},
                },
            ],
        }

    def list_tables(self, base_token):
        self.calls.append("list_tables")
        return self.tables

    def list_fields(self, base_token, table_id):
        self.calls.append(f"list_fields:{table_id}")
        return self.fields_by_table[table_id]


def test_schema_probe_calls_only_list_tables_then_each_table_fields():
    client = FakeSchemaClient()

    result = probe_schema(client, base_token="base-token")

    assert result.table_names == ("任务", "审核")
    assert client.calls == [
        "list_tables",
        "list_fields:tbl_task",
        "list_fields:tbl_review",
    ]


def test_schema_probe_hashes_only_schema_and_audit_payload_is_safe():
    result = probe_schema(FakeSchemaClient(), base_token="base-token")
    audit = result.to_audit_dict()
    encoded = json.dumps(audit, ensure_ascii=False, sort_keys=True)

    assert re.fullmatch(r"[0-9a-f]{64}", result.schema_sha256)
    assert audit["tables"] == [
        {
            "name": "任务",
            "fields": [
                {
                    "name": "题目名称",
                    "type": "1",
                    "options": [{"color": 0, "id": "opt_draft", "name": "草稿"}],
                },
            ],
        },
        {"name": "审核", "fields": [{"name": "P0", "type": "3", "options": []}]},
    ]
    for forbidden in ("base-token", "raw_value", "rec_hidden", "record_id"):
        assert forbidden not in encoded
    with pytest.raises((AttributeError, TypeError)):
        result.schema_sha256 = "other"


@pytest.mark.parametrize(
    ("tables", "fields_by_table", "base_token", "message"),
    [
        (None, None, "", "base token"),
        ([], {}, "base-token", "schema must contain at least one table"),
        (
            [
                {"table_id": "tbl_task", "name": "任务"},
                {"table_id": "tbl_task", "name": "重复任务"},
            ],
            {"tbl_task": []},
            "base-token",
            "duplicate table identity",
        ),
        (
            [{"table_id": "tbl_task", "name": "任务"}],
            {
                "tbl_task": [
                    {"field_id": "fld_title", "field_name": "题目", "type": 1},
                    {"field_id": "fld_title", "field_name": "重复题目", "type": 1},
                ],
            },
            "base-token",
            "duplicate field identity",
        ),
        (
            [{"table_id": "tbl_task", "name": "任务"}],
            {
                "tbl_task": [
                    {"field_id": "fld_title", "field_name": "题目", "type": False},
                ],
            },
            "base-token",
            "field type",
        ),
    ],
)
def test_schema_probe_rejects_empty_duplicate_or_invalid_metadata(
    tables, fields_by_table, base_token, message
):
    client = FakeSchemaClient(tables=tables, fields_by_table=fields_by_table)

    with pytest.raises(ValueError, match=message):
        probe_schema(client, base_token=base_token)


def test_schema_probe_rejects_table_without_fields():
    client = FakeSchemaClient(
        tables=[{"table_id": "tbl_task", "name": "任务"}],
        fields_by_table={"tbl_task": []},
    )

    with pytest.raises(ValueError, match="at least one field"):
        probe_schema(client, base_token="base-token")


def test_schema_probe_cli_help_requires_explicit_base_and_has_no_write_commands():
    script = Path(__file__).resolve().parents[1] / "scripts" / "probe_phase3_feishu_schema.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--help"],
        capture_output=True,
        check=False,
        cwd=script.parents[1],
        text=True,
    )

    assert completed.returncode == 0
    assert "--base-token" in completed.stdout
    for forbidden in (
        "--write",
        "--create",
        "--update",
        "--delete",
        "--record",
        "--form",
        "--automation",
        "--sheet",
    ):
        assert forbidden not in completed.stdout.lower()


SCHEMA_CLI_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "probe_phase3_feishu_schema.py"
)


def load_schema_cli_module():
    module_name = "phase3_schema_probe_cli_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCHEMA_CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def schema_page(items, *, has_more=False, page_token=None):
    data = {"items": items, "has_more": has_more}
    if page_token is not None:
        data["page_token"] = page_token
    return {"code": 0, "data": data}


def test_schema_cli_uses_only_fixed_tables_and_fields_get_paths(monkeypatch):
    schema_cli = load_schema_cli_module()
    responses = iter(
        [
            schema_page([{"table_id": "tbl_task", "name": "任务"}]),
            schema_page([{"field_id": "fld_title", "field_name": "题目", "type": 1}]),
        ]
    )
    calls = []

    def fake_http(method, url, **kwargs):
        calls.append((method, url, kwargs))
        return next(responses)

    monkeypatch.setattr(schema_cli, "_http", fake_http)
    client = schema_cli.ReadOnlySchemaClient("tenant-token")

    assert client.list_tables("base-safe") == [{"table_id": "tbl_task", "name": "任务"}]
    assert client.list_fields("base-safe", "tbl_task") == [
        {"field_id": "fld_title", "field_name": "题目", "type": 1}
    ]
    assert [method for method, _, _ in calls] == ["GET", "GET"]
    assert [urlparse(url).path for _, url, _ in calls] == [
        "/open-apis/bitable/v1/apps/base-safe/tables",
        "/open-apis/bitable/v1/apps/base-safe/tables/tbl_task/fields",
    ]
    assert all("records" not in url and "forms" not in url for _, url, _ in calls)
    for _, member in inspect.getmembers(schema_cli.ReadOnlySchemaClient, inspect.isfunction):
        parameter_names = inspect.signature(member).parameters
        assert not {"endpoint", "path", "url"} & set(parameter_names)


@pytest.mark.parametrize("code", [False, 1])
def test_schema_cli_rejects_non_integer_or_nonzero_success_code(code):
    schema_cli = load_schema_cli_module()

    with pytest.raises(schema_cli.FeishuEnvelopeError):
        schema_cli.ReadOnlySchemaClient._require_success_data({"code": code, "data": {}})


@pytest.mark.parametrize(
    "data",
    [
        {"items": []},
        {"items": [], "has_more": None},
        {"items": [], "has_more": "false"},
    ],
)
def test_schema_cli_rejects_non_boolean_page_completion_without_partial_result(
    monkeypatch, data
):
    schema_cli = load_schema_cli_module()
    calls = []

    def fake_http(method, url, **kwargs):
        calls.append((method, url))
        return {"code": 0, "data": data}

    monkeypatch.setattr(schema_cli, "_http", fake_http)

    with pytest.raises(schema_cli.FeishuEnvelopeError):
        schema_cli.ReadOnlySchemaClient("tenant-token").list_tables("base-safe")
    assert len(calls) == 1


@pytest.mark.parametrize("page_token", [None, "", "   "])
def test_schema_cli_rejects_incomplete_true_page_token(monkeypatch, page_token):
    schema_cli = load_schema_cli_module()
    calls = []

    def fake_http(*args, **kwargs):
        calls.append((args, kwargs))
        return schema_page([], has_more=True, page_token=page_token)

    monkeypatch.setattr(schema_cli, "_http", fake_http)

    with pytest.raises(schema_cli.FeishuEnvelopeError, match="no next page token"):
        schema_cli.ReadOnlySchemaClient("tenant-token").list_tables("base-safe")
    assert len(calls) == 1


def test_schema_cli_rejects_repeated_true_page_token(monkeypatch):
    schema_cli = load_schema_cli_module()
    responses = iter(
        [
            schema_page([], has_more=True, page_token="page-1"),
            schema_page([], has_more=True, page_token="page-1"),
        ]
    )

    monkeypatch.setattr(schema_cli, "_http", lambda *args, **kwargs: next(responses))

    with pytest.raises(schema_cli.FeishuEnvelopeError):
        schema_cli.ReadOnlySchemaClient("tenant-token").list_tables("base-safe")


def test_schema_probe_hash_is_stable_when_tables_fields_and_options_are_reordered():
    fields = {
        "tbl_task": [
            {
                "field_id": "fld_title",
                "field_name": "题目",
                "type": 1,
                "property": {
                    "options": [
                        {"id": "opt_b", "name": "B", "color": 1},
                        {"id": "opt_a", "name": "A", "color": 0},
                    ]
                },
            },
            {"field_id": "fld_level", "field_name": "难度", "type": 3},
        ],
        "tbl_review": [{"field_id": "fld_p0", "field_name": "P0", "type": 1}],
    }
    tables = [
        {"table_id": "tbl_task", "name": "任务"},
        {"table_id": "tbl_review", "name": "审核"},
    ]
    first = probe_schema(FakeSchemaClient(tables=tables, fields_by_table=fields), base_token="base")
    second = probe_schema(
        FakeSchemaClient(
            tables=list(reversed(tables)),
            fields_by_table={
                table_id: list(reversed(table_fields))
                for table_id, table_fields in fields.items()
            },
        ),
        base_token="base",
    )

    assert second.schema_sha256 == first.schema_sha256
    assert second.to_audit_dict() == first.to_audit_dict()


def test_schema_probe_hash_is_stable_for_mixed_color_types_without_option_ids():
    tables = [{"table_id": "tbl_task", "name": "任务"}]
    first_options = [
        {"name": "同名选项", "color": 1},
        {"name": "同名选项", "color": "1"},
    ]
    first = probe_schema(
        FakeSchemaClient(
            tables=tables,
            fields_by_table={
                "tbl_task": [
                    {
                        "field_id": "fld_status",
                        "field_name": "状态",
                        "type": 3,
                        "property": {"options": first_options},
                    }
                ]
            },
        ),
        base_token="base",
    )
    second = probe_schema(
        FakeSchemaClient(
            tables=tables,
            fields_by_table={
                "tbl_task": [
                    {
                        "field_id": "fld_status",
                        "field_name": "状态",
                        "type": 3,
                        "property": {"options": list(reversed(first_options))},
                    }
                ]
            },
        ),
        base_token="base",
    )

    assert first.schema_sha256 == second.schema_sha256
    assert first.to_audit_dict() == second.to_audit_dict()
    colors = [option["color"] for option in first.to_audit_dict()["tables"][0]["fields"][0]["options"]]
    assert {type(color) for color in colors} == {int, str}


def test_public_base_token_validation_is_shared_by_probe_and_cli():
    validate = phase3_feishu.validate_explicit_base_token

    assert validate("base-safe") == "base-safe"
    with pytest.raises(ValueError, match="base token"):
        validate("  ")


def test_schema_cli_help_does_not_read_tenant_credentials(monkeypatch):
    schema_cli = load_schema_cli_module()
    calls = []

    monkeypatch.setattr(schema_cli, "tenant_token", lambda: calls.append("tenant"))

    with pytest.raises(SystemExit) as exit_info:
        schema_cli.main(["--help"])
    assert exit_info.value.code == 0
    assert calls == []


def test_schema_cli_rejects_blank_base_before_tenant_credentials(monkeypatch, capsys):
    schema_cli = load_schema_cli_module()
    calls = []

    def forbidden_tenant_token():
        calls.append("tenant")
        raise AssertionError("tenant token must not be read")

    monkeypatch.setattr(schema_cli, "tenant_token", forbidden_tenant_token)

    assert schema_cli.main(["--base-token", "  "]) == 1
    captured = capsys.readouterr()
    assert calls == []
    assert "base-token" not in captured.err
    assert "  " not in captured.err


def test_schema_cli_error_hides_base_token_and_url(monkeypatch, capsys):
    schema_cli = load_schema_cli_module()
    hidden_base_token = "base-token-that-must-not-appear"

    def failing_tenant_token():
        raise RuntimeError(f"https://example.invalid/{hidden_base_token}/tables")

    monkeypatch.setattr(schema_cli, "tenant_token", failing_tenant_token)

    assert schema_cli.main(["--base-token", hidden_base_token]) == 1
    captured = capsys.readouterr()
    assert hidden_base_token not in captured.err
    assert "https://" not in captured.err
