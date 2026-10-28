from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from g2_a0_model_gate_cli import ModelGateEvidenceV1, ModelGateRunnerViolation
from test_g2_a0_model_gate_cli import (
    API_KEY,
    CANONICAL_REQUEST,
    BalanceReader,
    Completion,
    Verifier,
    candidate,
    make_runner,
    request_binding,
)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("provider_call_count", True),
        ("balance_read_count", False),
        ("replay_count", True),
        ("replay_provider_call_growth", False),
        ("balance_delta_micros_cny", True),
        ("public_case_count", False),
        ("hidden_case_count", True),
        ("network_call_count", False),
    ),
)
def test_evidence_rejects_bool_as_integer(
    field_name: str,
    bad_value: object,
    tmp_path: Path,
) -> None:
    runner, _, _, _ = make_runner(tmp_path)
    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    document = json.loads(result.evidence_bytes)
    document[field_name] = bad_value

    with pytest.raises(ModelGateRunnerViolation):
        runner.validate_evidence_bytes(
            request=request_binding(),
            data=json.dumps(
                document,
                separators=(",", ":"),
                sort_keys=True,
            ).encode(),
        )


def test_evidence_rejects_extra_and_duplicate_fields(tmp_path: Path) -> None:
    runner, _, _, _ = make_runner(tmp_path)
    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    document = json.loads(result.evidence_bytes)
    document["runtime_authorized"] = True
    extra = json.dumps(document, separators=(",", ":"), sort_keys=True).encode()
    duplicate = result.evidence_bytes.replace(
        b'{"balance_delta_micros_cny":17,',
        b'{"balance_delta_micros_cny":17,"balance_delta_micros_cny":17,',
    )

    for payload in (extra, duplicate):
        with pytest.raises(ModelGateRunnerViolation):
            runner.validate_evidence_bytes(
                request=request_binding(),
                data=payload,
            )


def test_evidence_claims_are_recomputed_not_trusted_from_document(
    tmp_path: Path,
) -> None:
    runner, _, _, _ = make_runner(tmp_path)
    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    baseline = json.loads(result.evidence_bytes)

    mutations = {
        "fixture_hash": "f" * 64,
        "response_schema_hash": "e" * 64,
        "provider_call_count": 0,
        "hidden_case_count": baseline["hidden_case_count"] + 1,
        "patched_sha256": "9" * 64,
        "implementation_commit": "0" * 40,
    }
    for field_name, bad_value in mutations.items():
        changed = deepcopy(baseline)
        changed[field_name] = bad_value
        with pytest.raises(ModelGateRunnerViolation, match="evidence_mismatch"):
            runner.validate_evidence_bytes(
                request=request_binding(),
                data=json.dumps(
                    changed,
                    separators=(",", ":"),
                    sort_keys=True,
                ).encode(),
            )


@pytest.mark.parametrize(
    "field_name",
    ("request_hash", "policy_hash", "fixture_hash", "response_schema_hash"),
)
def test_required_binding_hashes_cannot_be_null(
    field_name: str,
    tmp_path: Path,
) -> None:
    runner, _, _, _ = make_runner(tmp_path)
    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    document = json.loads(result.evidence_bytes)
    document[field_name] = None

    with pytest.raises(ModelGateRunnerViolation, match=f"invalid_{field_name}"):
        ModelGateEvidenceV1.from_json_bytes(
            json.dumps(document, separators=(",", ":"), sort_keys=True).encode()
        )


def test_decision_and_state_trace_must_describe_the_same_terminal(
    tmp_path: Path,
) -> None:
    runner, _, _, _ = make_runner(tmp_path)
    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    document = json.loads(result.evidence_bytes)
    document["state_trace"] = [
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "INCONCLUSIVE",
        "REPLAYED",
        "COMPLETE",
    ]

    with pytest.raises(ModelGateRunnerViolation, match="invalid_state_trace"):
        ModelGateEvidenceV1.from_json_bytes(
            json.dumps(document, separators=(",", ":"), sort_keys=True).encode()
        )


def test_balance_values_require_nonnegative_exact_ints(tmp_path: Path) -> None:
    for values in ((True, 0), (-1, 0)):
        runner, _, _, _ = make_runner(tmp_path, balances=BalanceReader(values))
        with pytest.raises(ModelGateRunnerViolation, match="balance_ambiguous"):
            runner.run(
                request=request_binding(),
                canonical_request=CANONICAL_REQUEST,
                api_key=API_KEY,
            )

    for values in ((1, False), (1, -1)):
        runner, _, _, _ = make_runner(tmp_path, balances=BalanceReader(values))
        result = runner.run(
            request=request_binding(),
            canonical_request=CANONICAL_REQUEST,
            api_key=API_KEY,
        )
        assert result.decision.status == "inconclusive"
        assert json.loads(result.evidence_bytes)["balance_delta_status"] == "ambiguous"


def test_balance_increase_and_budget_breach_do_not_admit(tmp_path: Path) -> None:
    increased, _, _, _ = make_runner(
        tmp_path,
        balances=BalanceReader((8_000_000, 8_000_001)),
    )
    increase_result = increased.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    assert increase_result.decision.status == "inconclusive"
    assert increase_result.decision.reason_codes == ("provider_call_ambiguous",)

    over_budget, _, _, _ = make_runner(
        tmp_path,
        balances=BalanceReader((8_000_000, 2_999_999)),
    )
    budget_result = over_budget.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    assert budget_result.decision.status == "rejected"
    assert budget_result.decision.reason_codes == ("budget_exceeded",)


def test_post_call_balance_failure_is_inconclusive_and_never_repeats(
    tmp_path: Path,
) -> None:
    class FailAfterCall:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self) -> int:
            self.calls += 1
            if self.calls == 1:
                return 8_000_000
            raise RuntimeError("raw balance failure")

    balances = FailAfterCall()
    completion = Completion()
    runner, _, _, verifier = make_runner(
        tmp_path,
        balances=balances,
        completion=completion,
    )

    first = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    replay = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    document = json.loads(first.evidence_bytes)

    assert replay is first
    assert first.decision.status == "inconclusive"
    assert first.decision.reason_codes == ("provider_call_ambiguous",)
    assert document["balance_delta_micros_cny"] == 0
    assert document["balance_delta_status"] == "ambiguous"
    assert balances.calls == 2
    assert completion.calls == 1
    assert verifier.calls == 1


def test_completion_reported_multiple_calls_is_rejected(tmp_path: Path) -> None:
    multiple = Completion()
    multiple.result = deepcopy(multiple.result)
    object.__setattr__(multiple.result, "provider_call_count", 2)
    runner, _, _, _ = make_runner(tmp_path, completion=multiple)

    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )

    assert result.decision.status == "rejected"
    assert result.decision.reason_codes == ("policy_violation",)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("source_sha256", "f" * 64),
        ("patched_sha256", None),
        ("patched_sha256", "a" * 64),
        ("oracle_output_sha256", None),
        ("oracle_output_sha256", "b" * 64),
        ("public_case_count", 2),
        ("hidden_case_count", 9),
        ("source_write_count", 1),
        ("network_call_count", 1),
        ("child_process_count", 0),
        ("fixture_cleanup_count", 0),
    ),
)
def test_inconsistent_verifier_result_cannot_admit(
    field_name: str,
    bad_value: object,
    tmp_path: Path,
) -> None:
    valid = Verifier(tmp_path)(candidate())
    inconsistent = replace(valid, **{field_name: bad_value})
    runner, _, _, _ = make_runner(
        tmp_path,
        verifier=lambda value: inconsistent,
    )

    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )

    assert result.decision.status == "rejected"
    assert result.decision.reason_codes == ("candidate_verification_failed",)


def test_canonical_request_and_key_are_validated_before_any_read(
    tmp_path: Path,
) -> None:
    runner, balances, completion, verifier = make_runner(tmp_path)

    for canonical_request in (b"", "{}"):
        with pytest.raises(ModelGateRunnerViolation):
            runner.run(
                request=request_binding(),
                canonical_request=canonical_request,
                api_key=API_KEY,
            )

    for api_key in ("", "contains whitespace", "密钥", "x" * 513):
        with pytest.raises(ModelGateRunnerViolation):
            runner.run(
                request=request_binding(),
                canonical_request=CANONICAL_REQUEST,
                api_key=api_key,
            )

    assert balances.calls == 0
    assert completion.calls == 0
    assert verifier.calls == 0
