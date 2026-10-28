"""Persistence-boundary tests for the atomic R1a evidence command."""

from __future__ import annotations

import hashlib
import inspect
from datetime import datetime, timezone

import platform_protocol
from platform_protocol.m1_r1a_execution_evidence import (
    EVIDENCE_CONTRACT_VERSION,
    ExecutorExecutionEvidenceV1,
)
from platform_protocol.models import ProtocolExecutorEvidence
from platform_protocol.repository import executor_execution_evidence
from platform_protocol.service import ProtocolService


def _evidence() -> ExecutorExecutionEvidenceV1:
    return ExecutorExecutionEvidenceV1(
        evidence_version=EVIDENCE_CONTRACT_VERSION,
        operation_id="op_r1a_synthetic_01",
        attempt_id="att_r1a_synthetic_01",
        input_ref_hash="1" * 64,
        executor_id="exec_r1a_synthetic_01",
        executor_release="rel_r1a_synthetic_01",
        executor_key_id="key_r1a_synthetic_01",
        bound_capsule_hash="2" * 64,
        fixture_hash="3" * 64,
        tool_policy_hash="4" * 64,
        artifact_hash="5" * 64,
        result_state="completed",
        produced_at=datetime(2026, 8, 9, 12, 30, tzinfo=timezone.utc),
        signature_algorithm="ed25519-v1",
        executor_signature="sig_" + "A" * 86,
    )


def test_executor_evidence_persistence_has_an_exact_protocol_only_allowlist() -> None:
    assert tuple(ProtocolExecutorEvidence.__table__.columns.keys()) == (
        "evidence_hash",
        "evidence_version",
        "operation_id",
        "attempt_id",
        "input_ref_hash",
        "executor_id",
        "executor_release",
        "executor_key_id",
        "bound_capsule_hash",
        "fixture_hash",
        "tool_policy_hash",
        "artifact_hash",
        "result_state",
        "produced_at",
        "signature_algorithm",
        "executor_signature",
    )


def test_persisted_executor_evidence_round_trips_the_canonical_contract() -> None:
    evidence = _evidence()
    row = ProtocolExecutorEvidence(
        evidence_hash=hashlib.sha256(evidence.canonical_bytes).hexdigest(),
        evidence_version=evidence.evidence_version,
        operation_id=evidence.operation_id,
        attempt_id=evidence.attempt_id,
        input_ref_hash=evidence.input_ref_hash,
        executor_id=evidence.executor_id,
        executor_release=evidence.executor_release,
        executor_key_id=evidence.executor_key_id,
        bound_capsule_hash=evidence.bound_capsule_hash,
        fixture_hash=evidence.fixture_hash,
        tool_policy_hash=evidence.tool_policy_hash,
        artifact_hash=evidence.artifact_hash,
        result_state=evidence.result_state,
        produced_at=evidence.produced_at,
        signature_algorithm=evidence.signature_algorithm,
        executor_signature=evidence.executor_signature,
    )

    assert executor_execution_evidence(row) == evidence


def test_service_exposes_one_atomic_evidence_and_manifest_command() -> None:
    parameters = inspect.signature(
        ProtocolService.record_execution_evidence_and_manifest
    ).parameters

    assert tuple(parameters) == ("self", "evidence", "manifest", "now")


def test_package_exports_the_frozen_r1a_protocol_types() -> None:
    assert platform_protocol.ExecutorExecutionEvidenceV1 is ExecutorExecutionEvidenceV1
    assert platform_protocol.R1aExecutorSelectionV1.__name__ == "R1aExecutorSelectionV1"
