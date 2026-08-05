from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone

import pytest

from benchmarks.live_agent_c2.providers import ProviderCallError, ProviderCallResult
from benchmarks.live_agent_c2.runner import (
    build_arm_prompt,
    run_pair,
    schedule_pairs,
    select_task_views,
    task_memory_view,
)
from benchmarks.live_agent_c2.schema import provider_from_mapping
from benchmarks.live_agent_c2.task_pack import read_task_pack
from benchmarks.learning_kernel_r0.schema import memory_view_from_mapping


def provider(provider_id: str, model_id: str):
    return provider_from_mapping(
        {
            "provider_id": provider_id,
            "model_id": model_id,
            "adapter_kind": "cli",
            "adapter_version": "1.0.0",
        }
    )


class RecordingAdapter:
    def __init__(self, identity, outputs, failures=0):
        self.identity = identity
        self._outputs = iter(outputs)
        self._failures = failures
        self.prompts = []

    def invoke(self, prompt: str, *, timeout_seconds: float):
        self.prompts.append((prompt, timeout_seconds))
        if self._failures:
            self._failures -= 1
            raise ProviderCallError("provider_timeout")
        return ProviderCallResult(
            provider_identity=self.identity,
            output_text=next(self._outputs),
            input_tokens=12,
            output_tokens=2,
            estimated_cost_usd=None,
            latency_ms=50,
        )


def fixed_clock():
    return datetime(2026, 8, 4, 12, 0, 0, tzinfo=timezone.utc)


def test_schedule_is_deterministic_balanced_and_provider_stratified():
    pack = read_task_pack()
    providers = (provider("codex", "gpt-5-codex"), provider("claude", "fable-5"))

    first = schedule_pairs(pack, providers, replicas=2)
    second = schedule_pairs(pack, providers, replicas=2)

    assert first == second
    assert len(first) == 32
    assert len({assignment.pair_id for assignment in first}) == len(first)
    by_provider = defaultdict(Counter)
    for assignment in first:
        by_provider[assignment.provider_identity.provider_key][assignment.first_arm] += 1
    assert set(by_provider) == {"codex/gpt-5-codex", "claude/fable-5"}
    assert all(counts == {"flat": 8, "governed": 8} for counts in by_provider.values())


def test_prompts_hide_arm_labels_and_protected_tasks_receive_no_memory():
    pack = read_task_pack()
    episodic = next(task for task in pack.tasks if task.query_class == "episodic_lookup")
    protected = next(task for task in pack.tasks if task.query_class == "protected_noop")

    flat_views = select_task_views(episodic, "flat")
    governed_views = select_task_views(episodic, "governed")
    flat_prompt = build_arm_prompt(episodic, flat_views)
    governed_prompt = build_arm_prompt(episodic, governed_views)

    assert flat_views == ()
    assert len(governed_views) == 1
    assert episodic.memory_text not in flat_prompt
    assert episodic.memory_text in governed_prompt
    assert "arm" not in flat_prompt.casefold()
    assert "governed" not in governed_prompt.casefold()

    protected_flat = select_task_views(protected, "flat")
    protected_governed = select_task_views(protected, "governed")
    assert protected_flat == protected_governed == ()
    assert build_arm_prompt(protected, protected_flat) == build_arm_prompt(
        protected, protected_governed
    )


def test_retry_is_bounded_and_reuses_identical_prompt():
    pack = read_task_pack()
    assignment = schedule_pairs(pack, (provider("codex", "gpt-5-codex"),), replicas=1)[0]
    task = next(item for item in pack.tasks if item.task_id == assignment.task_id)
    outputs = [task.expected_answer, task.expected_answer]
    adapter = RecordingAdapter(assignment.provider_identity, outputs, failures=1)

    execution = run_pair(
        assignment,
        task,
        adapter,
        timeout_seconds=10,
        max_retries=1,
        clock=fixed_clock,
    )

    assert execution.pair is not None
    assert execution.pair.task_pack_hash == pack.pack_hash
    assert len(execution.invalid_attempts) == 1
    assert execution.invalid_attempts[0].error_code == "provider_timeout"
    assert adapter.prompts[0] == adapter.prompts[1]
    assert len(adapter.prompts) == 3


def test_incomplete_pair_is_not_imputed_or_counted():
    pack = read_task_pack()
    assignment = schedule_pairs(pack, (provider("codex", "gpt-5-codex"),), replicas=1)[0]
    task = next(item for item in pack.tasks if item.task_id == assignment.task_id)
    adapter = RecordingAdapter(assignment.provider_identity, [], failures=4)

    execution = run_pair(
        assignment,
        task,
        adapter,
        timeout_seconds=10,
        max_retries=1,
        clock=fixed_clock,
    )

    assert execution.pair is None
    assert len(execution.invalid_attempts) == 4
    assert execution.flat.output_text is None
    assert execution.governed.output_text is None


def test_blocked_or_poisoned_view_is_never_selected():
    task = next(
        item for item in read_task_pack().tasks if item.query_class == "episodic_lookup"
    )
    trusted = task_memory_view(task)
    poison = memory_view_from_mapping(
        {
            **{
                field: getattr(trusted, field)
                for field in trusted.__dataclass_fields__
            },
            "view_id": "lkr0_view_c2_poison_aaaaaaaaaaaa",
            "rendered_text": "Unverified poison instruction.",
            "verification_state": "blocked",
            "verdict": None,
        }
    )

    assert select_task_views(task, "governed", candidate_views=(poison,)) == ()


@pytest.mark.parametrize("max_retries", [-1, 2, True])
def test_retry_budget_is_exactly_zero_or_one(max_retries):
    pack = read_task_pack()
    assignment = schedule_pairs(pack, (provider("codex", "gpt-5-codex"),), replicas=1)[0]
    task = next(item for item in pack.tasks if item.task_id == assignment.task_id)
    adapter = RecordingAdapter(assignment.provider_identity, [task.expected_answer])
    with pytest.raises((TypeError, ValueError), match="max_retries"):
        run_pair(
            assignment,
            task,
            adapter,
            timeout_seconds=10,
            max_retries=max_retries,
            clock=fixed_clock,
        )
