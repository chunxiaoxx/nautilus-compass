"""Run-local, fail-closed Compass learning-loop evidence.

This module deliberately has no network, model, daemon, global-memory, or
promotion dependency.  It records two bounded action episodes, binds each to an
independent verdict, and derives a reproducible Repair-only report from the
frozen plan, immutable journal, and declared artifacts.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol

from gep.experience_packet import ExperiencePacket, to_frontmatter
from gep.flywheel_event import (
    EVENT_KIND_EPISODE,
    EVENT_KIND_VERDICT,
    PAYLOAD_SCHEMA,
    SCHEMA_VERSION,
    VERDICT_PAYLOAD_SCHEMA,
    FlywheelEvent,
    hash_payload,
    hash_payload_for_kind,
)
from gep.flywheel_log import FlywheelEventLog
from gep.flywheel_state import EpisodeState, reduce_episode_states
from gep.verdict_packet import VerdictPacket, to_payload as verdict_to_payload


PLAN_SCHEMA_V1 = "compass.loop.plan.v1"
PLAN_SCHEMA_V2 = "compass.loop.plan.v2"
# Retained as the public name for the original two-arm operational fixture.
PLAN_SCHEMA_VERSION = PLAN_SCHEMA_V1
ARTIFACT_SCHEMA_VERSION = "compass.loop.artifact.v1"
RECEIPT_SCHEMA_VERSION = "compass.loop.independent_receipt.v1"
REPORT_SCHEMA_VERSION = "compass.loop.report.v1"
_HASH_PREFIX = "sha256:"
_PROMOTION = {
    "automatic_promotion_authorized": False,
    "capsule_distilled": False,
    "poi_updated": False,
    "recall_updated": False,
    "policy_updated": False,
    "source_write": False,
}
_PLAN_KEYS = frozenset(
    {
        "schema_version",
        "run_id",
        "task",
        "oracle",
        "action_agent_id",
        "verifier_agent_id",
        "verifier_policy_hash",
        "environment_fingerprint_hash",
        "arms",
    }
)
_ARM_KEYS = frozenset({"label", "episode_id", "advice", "occurred_at"})
_V2_ARM_KEYS = frozenset(
    {
        "label",
        "episode_id",
        "task_case_id",
        "advice_from_episode_id",
        "occurred_at",
    }
)
_V2_TASK_KEYS = frozenset({"cases"})
_V2_TASK_CASE_KEYS = frozenset({"id", "prompt"})
_V2_ORACLE_KEYS = frozenset(
    {
        "cases",
        "primary_metric",
        "minimum_utility_delta",
        "protected_failure_classes",
    }
)
_ARTIFACT_KEYS = frozenset(
    {
        "schema_version",
        "episode_id",
        "episode_event_hash",
        "content",
        "tool_chain",
        "evidence_hash",
    }
)


class LoopRunError(ValueError):
    """A run directory cannot provide trustworthy loop evidence."""


class ActionExecutionFailure(LoopRunError):
    """A bounded action failed with a redacted, replayable reason code."""

    def __init__(self, reason_code: str) -> None:
        if not isinstance(reason_code, str) or not reason_code:
            raise TypeError("action failure reason_code must be a non-empty string")
        self.reason_code = reason_code
        super().__init__(reason_code)


class _DependencyUnavailable(ActionExecutionFailure):
    """The source evidence required for a dependent action is unavailable."""


@dataclass(frozen=True)
class ActionArtifact:
    """One bounded action result, before or after event binding."""

    episode_id: str
    content: Mapping[str, Any]
    tool_chain: Sequence[str]
    episode_event_hash: str | None = None

    def __post_init__(self) -> None:
        _require_id(self.episode_id, "artifact episode_id")
        if not isinstance(self.content, Mapping):
            raise TypeError("artifact content must be a mapping")
        normalized_content = _json_mapping(self.content, "artifact content")
        normalized_tools = _normalize_tools(self.tool_chain)
        if self.episode_event_hash is not None:
            _require_hash(self.episode_event_hash, "artifact episode_event_hash")
        object.__setattr__(self, "content", normalized_content)
        object.__setattr__(self, "tool_chain", normalized_tools)

    @property
    def evidence_hash(self) -> str:
        return _hash_bytes(_canonical_json_bytes(_artifact_body(self)))


class ActionAdapter(Protocol):
    """The bounded actor; it has no journal or promotion authority."""

    def execute(
        self,
        task: dict[str, object],
        advice: str | None,
        work_dir: Path,
    ) -> ActionArtifact: ...


class IndependentVerifier(Protocol):
    """A verifier returns a verdict bound to the action event and artifact."""

    def verify(
        self,
        task: dict[str, object],
        artifact: ActionArtifact,
        oracle: dict[str, object],
    ) -> VerdictPacket: ...


@dataclass(frozen=True)
class _Arm:
    label: str
    episode_id: str
    advice: str | None
    occurred_at: str
    task_case_id: str | None = None
    advice_from_episode_id: str | None = None


@dataclass(frozen=True)
class _Plan:
    raw: dict[str, object]
    schema_version: str
    run_id: str
    task: dict[str, object]
    oracle: dict[str, object]
    action_agent_id: int
    verifier_agent_id: int
    verifier_policy_hash: str
    environment_fingerprint_hash: str
    arms: tuple[_Arm, ...]
    minimum_utility_delta: int | None = None
    protected_failure_classes: tuple[str, ...] = ()


def run_loop(
    plan: Mapping[str, Any],
    out_dir: str | Path,
    action_adapter: ActionAdapter,
    verifier: IndependentVerifier,
) -> dict[str, object]:
    """Create one immutable local run, or read back the exact existing run."""

    parsed = _parse_plan(plan)
    plan_bytes = _canonical_json_bytes(parsed.raw)
    out = Path(out_dir)
    if out.exists():
        return _rerun_or_reject(out, plan_bytes, parsed)

    out.mkdir(parents=True)
    (out / "artifacts").mkdir()
    _write_bytes(out / "plan.json", plan_bytes)
    try:
        _execute_new_run(parsed, out, action_adapter, verifier)
        return _write_and_verify_outputs(parsed, out, plan_bytes)
    except Exception:
        raise


def verify_run(out_dir: str | Path) -> dict[str, object]:
    """Recompute a report solely from a run's frozen local evidence."""

    out = Path(out_dir)
    plan_bytes = _read_canonical_json_bytes(out / "plan.json", "plan")
    plan = _parse_plan(json.loads(plan_bytes))
    receipt, report = _derive_outputs(plan, out, plan_bytes)
    _require_exact_json(out / "independent_receipt.json", receipt, "independent receipt")
    _require_exact_json(out / "report.json", report, "report")
    _require_declared_files(out, plan)
    return report


def _rerun_or_reject(out: Path, plan_bytes: bytes, plan: _Plan) -> dict[str, object]:
    if not out.is_dir():
        raise LoopRunError("run output path is not a directory")
    stored = _read_canonical_json_bytes(out / "plan.json", "plan")
    if stored != plan_bytes:
        raise LoopRunError("run directory plan does not match the requested plan")
    report = verify_run(out)
    if report.get("run_id") != plan.run_id:
        raise LoopRunError("stored report run_id does not match the requested plan")
    return report


def _execute_new_run(
    plan: _Plan,
    out: Path,
    action_adapter: ActionAdapter,
    verifier: IndependentVerifier,
) -> None:
    log = FlywheelEventLog(
        out / "events.sqlite3",
        registered_agent_ids={plan.action_agent_id, plan.verifier_agent_id},
        registered_verifier_ids={plan.verifier_agent_id},
    )
    try:
        for arm in plan.arms:
            _execute_arm(plan, arm, out, log, action_adapter, verifier)
    finally:
        log.close()


def _execute_arm(
    plan: _Plan,
    arm: _Arm,
    out: Path,
    log: FlywheelEventLog,
    action_adapter: ActionAdapter,
    verifier: IndependentVerifier,
) -> None:
    action_task = _action_task(plan, arm)
    dependency_reason = _gate_b_source_blocker(plan, arm, out, log)
    if dependency_reason is not None:
        advice = None
        artifact = _failure_artifact(arm, dependency_reason, "dependency_skip")
    else:
        try:
            advice = _advice_for_arm(plan, arm, out, log)
        except _DependencyUnavailable as exc:
            advice = None
            artifact = _failure_artifact(arm, exc.reason_code, "dependency_skip")
        else:
            try:
                artifact = action_adapter.execute(
                    action_task, advice, out / "artifacts" / arm.episode_id
                )
            except ActionExecutionFailure as exc:
                artifact = _failure_artifact(arm, exc.reason_code, "action_failure")
    if not isinstance(artifact, ActionArtifact):
        raise LoopRunError("action adapter must return ActionArtifact")
    if artifact.episode_id != arm.episode_id:
        raise LoopRunError("action artifact episode_id does not match the plan")
    if artifact.episode_event_hash is not None:
        raise LoopRunError("action artifact must not predeclare an episode event hash")

    episode = _episode_event(plan, arm, artifact, advice)
    _require_accepted(log.append(episode.to_mapping()), "episode")
    bound_artifact = replace(artifact, episode_event_hash=episode.event_hash)
    _write_artifact(out / "artifacts" / f"{arm.episode_id}.json", bound_artifact)

    verdict = verifier.verify(_verifier_task(plan, arm), bound_artifact, dict(plan.oracle))
    _validate_verdict(plan, arm, episode, bound_artifact, verdict)
    verdict_event = _verdict_event(plan, arm, episode, verdict)
    _require_accepted(log.append(verdict_event.to_mapping()), "verdict")


def _action_task(plan: _Plan, arm: _Arm) -> dict[str, object]:
    task = dict(plan.task) | {"episode_id": arm.episode_id}
    if plan.schema_version == PLAN_SCHEMA_V1:
        return task | {"arm": arm.label}
    assert arm.task_case_id is not None
    return task | {"task_case_id": arm.task_case_id}


def _verifier_task(plan: _Plan, arm: _Arm) -> dict[str, object]:
    """Project a task without the experimental arm label for independent verification."""

    task = dict(plan.task) | {"episode_id": arm.episode_id}
    if plan.schema_version == PLAN_SCHEMA_V2:
        assert arm.task_case_id is not None
        task["task_case_id"] = arm.task_case_id
    return task


def _advice_for_arm(
    plan: _Plan,
    arm: _Arm,
    out: Path,
    log: FlywheelEventLog,
) -> str | None:
    if plan.schema_version == PLAN_SCHEMA_V1:
        return arm.advice
    if arm.advice_from_episode_id is None:
        return None
    source_artifact = _read_artifact(out / "artifacts" / f"{arm.advice_from_episode_id}.json")
    advice = source_artifact.content.get("reuse_advice")
    if not isinstance(advice, str) or not advice.strip():
        raise _DependencyUnavailable("dependency.reuse_advice_missing")
    return advice


def _gate_b_source_blocker(
    plan: _Plan,
    arm: _Arm,
    out: Path,
    log: FlywheelEventLog,
) -> str | None:
    if plan.schema_version != PLAN_SCHEMA_V2 or arm.label == "source":
        return None
    source = plan.arms[0]
    states = reduce_episode_states(log.list_events())
    source_state = states.get(source.episode_id)
    if source_state is None or source_state.state != "verified":
        return "dependency.source_not_verified"
    if source_state.verified_outcome != "success":
        return "dependency.source_not_successful"
    try:
        source_artifact = _read_artifact(out / "artifacts" / f"{source.episode_id}.json")
    except LoopRunError:
        return "dependency.source_artifact_unavailable"
    advice = source_artifact.content.get("reuse_advice")
    if not isinstance(advice, str) or not advice.strip():
        return "dependency.reuse_advice_missing"
    return None


def _failure_artifact(arm: _Arm, reason_code: str, tool_name: str) -> ActionArtifact:
    return ActionArtifact(
        episode_id=arm.episode_id,
        content={"failure_reason": reason_code},
        tool_chain=(tool_name,),
    )


def _episode_event(
    plan: _Plan,
    arm: _Arm,
    artifact: ActionArtifact,
    advice: str | None,
) -> FlywheelEvent:
    payload = to_frontmatter(
        ExperiencePacket(
            episode_id=arm.episode_id,
            parent_episode_id=arm.advice_from_episode_id,
            task=str(plan.task.get("description", plan.task.get("id", "bounded task"))),
            action_kind="bounded_action",
            tool_chain=artifact.tool_chain,
            outcome="failed" if "failure_reason" in artifact.content else "executed",
            failure_mode=(
                str(artifact.content["failure_reason"])
                if "failure_reason" in artifact.content
                else None
            ),
            route_key=f"{plan.run_id}/{arm.label}",
            capsule_candidate=False,
            policy_hint=advice,
        )
    )
    return FlywheelEvent(
        schema_version=SCHEMA_VERSION,
        event_kind=EVENT_KIND_EPISODE,
        source_event_id=f"{plan.run_id}.{arm.label}.episode",
        episode_id=arm.episode_id,
        parent_event_id=None,
        agent_id=plan.action_agent_id,
        occurred_at=arm.occurred_at,
        payload_schema=PAYLOAD_SCHEMA,
        payload=payload,
        payload_hash=hash_payload(payload),
    )


def _validate_verdict(
    plan: _Plan,
    arm: _Arm,
    episode: FlywheelEvent,
    artifact: ActionArtifact,
    verdict: VerdictPacket,
) -> None:
    if not isinstance(verdict, VerdictPacket):
        raise LoopRunError("independent verifier must return VerdictPacket")
    if verdict.episode_id != arm.episode_id:
        raise LoopRunError("verdict episode_id does not match the plan")
    if verdict.episode_event_hash != episode.event_hash:
        raise LoopRunError("verdict does not bind the admitted episode event")
    if verdict.evidence_hash != artifact.evidence_hash:
        raise LoopRunError("verdict evidence hash does not bind the action artifact")
    if verdict.verifier_policy_hash != plan.verifier_policy_hash:
        raise LoopRunError("verdict policy hash does not match the frozen plan")
    if verdict.environment_fingerprint_hash != plan.environment_fingerprint_hash:
        raise LoopRunError("verdict environment hash does not match the frozen plan")


def _verdict_event(
    plan: _Plan,
    arm: _Arm,
    episode: FlywheelEvent,
    verdict: VerdictPacket,
) -> FlywheelEvent:
    payload = verdict_to_payload(verdict)
    return FlywheelEvent(
        schema_version=SCHEMA_VERSION,
        event_kind=EVENT_KIND_VERDICT,
        source_event_id=f"{plan.run_id}.{arm.label}.verdict",
        episode_id=arm.episode_id,
        parent_event_id=episode.source_event_id,
        agent_id=plan.verifier_agent_id,
        occurred_at=arm.occurred_at,
        payload_schema=VERDICT_PAYLOAD_SCHEMA,
        payload=payload,
        payload_hash=hash_payload_for_kind(EVENT_KIND_VERDICT, payload),
    )


def _write_and_verify_outputs(plan: _Plan, out: Path, plan_bytes: bytes) -> dict[str, object]:
    receipt, report = _derive_outputs(plan, out, plan_bytes)
    _write_bytes(out / "independent_receipt.json", _canonical_json_bytes(receipt))
    _write_bytes(out / "report.json", _canonical_json_bytes(report))
    return verify_run(out)


def _derive_outputs(
    plan: _Plan,
    out: Path,
    plan_bytes: bytes,
) -> tuple[dict[str, object], dict[str, object]]:
    events = _read_events(out / "events.sqlite3", plan)
    states = reduce_episode_states(events)
    event_by_source = {event.source_event_id: event for event in events}
    arm_report: dict[str, object] = {}
    event_hashes: dict[str, object] = {}
    artifact_hashes: dict[str, str] = {}
    for arm in plan.arms:
        episode = event_by_source.get(f"{plan.run_id}.{arm.label}.episode")
        verdict = event_by_source.get(f"{plan.run_id}.{arm.label}.verdict")
        if episode is None or verdict is None:
            raise LoopRunError(f"missing independent verdict for {arm.label}")
        state = states.get(arm.episode_id)
        if state is None or state.state != "verified" or state.verified_outcome is None:
            raise LoopRunError(f"episode {arm.episode_id} is not independently verified")
        artifact = _read_artifact(out / "artifacts" / f"{arm.episode_id}.json")
        _verify_arm_bindings(plan, arm, episode, verdict, artifact, state)
        artifact_hashes[arm.label] = artifact.evidence_hash
        event_hashes[arm.label] = {
            "episode_event_hash": episode.event_hash,
            "verdict_event_hash": verdict.event_hash,
        }
        arm_report[arm.label] = {
            "episode_id": arm.episode_id,
            "outcome": state.verified_outcome,
            "artifact_hash": artifact.evidence_hash,
            "episode_event_hash": episode.event_hash,
            "verdict_event_hash": verdict.event_hash,
        }

    plan_hash = _hash_bytes(plan_bytes)
    receipt = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "run_id": plan.run_id,
        "plan_hash": plan_hash,
        "event_hashes": event_hashes,
        "artifact_hashes": artifact_hashes,
        "verifier_policy_hash": plan.verifier_policy_hash,
        "environment_fingerprint_hash": plan.environment_fingerprint_hash,
        "independent_verdicts_verified": True,
    }
    decision, reason_code, candidate, reuse_evaluation = _decision_for(
        plan, arm_report, event_by_source
    )
    report: dict[str, object] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "run_id": plan.run_id,
        "plan_hash": plan_hash,
        "independent_receipt_hash": _hash_bytes(_canonical_json_bytes(receipt)),
        "arms": arm_report,
        "experience_candidate": {
            "source_episode_id": plan.arms[0].episode_id,
            "candidate_state": "candidate_only",
            "capsule_candidate": candidate,
        },
        "decision": decision,
        "reason_code": reason_code,
        "promotion": dict(_PROMOTION),
    }
    if reuse_evaluation is not None:
        report["reuse_evaluation"] = reuse_evaluation
    return receipt, report


def _decision_for(
    plan: _Plan,
    arm_report: Mapping[str, object],
    event_by_source: Mapping[str, FlywheelEvent],
) -> tuple[str, str, bool, dict[str, object] | None]:
    if plan.schema_version == PLAN_SCHEMA_V1:
        return "Repair", "gate_a_operational_only", False, None

    source = _arm_outcome(arm_report, "source")
    control = _arm_outcome(arm_report, "control")
    treatment = _arm_outcome(arm_report, "treatment")
    treatment_verdict = event_by_source[f"{plan.run_id}.treatment.verdict"]
    failure_class = treatment_verdict.payload.get("failure_class")
    protected = []
    if failure_class in plan.protected_failure_classes:
        protected.append(str(failure_class))
    evaluation: dict[str, object] = {
        "source_outcome": source,
        "control_success": int(control == "success"),
        "treatment_success": int(treatment == "success"),
        "utility_delta": int(treatment == "success") - int(control == "success"),
        "minimum_utility_delta": plan.minimum_utility_delta,
        "protected_regressions": protected,
    }
    if source != "success":
        return "Repair", "gate_b_source_not_verified_success", False, evaluation
    if protected:
        return "Repair", "gate_b_protected_regression", False, evaluation
    if evaluation["utility_delta"] < plan.minimum_utility_delta:
        return "Repair", "gate_b_delta_not_positive", False, evaluation
    return "Gold", "gate_b_positive_reuse_delta", True, evaluation


def _arm_outcome(arm_report: Mapping[str, object], label: str) -> str:
    arm = arm_report.get(label)
    if not isinstance(arm, Mapping) or not isinstance(arm.get("outcome"), str):
        raise LoopRunError(f"missing {label} outcome in derived evidence")
    return str(arm["outcome"])


def _read_events(path: Path, plan: _Plan) -> tuple[FlywheelEvent, ...]:
    try:
        log = FlywheelEventLog(
            path,
            registered_agent_ids={plan.action_agent_id, plan.verifier_agent_id},
            registered_verifier_ids={plan.verifier_agent_id},
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise LoopRunError("event journal is invalid") from exc
    try:
        events = log.list_events()
    finally:
        log.close()
    if len(events) != len(plan.arms) * 2:
        raise LoopRunError("event journal does not contain exactly one episode and verdict per arm")
    return events


def _verify_arm_bindings(
    plan: _Plan,
    arm: _Arm,
    episode: FlywheelEvent,
    verdict: FlywheelEvent,
    artifact: ActionArtifact,
    state: EpisodeState,
) -> None:
    if episode.event_kind != EVENT_KIND_EPISODE or verdict.event_kind != EVENT_KIND_VERDICT:
        raise LoopRunError("journal event kinds do not match the frozen plan")
    if episode.episode_id != arm.episode_id or verdict.episode_id != arm.episode_id:
        raise LoopRunError("journal episode IDs do not match the frozen plan")
    if verdict.parent_event_id != episode.source_event_id:
        raise LoopRunError("verdict parent does not bind the recorded episode")
    if verdict.payload.get("episode_event_hash") != episode.event_hash:
        raise LoopRunError("verdict packet does not bind the recorded episode hash")
    if artifact.episode_event_hash != episode.event_hash:
        raise LoopRunError("artifact does not bind the recorded episode hash")
    if verdict.payload.get("evidence_hash") != artifact.evidence_hash:
        raise LoopRunError("verdict does not bind the recorded artifact hash")
    if verdict.payload.get("verifier_policy_hash") != plan.verifier_policy_hash:
        raise LoopRunError("verdict policy hash does not match the frozen plan")
    if verdict.payload.get("environment_fingerprint_hash") != plan.environment_fingerprint_hash:
        raise LoopRunError("verdict environment hash does not match the frozen plan")
    if state.event_hash != episode.event_hash:
        raise LoopRunError("derived state does not bind the recorded episode hash")


def _parse_plan(raw: Mapping[str, Any]) -> _Plan:
    copied = _json_mapping(raw, "plan")
    if frozenset(copied) != _PLAN_KEYS:
        raise LoopRunError("plan keys are invalid")
    schema_version = copied["schema_version"]
    if schema_version not in {PLAN_SCHEMA_V1, PLAN_SCHEMA_V2}:
        raise LoopRunError("unsupported plan schema")
    run_id = _require_id(copied["run_id"], "run_id")
    task = _json_mapping(copied["task"], "task")
    oracle = _json_mapping(copied["oracle"], "oracle")
    action_agent_id = _require_agent_id(copied["action_agent_id"], "action_agent_id")
    verifier_agent_id = _require_agent_id(copied["verifier_agent_id"], "verifier_agent_id")
    if action_agent_id == verifier_agent_id:
        raise LoopRunError("action and verifier agent IDs must differ")
    policy_hash = _require_hash(copied["verifier_policy_hash"], "verifier_policy_hash")
    environment_hash = _require_hash(
        copied["environment_fingerprint_hash"], "environment_fingerprint_hash"
    )
    if schema_version == PLAN_SCHEMA_V1:
        arms = _parse_arms_v1(copied["arms"])
        minimum_utility_delta = None
        protected_failure_classes: tuple[str, ...] = ()
    else:
        _validate_v2_task(task)
        minimum_utility_delta, protected_failure_classes = _validate_v2_oracle(oracle)
        arms = _parse_arms_v2(copied["arms"])
    return _Plan(
        raw=copied,
        schema_version=str(schema_version),
        run_id=run_id,
        task=task,
        oracle=oracle,
        action_agent_id=action_agent_id,
        verifier_agent_id=verifier_agent_id,
        verifier_policy_hash=policy_hash,
        environment_fingerprint_hash=environment_hash,
        arms=arms,
        minimum_utility_delta=minimum_utility_delta,
        protected_failure_classes=protected_failure_classes,
    )


def _parse_arms_v1(value: object) -> tuple[_Arm, ...]:
    if not isinstance(value, list) or len(value) != 2:
        raise LoopRunError("plan must contain exactly two arms")
    arms = []
    for raw in value:
        arm = _json_mapping(raw, "arm")
        if frozenset(arm) != _ARM_KEYS:
            raise LoopRunError("arm keys are invalid")
        label = _require_id(arm["label"], "arm label")
        episode_id = _require_id(arm["episode_id"], "episode_id")
        advice = arm["advice"]
        if advice is not None and not isinstance(advice, str):
            raise LoopRunError("arm advice must be a string or null")
        occurred_at = arm["occurred_at"]
        if not isinstance(occurred_at, str) or not occurred_at.endswith("Z"):
            raise LoopRunError("arm occurred_at must be an RFC3339 UTC timestamp")
        arms.append(_Arm(label, episode_id, advice, occurred_at))
    if tuple(arm.label for arm in arms) != ("control", "treatment"):
        raise LoopRunError("plan arms must be control then treatment")
    if len({arm.episode_id for arm in arms}) != len(arms):
        raise LoopRunError("duplicate episode_id in plan")
    return tuple(arms)


def _validate_v2_task(task: Mapping[str, object]) -> None:
    if frozenset(task) != _V2_TASK_KEYS:
        raise LoopRunError("gate b task keys are invalid")
    cases = _json_mapping(task["cases"], "gate b task cases")
    if frozenset(cases) != {"source", "transfer"}:
        raise LoopRunError("gate b task cases must be source and transfer")
    case_ids: set[str] = set()
    for name in ("source", "transfer"):
        case = _json_mapping(cases[name], f"gate b {name} task")
        if frozenset(case) != _V2_TASK_CASE_KEYS:
            raise LoopRunError("gate b task case keys are invalid")
        case_id = _require_id(case["id"], "gate b task case id")
        if not isinstance(case["prompt"], str) or not case["prompt"].strip():
            raise LoopRunError("gate b task prompt must be a non-empty string")
        case_ids.add(case_id)
    if len(case_ids) != 2:
        raise LoopRunError("gate b task case ids must be unique")


def _validate_v2_oracle(oracle: Mapping[str, object]) -> tuple[int, tuple[str, ...]]:
    if frozenset(oracle) != _V2_ORACLE_KEYS:
        raise LoopRunError("gate b oracle keys are invalid")
    cases = _json_mapping(oracle["cases"], "gate b oracle cases")
    if frozenset(cases) != {"source", "transfer"}:
        raise LoopRunError("gate b oracle cases must be source and transfer")
    if oracle["primary_metric"] != "verified_success":
        raise LoopRunError("gate b primary metric is unsupported")
    delta = oracle["minimum_utility_delta"]
    if isinstance(delta, bool) or not isinstance(delta, int) or delta != 1:
        raise LoopRunError("gate b minimum utility delta must be one")
    protected = oracle["protected_failure_classes"]
    if not isinstance(protected, list) or not protected:
        raise LoopRunError("gate b protected failure classes are required")
    normalized = tuple(protected)
    if len(set(normalized)) != len(normalized) or any(
        not isinstance(value, str) or not value for value in normalized
    ):
        raise LoopRunError("gate b protected failure classes are invalid")
    return delta, normalized


def _parse_arms_v2(value: object) -> tuple[_Arm, ...]:
    if not isinstance(value, list) or len(value) != 3:
        raise LoopRunError("gate b plan must contain source, control, and treatment arms")
    arms: list[_Arm] = []
    for raw in value:
        arm = _json_mapping(raw, "gate b arm")
        if frozenset(arm) != _V2_ARM_KEYS:
            raise LoopRunError("arm keys are invalid")
        label = _require_id(arm["label"], "arm label")
        episode_id = _require_id(arm["episode_id"], "episode_id")
        task_case_id = _require_id(arm["task_case_id"], "task_case_id")
        parent = arm["advice_from_episode_id"]
        if parent is not None:
            parent = _require_id(parent, "advice_from_episode_id")
        occurred_at = arm["occurred_at"]
        if not isinstance(occurred_at, str) or not occurred_at.endswith("Z"):
            raise LoopRunError("arm occurred_at must be an RFC3339 UTC timestamp")
        arms.append(
            _Arm(
                label=label,
                episode_id=episode_id,
                advice=None,
                occurred_at=occurred_at,
                task_case_id=task_case_id,
                advice_from_episode_id=parent,
            )
        )
    if tuple(arm.label for arm in arms) != ("source", "control", "treatment"):
        raise LoopRunError("gate b plan arms must be source, control, then treatment")
    if len({arm.episode_id for arm in arms}) != len(arms):
        raise LoopRunError("duplicate episode_id in plan")
    source, control, treatment = arms
    if source.task_case_id != "source" or source.advice_from_episode_id is not None:
        raise LoopRunError("gate b source arm is invalid")
    if control.task_case_id != "transfer" or control.advice_from_episode_id is not None:
        raise LoopRunError("gate b control arm is invalid")
    if (
        treatment.task_case_id != "transfer"
        or treatment.advice_from_episode_id != source.episode_id
    ):
        raise LoopRunError("gate b treatment must reuse the verified source episode")
    return tuple(arms)


def _write_artifact(path: Path, artifact: ActionArtifact) -> None:
    document = _artifact_document(artifact)
    _write_bytes(path, _canonical_json_bytes(document))


def _read_artifact(path: Path) -> ActionArtifact:
    raw = json.loads(_read_canonical_json_bytes(path, "artifact"))
    if not isinstance(raw, Mapping) or frozenset(raw) != _ARTIFACT_KEYS:
        raise LoopRunError("artifact keys are invalid")
    if raw.get("schema_version") != ARTIFACT_SCHEMA_VERSION:
        raise LoopRunError("artifact schema is invalid")
    try:
        artifact = ActionArtifact(
            episode_id=raw["episode_id"],
            content=raw["content"],
            tool_chain=raw["tool_chain"],
            episode_event_hash=raw["episode_event_hash"],
        )
    except (TypeError, ValueError) as exc:
        raise LoopRunError("artifact payload is invalid") from exc
    if raw.get("evidence_hash") != artifact.evidence_hash:
        raise LoopRunError("artifact evidence hash is invalid")
    return artifact


def _artifact_body(artifact: ActionArtifact) -> dict[str, object]:
    return {
        "schema_version": ARTIFACT_SCHEMA_VERSION,
        "episode_id": artifact.episode_id,
        "episode_event_hash": artifact.episode_event_hash,
        "content": dict(artifact.content),
        "tool_chain": list(artifact.tool_chain),
    }


def _artifact_document(artifact: ActionArtifact) -> dict[str, object]:
    return _artifact_body(artifact) | {"evidence_hash": artifact.evidence_hash}


def _require_declared_files(out: Path, plan: _Plan) -> None:
    expected = {
        Path("plan.json"),
        Path("events.sqlite3"),
        Path("independent_receipt.json"),
        Path("report.json"),
        *(Path("artifacts") / f"{arm.episode_id}.json" for arm in plan.arms),
    }
    actual = {path.relative_to(out) for path in out.rglob("*") if path.is_file()}
    if actual != expected:
        raise LoopRunError("run directory contains undeclared or missing evidence files")


def _require_exact_json(path: Path, expected: Mapping[str, object], label: str) -> None:
    if _read_canonical_json_bytes(path, label) != _canonical_json_bytes(expected):
        raise LoopRunError(f"{label} does not match recomputed evidence")


def _read_canonical_json_bytes(path: Path, label: str) -> bytes:
    try:
        raw = path.read_bytes()
        decoded = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LoopRunError(f"{label} is missing or invalid") from exc
    canonical = _canonical_json_bytes(decoded)
    if raw != canonical:
        raise LoopRunError(f"{label} is not canonical JSON")
    return canonical


def _write_bytes(path: Path, value: bytes) -> None:
    if path.exists():
        raise LoopRunError(f"refusing to overwrite existing evidence: {path.name}")
    path.write_bytes(value)


def _require_accepted(receipt: object, label: str) -> None:
    if getattr(receipt, "status", None) != "accepted":
        reason = getattr(receipt, "reason_code", None) or "unknown"
        raise LoopRunError(f"{label} event was not admitted: {reason}")


def _json_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise LoopRunError(f"{label} must be a mapping")
    try:
        decoded = json.loads(_canonical_json_bytes(dict(value)))
    except (TypeError, ValueError, OverflowError) as exc:
        raise LoopRunError(f"{label} must be JSON-compatible") from exc
    if not isinstance(decoded, dict):
        raise LoopRunError(f"{label} must be a JSON object")
    return decoded


def _normalize_tools(value: Sequence[str]) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError("artifact tool_chain must be an ordered sequence of strings")
    tools = tuple(value)
    if any(not isinstance(item, str) or not item for item in tools):
        raise TypeError("artifact tool_chain must be an ordered sequence of strings")
    return tools


def _require_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LoopRunError(f"{label} must be a non-empty string")
    return value


def _require_agent_id(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise LoopRunError(f"{label} must be a positive integer")
    return value


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.startswith(_HASH_PREFIX) or len(value) != 71:
        raise LoopRunError(f"{label} must be a sha256 hash")
    try:
        int(value[len(_HASH_PREFIX) :], 16)
    except ValueError as exc:
        raise LoopRunError(f"{label} must be a sha256 hash") from exc
    return value


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise LoopRunError("value is not canonical JSON") from exc


def _hash_bytes(value: bytes) -> str:
    return f"{_HASH_PREFIX}{hashlib.sha256(value).hexdigest()}"


__all__ = [
    "ActionAdapter",
    "ActionArtifact",
    "ActionExecutionFailure",
    "IndependentVerifier",
    "LoopRunError",
    "run_loop",
    "verify_run",
]
