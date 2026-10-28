from __future__ import annotations

import os
from pathlib import Path

import pytest


def _required_directory(name: str) -> Path:
    value = os.environ.get(name)
    if value is None:
        # 2026-09-15: env 缺失=本机无垂直链环境,skip 不 fail(工厂机有 env 照跑);
        # 13 假红污染"测试绿=可部署"信心
        pytest.skip(f"{name} is required for the local R1a vertical chain (factory env)")
    path = Path(value).resolve()
    assert path.is_dir(), f"{name} must name an existing directory"
    return path


def test_r1a_positive_chain_persists_one_independently_verified_result() -> None:
    try:
        from tests.platform_protocol.m1_r1a_synthetic_repair_harness import (
            run_positive_chain,
        )
    except ModuleNotFoundError as error:
        if error.name == "tests.platform_protocol.m1_r1a_synthetic_repair_harness":
            pytest.fail("m1_r1a_synthetic_repair_harness_missing", pytrace=False)
        raise

    database_url = os.environ.get("NAUTILUS_PLATFORM_DATABASE_URL")
    if database_url is None:
        pytest.skip(
            "NAUTILUS_PLATFORM_DATABASE_URL is required for the local R1a chain (factory env)"
        )

    result = run_positive_chain(
        database_url=database_url,
        platform_root=Path(__file__).resolve().parents[4],
        v5_authority_root=_required_directory("NAUTILUS_V5_AUTHORITY_ROOT"),
        v5_executor_root=_required_directory("NAUTILUS_V5_EXECUTOR_ROOT"),
        compass_authority_root=_required_directory("NAUTILUS_COMPASS_AUTHORITY_ROOT"),
    )

    assert result.source_admission_status == "admitted_for_local_r1a_synthetic_repair"
    assert result.protocol_row_counts == {
        "operations": 1,
        "attempts": 1,
        "executor_evidence": 1,
        "manifests": 1,
        "receipts": 1,
        "audit_events": 4,
        "outbox_events": 3,
    }
    assert result.attempt_claim_count == 1
    assert result.audit_event_types == (
        "accepted",
        "dispatched",
        "manifest_received",
        "receipt_verified",
    )
    assert result.outbox_event_types == (
        "dispatched",
        "manifest_received",
        "receipt_verified",
    )
    assert result.outbox_state_counts == {"delivered": 1, "pending": 2}
    assert result.receipt_decision == "accepted"
    assert result.receipt_reason_codes == ("policy_satisfied",)
    assert result.operation_state == "receipt_verified"
    assert result.executor_principal != result.verifier_principal
    assert result.executor_release != result.verifier_release
    assert result.executor_public_key != result.verifier_public_key
    assert result.network_delivery_count == 0
    assert result.separate_database_readback is True
    assert result.temporary_fixture_removed is True
    assert result.executor_result_state == "completed"
    assert result.repair_completed is True
