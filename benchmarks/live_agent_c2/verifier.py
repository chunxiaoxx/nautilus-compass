"""Deterministic, hash-only answer verification for Compass C2."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from benchmarks.poi_gate2.canonical import hash_json

from .schema import LiveTask


MAX_OUTPUT_CHARACTERS = 4096
_STEP_SEPARATOR = re.compile(r"\s*(?:->|>)\s*")


@dataclass(frozen=True, slots=True)
class VerificationResult:
    success: bool
    verifier_code: str
    response_hash: str
    normalized_answer_hash: str
    verifier_policy_hash: str
    evidence_hash: str


def verify_output(task: LiveTask, output_text: str) -> VerificationResult:
    if not isinstance(task, LiveTask):
        raise TypeError("task must be a LiveTask")
    if not isinstance(output_text, str):
        raise TypeError("output_text must be a string")

    output_hash = response_hash(output_text)
    malformed_code = _malformed_code(output_text)
    if malformed_code is not None:
        return _result(task, output_hash, malformed_code, False, malformed_code)

    verifier = _VERIFIERS[task.verifier_kind]
    actual, expected = verifier(output_text, task.expected_answer)
    success = actual == expected
    if success:
        success_codes = {
            "exact_text": "exact_match",
            "ordered_steps": "ordered_match",
            "exact_set": "set_match",
        }
        code = success_codes[task.verifier_kind]
    else:
        code = "answer_mismatch"
    return _result(task, output_hash, actual, success, code)


def response_hash(output_text: str) -> str:
    if not isinstance(output_text, str):
        raise TypeError("output_text must be a string")
    return hash_json(
        {"domain": "compass.live_agent_c2.provider_response.v1", "text": output_text}
    )


def _result(
    task: LiveTask,
    response_hash: str,
    normalized: str,
    success: bool,
    code: str,
) -> VerificationResult:
    normalized_hash = hash_json(
        {"domain": "compass.live_agent_c2.normalized_answer.v1", "value": normalized}
    )
    evidence_hash = hash_json(
        {
            "domain": "compass.live_agent_c2.verification_evidence.v1",
            "normalized_answer_hash": normalized_hash,
            "response_hash": response_hash,
            "success": success,
            "task_hash": task.task_hash,
            "verifier_code": code,
            "verifier_policy_hash": task.verifier_policy_hash,
        }
    )
    return VerificationResult(
        success=success,
        verifier_code=code,
        response_hash=response_hash,
        normalized_answer_hash=normalized_hash,
        verifier_policy_hash=task.verifier_policy_hash,
        evidence_hash=evidence_hash,
    )


def _malformed_code(output_text: str) -> str | None:
    if not output_text.strip():
        return "malformed_empty"
    if "\x00" in output_text:
        return "malformed_control"
    if len(output_text) > MAX_OUTPUT_CHARACTERS:
        return "malformed_oversize"
    return None


def _normalize_text(actual: str, expected: str) -> tuple[str, str]:
    return actual.strip().casefold(), expected.strip().casefold()


def _normalize_steps(actual: str, expected: str) -> tuple[str, str]:
    return _ordered_value(actual), _ordered_value(expected)


def _ordered_value(value: str) -> str:
    return ">".join(part.strip().casefold() for part in _STEP_SEPARATOR.split(value.strip()))


def _normalize_set(actual: str, expected: str) -> tuple[str, str]:
    return _set_value(actual), _set_value(expected)


def _set_value(value: str) -> str:
    members = tuple(part.strip().casefold() for part in value.strip().split(","))
    if any(not member for member in members) or len(members) != len(set(members)):
        return "<invalid-set>"
    return ",".join(sorted(members))


_VERIFIERS: dict[str, Callable[[str, str], tuple[str, str]]] = {
    "exact_text": _normalize_text,
    "ordered_steps": _normalize_steps,
    "exact_set": _normalize_set,
}


__all__ = [
    "MAX_OUTPUT_CHARACTERS",
    "VerificationResult",
    "response_hash",
    "verify_output",
]
