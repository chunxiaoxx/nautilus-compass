from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.fde_phase3_feishu import ExportReadback
from services.fde_phase3_feishu_runtime_contract import (
    AppRole,
    BitableEventEnvelope,
    CanonicalTable,
    CompassReceipt,
    RepairReferenceReadback,
    RepairReferenceState,
    RuntimeRoute,
    V3ManifestReadback,
    authorize_canonical_mutation,
    authorize_compass_receipt_write,
    authorize_revision_link,
    build_mentor_projection,
    build_v5_eligible_projection,
)
from services.fde_phase3_mentor_projection import CuratedLesson, MentorTaskGuidance
from services.fde_phase3_single_submission_qc import P0Disposition
from services.fde_phase3_single_submission_schema import PHASE3_WORKFLOW_PROFILE


EVIDENCE_HASH = "sha256:" + "a" * 64
INTERACTION_HASH = "sha256:" + "b" * 64
PAYLOAD_HASH = "sha256:" + "c" * 64
MANIFEST_HASH = "sha256:" + "d" * 64
RECEIPT_HASH = "sha256:" + "e" * 64
NOW = datetime(2026, 7, 23, 12, tzinfo=timezone.utc)


def event(route: RuntimeRoute, **overrides: object) -> BitableEventEnvelope:
    values: dict[str, object] = {
        "route": route,
        "record_id": "rec_submission_001",
        "record_version": 3,
        "source_event_id": "evt_feishu_001",
    }
    values.update(overrides)
    return BitableEventEnvelope(**values)


def eligible_export_readback(**overrides: object) -> ExportReadback:
    values: dict[str, object] = {
        "task_record_id": "rec_task_001",
        "attempt_record_id": "rec_submission_001",
        "review_record_id": "rec_review_001",
        "export_record_id": "rec_export_001",
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


def mentor_guidance() -> MentorTaskGuidance:
    return MentorTaskGuidance(
        task_handle="mentor_task_001",
        p0_disposition=P0Disposition.REPAIR_REQUIRED,
        next_action="repair_and_resubmit",
        reason_codes=("trajectory_not_coherent",),
        repair_guidance="让每轮追问围绕上一轮的缺口、决策或产物推进后重新提交。",
        knowledge_pack_version="mentor-p3-v1",
        lessons=(
            CuratedLesson(
                lesson_id="trajectory-coherence",
                category="interaction_evidence",
                guidance="每轮追问都应解决上一轮留下的具体问题。",
            ),
        ),
    )


def repair_reference_readback(**overrides: object) -> RepairReferenceReadback:
    values: dict[str, object] = {
        "repair_reference": "repair_trajectory_001",
        "expert_scope_handle": "mentor_expert_001",
        "bound_expert_record_id": "rec_expert_001",
        "predecessor_submission_record_id": "rec_submission_001",
        "predecessor_business_status": "需返修",
        "expires_at": NOW + timedelta(days=1),
        "state": RepairReferenceState.ACTIVE,
    }
    values.update(overrides)
    return RepairReferenceReadback(**values)


def manifest_readback(**overrides: object) -> V3ManifestReadback:
    values: dict[str, object] = {
        "export_record_id": "rec_export_001",
        "opaque_task_id": "task_v3_eligible_001",
        "event_id": "evt_v5_001",
        "payload_hash": PAYLOAD_HASH,
        "manifest_hash": MANIFEST_HASH,
        "signer_key_id": "key_v5_202607",
        "signature": "sig_v5_001",
    }
    values.update(overrides)
    return V3ManifestReadback(**values)


def compass_receipt(**overrides: object) -> CompassReceipt:
    values: dict[str, object] = {
        "opaque_task_id": "task_v3_eligible_001",
        "event_id": "evt_v5_001",
        "payload_hash": PAYLOAD_HASH,
        "manifest_hash": MANIFEST_HASH,
        "receipt_hash": RECEIPT_HASH,
        "signer_key_id": "key_compass_202607",
        "signature": "sig_compass_001",
    }
    values.update(overrides)
    return CompassReceipt(**values)


class ReceiptVerifier:
    def __init__(self, *, manifest_ok: bool = True, receipt_ok: bool = True) -> None:
        self.manifest_ok = manifest_ok
        self.receipt_ok = receipt_ok

    def verify_v5_manifest(self, artifact: V3ManifestReadback) -> bool:
        return self.manifest_ok

    def verify_compass_receipt(
        self,
        artifact: V3ManifestReadback,
        receipt: CompassReceipt,
    ) -> bool:
        return self.receipt_ok


def test_only_nautilus_can_authorize_canonical_bitable_mutations() -> None:
    envelope = event(RuntimeRoute.QC_COMPLETED)

    with pytest.raises(PermissionError, match="Nautilus"):
        authorize_canonical_mutation(
            actor=AppRole.MENTOR,
            envelope=envelope,
            target_table=CanonicalTable.TASK_SUBMISSION,
            target_record_id="rec_submission_001",
            updates={"自动P0状态": "建议进入甲方队列"},
        )

    mutation = authorize_canonical_mutation(
        actor=AppRole.NAUTILUS,
        envelope=envelope,
        target_table=CanonicalTable.TASK_SUBMISSION,
        target_record_id="rec_submission_001",
        updates={"自动P0状态": "建议进入甲方队列"},
    )

    assert mutation.idempotency_key == envelope.idempotency_key
    assert mutation.target_table is CanonicalTable.TASK_SUBMISSION


def test_submission_created_initializes_only_the_internal_profile_and_expert_link() -> None:
    envelope = event(RuntimeRoute.SUBMISSION_CREATED)

    mutation = authorize_canonical_mutation(
        actor=AppRole.NAUTILUS,
        envelope=envelope,
        target_table=CanonicalTable.TASK_SUBMISSION,
        target_record_id="rec_submission_001",
        updates={
            "工作流配置": PHASE3_WORKFLOW_PROFILE,
            "专家关联": ["rec_expert_001"],
            "业务状态": "自动质检中",
            "自动P0状态": "待运行",
        },
    )

    assert mutation.updates["工作流配置"] == PHASE3_WORKFLOW_PROFILE
    with pytest.raises(ValueError, match="workflow profile"):
        authorize_canonical_mutation(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            target_table=CanonicalTable.TASK_SUBMISSION,
            target_record_id="rec_submission_001",
            updates={"工作流配置": "generic_evidence_pack"},
        )
    with pytest.raises(PermissionError, match="route is not approved"):
        authorize_canonical_mutation(
            actor=AppRole.NAUTILUS,
            envelope=event(RuntimeRoute.QC_COMPLETED),
            target_table=CanonicalTable.TASK_SUBMISSION,
            target_record_id="rec_submission_001",
            updates={"工作流配置": PHASE3_WORKFLOW_PROFILE},
        )


def test_nautilus_can_anchor_review_and_export_rows_to_the_submission() -> None:
    review = authorize_canonical_mutation(
        actor=AppRole.NAUTILUS,
        envelope=event(RuntimeRoute.QC_COMPLETED),
        target_table=CanonicalTable.REVIEW_FEEDBACK,
        target_record_id="rec_review_001",
        updates={
            "提交关联": ["rec_submission_001"],
            "P0状态": "建议进入甲方队列",
        },
    )
    export = authorize_canonical_mutation(
        actor=AppRole.NAUTILUS,
        envelope=event(RuntimeRoute.BUYER_FEEDBACK_RECORDED),
        target_table=CanonicalTable.EXPORT_RECEIPT,
        target_record_id="rec_export_001",
        updates={
            "提交关联": ["rec_submission_001"],
            "审核关联": ["rec_review_001"],
            "导出状态": "待导出",
        },
    )

    assert review.target_table is CanonicalTable.REVIEW_FEEDBACK
    assert export.target_table is CanonicalTable.EXPORT_RECEIPT


def test_event_idempotency_is_anchored_to_route_record_identity_and_version() -> None:
    original = event(RuntimeRoute.QC_COMPLETED)
    repeated_delivery = event(RuntimeRoute.QC_COMPLETED, source_event_id="evt_retry_001")
    new_version = event(RuntimeRoute.QC_COMPLETED, record_version=4)
    different_route = event(RuntimeRoute.REPAIR_REQUIRED)

    assert original.idempotency_key == repeated_delivery.idempotency_key
    assert original.idempotency_key != new_version.idempotency_key
    assert original.idempotency_key != different_route.idempotency_key


def test_runtime_rejects_developer_chat_as_a_business_route() -> None:
    with pytest.raises(ValueError, match="RuntimeRoute"):
        BitableEventEnvelope(
            route="developer_chat",  # type: ignore[arg-type]
            record_id="rec_submission_001",
            record_version=3,
            source_event_id="evt_chat_001",
        )


def test_mentor_receives_only_expert_scoped_redacted_projection() -> None:
    projection = build_mentor_projection(
        guidance=mentor_guidance(),
        expert_scope_handle="mentor_expert_001",
        task_handle="mentor_task_001",
        repair_reference="repair_trajectory_001",
        human_interaction_ref_hash=INTERACTION_HASH,
    )

    assert projection.to_payload() == {
        "expert_scope_handle": "mentor_expert_001",
        "task_handle": "mentor_task_001",
        "p0_disposition": "repair_required",
        "next_action": "repair_and_resubmit",
        "reason_codes": ["trajectory_not_coherent"],
        "repair_guidance": "让每轮追问围绕上一轮的缺口、决策或产物推进后重新提交。",
        "knowledge_pack_version": "mentor-p3-v1",
        "repair_reference": "repair_trajectory_001",
        "lessons": [
            {
                "lesson_id": "trajectory-coherence",
                "category": "interaction_evidence",
                "guidance": "每轮追问都应解决上一轮留下的具体问题。",
            }
        ],
        "human_interaction_ref_hash": INTERACTION_HASH,
    }
    assert not hasattr(projection, "submission_record_id")
    assert not hasattr(projection, "attachments")
    assert not hasattr(projection, "raw_buyer_feedback")


def test_mentor_projection_requires_the_guidances_opaque_task_handle() -> None:
    with pytest.raises(PermissionError, match="task handle"):
        build_mentor_projection(
            guidance=mentor_guidance(),
            expert_scope_handle="mentor_expert_001",
            task_handle="mentor_task_other_001",
            repair_reference="repair_trajectory_001",
        )

    with pytest.raises(ValueError, match="sha256"):
        build_mentor_projection(
            guidance=mentor_guidance(),
            expert_scope_handle="mentor_expert_001",
            task_handle="mentor_task_001",
            repair_reference="repair_trajectory_001",
            human_interaction_ref_hash="https://private.example/trajectory",
        )


def test_repair_projection_requires_an_opaque_reference_and_nautilus_controls_lineage() -> None:
    with pytest.raises(ValueError, match="repair_reference"):
        build_mentor_projection(
            guidance=mentor_guidance(),
            expert_scope_handle="mentor_expert_001",
            task_handle="mentor_task_001",
        )

    envelope = event(
        RuntimeRoute.SUBMISSION_CREATED,
        record_id="rec_submission_002",
    )
    with pytest.raises(PermissionError, match="Nautilus"):
        authorize_revision_link(
            actor=AppRole.MENTOR,
            envelope=envelope,
            expert_scope_handle="mentor_expert_001",
            authenticated_expert_record_id="rec_expert_001",
            repair_reference="repair_trajectory_001",
            predecessor=repair_reference_readback(),
            now=NOW,
        )

    link = authorize_revision_link(
        actor=AppRole.NAUTILUS,
        envelope=envelope,
        expert_scope_handle="mentor_expert_001",
        authenticated_expert_record_id="rec_expert_001",
        repair_reference="repair_trajectory_001",
        predecessor=repair_reference_readback(),
        now=NOW,
    )

    assert link.successor_submission_record_id == "rec_submission_002"
    assert link.revision_of_record_id == "rec_submission_001"


def test_repair_reference_requires_bound_expert_unexpired_single_use_claim() -> None:
    envelope = event(
        RuntimeRoute.SUBMISSION_CREATED,
        record_id="rec_submission_002",
    )
    with pytest.raises(PermissionError, match="bound expert"):
        authorize_revision_link(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            expert_scope_handle="mentor_expert_001",
            authenticated_expert_record_id="rec_expert_other",
            repair_reference="repair_trajectory_001",
            predecessor=repair_reference_readback(),
            now=NOW,
        )
    with pytest.raises(PermissionError, match="expired"):
        authorize_revision_link(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            expert_scope_handle="mentor_expert_001",
            authenticated_expert_record_id="rec_expert_001",
            repair_reference="repair_trajectory_001",
            predecessor=repair_reference_readback(expires_at=NOW - timedelta(seconds=1)),
            now=NOW,
        )
    with pytest.raises(PermissionError, match="expired"):
        authorize_revision_link(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            expert_scope_handle="mentor_expert_001",
            authenticated_expert_record_id="rec_expert_001",
            repair_reference="repair_trajectory_001",
            predecessor=repair_reference_readback(expires_at=NOW),
            now=NOW,
        )
    with pytest.raises(PermissionError, match="already claimed"):
        authorize_revision_link(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            expert_scope_handle="mentor_expert_001",
            authenticated_expert_record_id="rec_expert_001",
            repair_reference="repair_trajectory_001",
            predecessor=repair_reference_readback(
                state=RepairReferenceState.USED,
                claimed_by_submission_record_id="rec_submission_other",
            ),
            now=NOW,
        )
    idempotent = authorize_revision_link(
        actor=AppRole.NAUTILUS,
        envelope=envelope,
        expert_scope_handle="mentor_expert_001",
        authenticated_expert_record_id="rec_expert_001",
        repair_reference="repair_trajectory_001",
        predecessor=repair_reference_readback(
            state=RepairReferenceState.USED,
            claimed_by_submission_record_id="rec_submission_002",
        ),
        now=NOW,
    )

    assert idempotent.idempotency_key == envelope.idempotency_key


def test_v5_receives_only_eligible_deidentified_projection() -> None:
    projection = build_v5_eligible_projection(
        source_event=event(RuntimeRoute.BUYER_FEEDBACK_RECORDED),
        export_readback=eligible_export_readback(),
        opaque_task_id="task_v3_eligible_001",
        p0_state="passed",
        feedback_class_code="accepted",
        verdict="Gold",
        evidence_hash=EVIDENCE_HASH,
        human_interaction_ref_hash=INTERACTION_HASH,
    )

    assert projection.to_payload() == {
        "task_id": "task_v3_eligible_001",
        "p0_state": "passed",
        "feedback_class": "accepted",
        "verdict": "Gold",
        "evidence_hash": EVIDENCE_HASH,
        "human_interaction_ref_hash": INTERACTION_HASH,
    }
    assert not hasattr(projection, "record_id")
    assert not hasattr(projection, "share_url")
    assert not hasattr(projection, "attachment")
    assert not hasattr(projection, "raw_buyer_feedback")

    with pytest.raises(ValueError, match="sha256"):
        build_v5_eligible_projection(
            source_event=event(RuntimeRoute.BUYER_FEEDBACK_RECORDED),
            export_readback=eligible_export_readback(),
            opaque_task_id="task_v3_eligible_001",
            p0_state="passed",
            feedback_class_code="accepted",
            verdict="Gold",
            evidence_hash=EVIDENCE_HASH,
            human_interaction_ref_hash="https://private.example/trajectory",
        )


def test_v5_projection_cannot_be_built_before_buyer_feedback_is_recorded() -> None:
    with pytest.raises(ValueError, match="buyer_feedback_recorded"):
        build_v5_eligible_projection(
            source_event=event(RuntimeRoute.QC_COMPLETED),
            export_readback=eligible_export_readback(),
            opaque_task_id="task_v3_eligible_001",
            p0_state="passed",
            feedback_class_code="accepted",
            verdict="Gold",
            evidence_hash=EVIDENCE_HASH,
        )


def test_v5_projection_must_match_the_buyer_verdict_read_back_from_bitable() -> None:
    with pytest.raises(ValueError, match="buyer verdict"):
        build_v5_eligible_projection(
            source_event=event(RuntimeRoute.BUYER_FEEDBACK_RECORDED),
            export_readback=eligible_export_readback(),
            opaque_task_id="task_v3_eligible_001",
            p0_state="passed",
            feedback_class_code="accepted",
            verdict="Repair",
            evidence_hash=EVIDENCE_HASH,
        )


def test_compass_receipt_requires_verified_exact_v3_binding_before_writeback() -> None:
    envelope = event(
        RuntimeRoute.COMPASS_RECEIPT_RECORDED,
        record_id="rec_export_001",
        source_event_id="evt_compass_receipt_001",
    )
    mutation = authorize_compass_receipt_write(
        actor=AppRole.NAUTILUS,
        envelope=envelope,
        artifact=manifest_readback(),
        receipt=compass_receipt(),
        verifier=ReceiptVerifier(),
    )

    assert mutation.target_table is CanonicalTable.EXPORT_RECEIPT
    assert mutation.updates == {
        "导出状态": "已回执",
        "compass_receipt_hash": RECEIPT_HASH,
        "Compass签名键ID": "key_compass_202607",
        "回执幂等键": envelope.idempotency_key,
    }
    with pytest.raises(ValueError, match="payload_hash"):
        authorize_compass_receipt_write(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            artifact=manifest_readback(),
            receipt=compass_receipt(payload_hash=EVIDENCE_HASH),
            verifier=ReceiptVerifier(),
        )
    with pytest.raises(PermissionError, match="signature verification"):
        authorize_compass_receipt_write(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            artifact=manifest_readback(),
            receipt=compass_receipt(),
            verifier=ReceiptVerifier(receipt_ok=False),
        )
