from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest
from nacl.signing import SigningKey

from benchmarks.live_agent_c2.evidence import (
    bundle_from_mapping,
    bundle_to_mapping,
    project_episode,
    verify_episode_bundle,
)
from benchmarks.live_agent_c2.providers import ProviderCallResult
from benchmarks.live_agent_c2.runner import run_pair, schedule_pairs
from benchmarks.live_agent_c2.schema import provider_from_mapping
from benchmarks.live_agent_c2.schema import attempt_to_mapping
from benchmarks.live_agent_c2.task_pack import read_task_pack
from gep.flywheel_log import FlywheelEventLog


ACTION_AGENT_ID = 4101
VERIFIER_AGENT_ID = 4201
SIGNING_KEY = SigningKey(bytes(range(32)))


def provider():
    return provider_from_mapping(
        {
            "provider_id": "codex",
            "model_id": "gpt-5-codex",
            "adapter_kind": "cli",
            "adapter_version": "1.0.0",
        }
    )


class ExactAdapter:
    def __init__(self, identity, answer):
        self.identity = identity
        self.answer = answer

    def invoke(self, prompt: str, *, timeout_seconds: float):
        return ProviderCallResult(
            provider_identity=self.identity,
            output_text=self.answer,
            input_tokens=10,
            output_tokens=2,
            estimated_cost_usd=None,
            latency_ms=20,
        )


def clock():
    return datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


def successful_execution():
    pack = read_task_pack()
    assignment = schedule_pairs(pack, (provider(),), replicas=1)[0]
    task = next(item for item in pack.tasks if item.task_id == assignment.task_id)
    execution = run_pair(
        assignment,
        task,
        ExactAdapter(assignment.provider_identity, task.expected_answer),
        timeout_seconds=10,
        max_retries=0,
        clock=clock,
    )
    return pack, task, execution


def event_log(path):
    return FlywheelEventLog(
        path,
        registered_agent_ids=(ACTION_AGENT_ID, VERIFIER_AGENT_ID),
        registered_verifier_ids=(VERIFIER_AGENT_ID,),
    )


def test_each_arm_projects_packet_independent_verdict_signature_and_poi(tmp_path):
    pack, task, execution = successful_execution()
    log = event_log(tmp_path / "flywheel.sqlite")
    try:
        flat = project_episode(
            execution.flat,
            task=task,
            task_pack_hash=pack.pack_hash,
            event_log=log,
            action_agent_id=ACTION_AGENT_ID,
            verifier_agent_id=VERIFIER_AGENT_ID,
            signing_key=SIGNING_KEY,
        )
        governed = project_episode(
            execution.governed,
            task=task,
            task_pack_hash=pack.pack_hash,
            event_log=log,
            action_agent_id=ACTION_AGENT_ID,
            verifier_agent_id=VERIFIER_AGENT_ID,
            signing_key=SIGNING_KEY,
        )

        assert log.count_events() == 4
        assert flat.packet.capsule_candidate is False
        assert governed.packet.capsule_candidate is False
        assert flat.verdict.episode_event_hash == flat.episode_event.event_hash
        assert governed.verdict.episode_event_hash == governed.episode_event.event_hash
        assert flat.poi_signal.impact == 0.0
        assert governed.poi_signal.impact == 1.0
        assert verify_episode_bundle(flat, event_log=log) is True
        assert verify_episode_bundle(governed, event_log=log) is True
        assert bundle_to_mapping(flat)["attempt"] == attempt_to_mapping(
            execution.flat.attempt
        )
        assert "output_text" not in repr(flat)
    finally:
        log.close()


def test_projection_is_idempotent_and_replay_detects_signature_tampering(tmp_path):
    pack, task, execution = successful_execution()
    log = event_log(tmp_path / "flywheel.sqlite")
    try:
        first = project_episode(
            execution.flat,
            task=task,
            task_pack_hash=pack.pack_hash,
            event_log=log,
            action_agent_id=ACTION_AGENT_ID,
            verifier_agent_id=VERIFIER_AGENT_ID,
            signing_key=SIGNING_KEY,
        )
        second = project_episode(
            execution.flat,
            task=task,
            task_pack_hash=pack.pack_hash,
            event_log=log,
            action_agent_id=ACTION_AGENT_ID,
            verifier_agent_id=VERIFIER_AGENT_ID,
            signing_key=SIGNING_KEY,
        )

        assert first.bundle_hash == second.bundle_hash
        assert log.count_events() == 2
        assert bundle_from_mapping(bundle_to_mapping(first)) == first
        invalid = bundle_to_mapping(first)
        invalid["raw_output"] = "forbidden"
        with pytest.raises(TypeError, match="unknown EpisodeEvidenceBundle fields"):
            bundle_from_mapping(invalid)
        tampered_attempt = bundle_to_mapping(first)
        tampered_attempt["attempt"]["latency_ms"] += 1
        with pytest.raises(ValueError, match="attempt"):
            bundle_from_mapping(tampered_attempt)
        tampered = replace(first, verdict_signature="0" * 128)
        with pytest.raises(ValueError, match="signature"):
            verify_episode_bundle(tampered, event_log=log)
    finally:
        log.close()


def test_self_verdict_and_incomplete_attempt_fail_closed(tmp_path):
    pack, task, execution = successful_execution()
    log = event_log(tmp_path / "flywheel.sqlite")
    try:
        with pytest.raises(ValueError, match="independent"):
            project_episode(
                execution.flat,
                task=task,
                task_pack_hash=pack.pack_hash,
                event_log=log,
                action_agent_id=ACTION_AGENT_ID,
                verifier_agent_id=ACTION_AGENT_ID,
                signing_key=SIGNING_KEY,
            )
        incomplete = replace(execution.flat, output_text=None)
        with pytest.raises(ValueError, match="valid completed arm"):
            project_episode(
                incomplete,
                task=task,
                task_pack_hash=pack.pack_hash,
                event_log=log,
                action_agent_id=ACTION_AGENT_ID,
                verifier_agent_id=VERIFIER_AGENT_ID,
                signing_key=SIGNING_KEY,
            )
    finally:
        log.close()
