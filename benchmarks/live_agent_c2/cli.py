"""One-command dry-run, synthetic E2E, and replay entry point for Compass C2."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional, Sequence

from benchmarks.poi_gate2.canonical import hash_json
from gep.flywheel_log import FlywheelEventLog

from .evidence import (
    EpisodeEvidenceBundle,
    bundle_from_mapping,
    bundle_to_mapping,
    project_episode,
    verify_episode_bundle,
)
from .metrics import (
    C2Metrics,
    PairOutcome,
    compute_metrics,
    outcome_from_mapping,
    outcome_to_mapping,
)
from .policy import evaluate_c2_policy
from .providers import (
    LIVE_PROVIDER_NAMES,
    ProviderCallError,
    ProviderCallResult,
    build_live_adapters,
)
from .runner import PairAssignment, PairExecution, ProviderAdapter, run_pair, schedule_pairs
from .schema import LiveTask, ProviderIdentity, provider_from_mapping
from .task_pack import C2TaskPack, read_task_pack
from .verifier import response_hash, verify_output


ACTION_AGENT_ID = 4101
VERIFIER_AGENT_ID = 4201
RUN_MANIFEST_SCHEMA = "compass.live_agent_c2.run_manifest.v1"
FAKE_PROVIDERS = ("fake-alpha", "fake-beta")
ALL_PROVIDER_NAMES = (*FAKE_PROVIDERS, *LIVE_PROVIDER_NAMES)
AdapterResolver = Callable[[PairAssignment, LiveTask], ProviderAdapter]


class _SyntheticAdapter:
    def __init__(self, identity: ProviderIdentity, task: LiveTask) -> None:
        self.identity = identity
        self._task = task

    def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
        has_context = self._task.memory_text is not None and self._task.memory_text in prompt
        output = self._task.expected_answer if self._task.protected or has_context else "unknown"
        return ProviderCallResult(
            provider_identity=self.identity,
            output_text=output,
            input_tokens=max(1, len(prompt.split())),
            output_tokens=max(1, len(output.split())),
            estimated_cost_usd=None,
            latency_ms=1,
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.live_agent_c2")
    parser.add_argument(
        "--mode",
        choices=("dry-run", "fake", "probe", "pilot", "formal", "replay"),
        required=True,
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--provider", action="append", choices=ALL_PROVIDER_NAMES)
    parser.add_argument("--replicas", type=int)
    parser.add_argument("--limit-pairs", type=int)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    parser.add_argument("--timeout-seconds", type=float, default=90.0)
    parser.add_argument("--resume", action="store_true")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.mode == "replay":
        report = replay_run(args.output)
        _print_json(report)
        return 0
    _validate_args(args)
    pack = read_task_pack()
    if args.mode in {"probe", "pilot", "formal"}:
        adapters = build_live_adapters(args.provider)
        if len(adapters) < 2:
            raise ValueError("live runs require at least two admissible providers")
        if any(not adapter.admissible for adapter in adapters):
            raise ValueError("live runs require admissible provider isolation")
        if args.mode == "probe":
            report = _probe_live(args.output, adapters, args.timeout_seconds)
            _print_json(report)
            return 0 if report["admissible_provider_count"] == len(adapters) else 2
        providers = tuple(adapter.identity for adapter in adapters)
    else:
        providers = _fake_provider_identities(args.provider)
        adapters = ()
    replicas = _effective_replicas(args)
    assignments = schedule_pairs(pack, providers, replicas=replicas)
    if args.mode == "pilot":
        assignments = _pilot_assignments(assignments, pack)
    if args.limit_pairs is not None:
        assignments = assignments[: args.limit_pairs]
    if args.mode == "dry-run":
        _print_json(
            {
                "improvement_claim": False,
                "mode": "dry-run",
                "provider_count": len(providers),
                "runtime_recommendation": "flat",
                "scheduled_pairs": len(assignments),
                "task_count": len(pack.tasks),
                "task_pack_hash": pack.pack_hash,
            }
        )
        return 0
    config = _run_config(args, pack, providers, len(assignments), replicas)
    if args.output.exists() and any(args.output.iterdir()):
        if not args.resume:
            raise ValueError("output directory must be absent or empty unless --resume is used")
        manifest = _read_json(args.output / "run_manifest.json")
        if manifest.get("config_hash") != config["config_hash"]:
            raise ValueError("resume configuration does not match existing run")
        report = replay_run(args.output)
        _print_json(report)
        return 0
    if args.mode in {"pilot", "formal"}:
        report = _run_live(
            args.output,
            pack,
            assignments,
            config,
            args.bootstrap_samples,
            adapters,
            args.timeout_seconds,
        )
    else:
        report = _run_synthetic(
            args.output, pack, assignments, config, args.bootstrap_samples
        )
    _print_json(report)
    return 0


def replay_run(output: Path) -> dict[str, object]:
    root = Path(output)
    manifest = _read_json(root / "run_manifest.json")
    if manifest.get("schema_version") != RUN_MANIFEST_SCHEMA:
        raise ValueError("unsupported run manifest schema")
    pack = read_task_pack()
    if manifest.get("task_pack_hash") != pack.pack_hash:
        raise ValueError("run manifest task pack mismatch")
    bundles = tuple(
        bundle_from_mapping(item) for item in _read_jsonl(root / "bundles.jsonl")
    )
    outcomes = tuple(
        outcome_from_mapping(item) for item in _read_jsonl(root / "outcomes.jsonl")
    )
    tasks_by_hash = {task.task_hash: task for task in pack.tasks}
    event_log = _event_log(root / "flywheel.sqlite")
    try:
        for bundle in bundles:
            if bundle.verifier_public_key != manifest.get("verifier_public_key"):
                raise ValueError("bundle verifier key does not match run manifest")
            task = tasks_by_hash.get(bundle.task_hash)
            if task is None:
                raise ValueError("bundle task hash is not in frozen task pack")
            raw = (root / "raw" / f"{bundle.attempt_id}.txt").read_text(encoding="utf-8")
            if verify_output(task, raw) != bundle.verification:
                raise ValueError("raw response does not replay to stored verification")
            verify_episode_bundle(bundle, event_log=event_log)
    finally:
        event_log.close()
    stored_summary = _read_json(root / "summary.json")
    metrics = compute_metrics(
        outcomes,
        seed=int(manifest["seed"]),
        bootstrap_samples=int(manifest["bootstrap_samples"]),
        invalid_attempt_count=int(stored_summary["invalid_attempt_count"]),
        retry_count=int(stored_summary["retry_count"]),
    )
    if metrics.pairs_hash != stored_summary.get("pairs_hash"):
        raise ValueError("outcome replay hash mismatch")
    if len(bundles) != 2 * len(outcomes):
        raise ValueError("every complete pair must have two evidence bundles")
    report = dict(stored_summary)
    report["replay_verified"] = True
    return report


def _probe_live(output: Path, adapters, timeout_seconds: float) -> dict[str, object]:
    if output.exists() and any(output.iterdir()):
        raise ValueError("output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    providers = []
    for adapter in adapters:
        try:
            result = adapter.invoke(
                "Compute 17 plus 25 and return only the integer.",
                timeout_seconds=timeout_seconds,
            )
            verified = result.output_text.strip() == "42"
            providers.append(
                {
                    "cost_known": result.estimated_cost_usd is not None,
                    "estimated_cost_usd": result.estimated_cost_usd,
                    "input_tokens": result.input_tokens,
                    "latency_ms": result.latency_ms,
                    "output_tokens": result.output_tokens,
                    "provider_key": result.provider_identity.provider_key,
                    "response_hash": response_hash(result.output_text),
                    "verified": verified,
                }
            )
        except ProviderCallError as error:
            providers.append(
                {
                    "error_code": error.reason_code,
                    "provider_key": adapter.identity.provider_key,
                    "verified": False,
                }
            )
    report = {
        "admissible_provider_count": sum(item["verified"] for item in providers),
        "improvement_claim": False,
        "mode": "probe",
        "providers": providers,
        "runtime_recommendation": "flat",
    }
    _write_json(output / "provider_probe.json", report)
    return report


def _run_synthetic(
    output: Path,
    pack: C2TaskPack,
    assignments,
    config: dict[str, object],
    bootstrap_samples: int,
) -> dict[str, object]:
    from nacl.signing import SigningKey

    signing_key = SigningKey(bytes(range(32)))
    return _run_experiment(
        output,
        pack,
        assignments,
        config,
        bootstrap_samples,
        evidence_tier="synthetic",
        signing_key=signing_key,
        adapter_resolver=lambda assignment, task: _SyntheticAdapter(
            assignment.provider_identity, task
        ),
        timeout_seconds=10,
    )


def _run_live(
    output: Path,
    pack: C2TaskPack,
    assignments: Sequence[PairAssignment],
    config: dict[str, object],
    bootstrap_samples: int,
    adapters,
    timeout_seconds: float,
) -> dict[str, object]:
    from nacl.signing import SigningKey

    by_provider = {adapter.identity.provider_key: adapter for adapter in adapters}
    if len(by_provider) != len(adapters):
        raise ValueError("live adapters must have unique provider identities")
    return _run_experiment(
        output,
        pack,
        assignments,
        config,
        bootstrap_samples,
        evidence_tier="live",
        signing_key=SigningKey.generate(),
        adapter_resolver=lambda assignment, _task: by_provider[
            assignment.provider_identity.provider_key
        ],
        timeout_seconds=timeout_seconds,
    )


def _run_experiment(
    output: Path,
    pack: C2TaskPack,
    assignments: Sequence[PairAssignment],
    config: dict[str, object],
    bootstrap_samples: int,
    *,
    evidence_tier: str,
    signing_key,
    adapter_resolver: AdapterResolver,
    timeout_seconds: float,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    raw_directory = output / "raw"
    raw_directory.mkdir()
    (output / ".verifier_signing_key").write_text(
        signing_key.encode().hex(), encoding="ascii"
    )
    manifest = {
        **config,
        "schema_version": RUN_MANIFEST_SCHEMA,
        "evidence_tier": evidence_tier,
        "verifier_public_key": signing_key.verify_key.encode().hex(),
    }
    _write_json(output / "run_manifest.json", manifest)
    tasks = {task.task_id: task for task in pack.tasks}
    bundles: list[EpisodeEvidenceBundle] = []
    outcomes: list[PairOutcome] = []
    invalid_attempt_count = 0
    retry_count = 0
    event_log = _event_log(output / "flywheel.sqlite")
    try:
        for assignment in assignments:
            task = tasks[assignment.task_id]
            execution = run_pair(
                assignment,
                task,
                adapter_resolver(assignment, task),
                timeout_seconds=timeout_seconds,
                max_retries=1,
            )
            invalid_attempt_count += len(execution.invalid_attempts)
            retry_count += execution.flat.retry_count + execution.governed.retry_count
            if execution.pair is None:
                continue
            flat = _project_and_write_raw(
                execution.flat, task, pack, event_log, signing_key, raw_directory
            )
            governed = _project_and_write_raw(
                execution.governed, task, pack, event_log, signing_key, raw_directory
            )
            bundles.extend((flat, governed))
            outcomes.append(_pair_outcome(execution, task, flat, governed))
    finally:
        event_log.close()
    if not outcomes:
        raise ValueError("experiment produced no complete pairs")
    _write_jsonl(output / "bundles.jsonl", (bundle_to_mapping(item) for item in bundles))
    _write_jsonl(output / "outcomes.jsonl", (outcome_to_mapping(item) for item in outcomes))
    metrics = compute_metrics(
        tuple(outcomes),
        seed=pack.seed,
        bootstrap_samples=bootstrap_samples,
        invalid_attempt_count=invalid_attempt_count,
        retry_count=retry_count,
    )
    summary = _summary(metrics, evidence_tier=evidence_tier, task_pack_hash=pack.pack_hash)
    _write_json(output / "summary.json", summary)
    return replay_run(output)


def _project_and_write_raw(
    arm,
    task: LiveTask,
    pack: C2TaskPack,
    event_log: FlywheelEventLog,
    signing_key,
    raw_directory: Path,
) -> EpisodeEvidenceBundle:
    if arm.output_text is None:
        raise ValueError("cannot project an incomplete arm")
    (raw_directory / f"{arm.attempt.attempt_id}.txt").write_text(
        arm.output_text, encoding="utf-8"
    )
    return project_episode(
        arm,
        task=task,
        task_pack_hash=pack.pack_hash,
        event_log=event_log,
        action_agent_id=ACTION_AGENT_ID,
        verifier_agent_id=VERIFIER_AGENT_ID,
        signing_key=signing_key,
    )


def _pair_outcome(
    execution: PairExecution,
    task: LiveTask,
    flat: EpisodeEvidenceBundle,
    governed: EpisodeEvidenceBundle,
) -> PairOutcome:
    if execution.pair is None:
        raise ValueError("pair outcome requires a complete pair")
    poison_admissions = len(execution.flat.selected_view_ids)
    if task.protected:
        poison_admissions += len(execution.governed.selected_view_ids)
    elif len(execution.governed.selected_view_ids) != 1:
        poison_admissions += 1
    return PairOutcome(
        pair_id=execution.pair.pair_id,
        provider_key=execution.pair.provider_identity.provider_key,
        query_class=task.query_class,
        protected=task.protected,
        flat_success=flat.verdict.outcome == "success",
        governed_success=governed.verdict.outcome == "success",
        flat_latency_ms=execution.flat.attempt.latency_ms,
        governed_latency_ms=execution.governed.attempt.latency_ms,
        flat_input_tokens=execution.flat.attempt.input_tokens,
        flat_output_tokens=execution.flat.attempt.output_tokens,
        governed_input_tokens=execution.governed.attempt.input_tokens,
        governed_output_tokens=execution.governed.attempt.output_tokens,
        flat_cost_usd=execution.flat.attempt.estimated_cost_usd,
        governed_cost_usd=execution.governed.attempt.estimated_cost_usd,
        flat_bundle_hash=flat.bundle_hash,
        governed_bundle_hash=governed.bundle_hash,
        replay_verified=True,
        poison_admissions=poison_admissions,
    )


def _summary(
    metrics: C2Metrics,
    *,
    evidence_tier: str,
    task_pack_hash: str,
) -> dict[str, object]:
    decision = evaluate_c2_policy(metrics)
    reasons = tuple(decision.reasons)
    promote_recommended = decision.promote_recommended
    if evidence_tier != "live":
        reasons = tuple(dict.fromkeys((*reasons, "synthetic_evidence_only")))
        promote_recommended = False
    return {
        "by_provider": {key: asdict(value) for key, value in metrics.by_provider.items()},
        "by_provider_query_class": {
            f"{provider}|{query_class}": asdict(value)
            for (provider, query_class), value in metrics.by_provider_query_class.items()
        },
        "by_query_class": {
            key: asdict(value) for key, value in metrics.by_query_class.items()
        },
        "candidate_state": decision.candidate_state,
        "evidence_tier": evidence_tier,
        "improvement_claim": False,
        "invalid_attempt_count": metrics.invalid_attempt_count,
        "overall": asdict(metrics.overall),
        "pairs_hash": metrics.pairs_hash,
        "promote_recommended": promote_recommended,
        "provider_count": metrics.provider_count,
        "reasons": list(reasons),
        "replay_verified": metrics.overall.replay_failures == 0,
        "retry_count": metrics.retry_count,
        "runtime_recommendation": "flat",
        "task_pack_hash": task_pack_hash,
        "total_pairs": metrics.total_pairs,
    }


def _run_config(
    args,
    pack: C2TaskPack,
    providers: tuple[ProviderIdentity, ...],
    scheduled_pairs: int,
    replicas: int,
) -> dict[str, object]:
    values = {
        "bootstrap_samples": args.bootstrap_samples,
        "mode": args.mode,
        "providers": [provider.provider_key for provider in providers],
        "replicas": replicas,
        "scheduled_pairs": scheduled_pairs,
        "seed": pack.seed,
        "task_pack_hash": pack.pack_hash,
    }
    return {**values, "config_hash": hash_json(values)}


def _pilot_assignments(
    assignments: Sequence[PairAssignment], pack: C2TaskPack
) -> tuple[PairAssignment, ...]:
    query_class_by_task = {task.task_id: task.query_class for task in pack.tasks}
    selected = []
    seen = set()
    for assignment in assignments:
        coordinate = (
            assignment.provider_identity.provider_key,
            query_class_by_task[assignment.task_id],
        )
        if coordinate in seen:
            continue
        seen.add(coordinate)
        selected.append(assignment)
    expected = len({item.provider_identity.provider_key for item in assignments}) * 4
    if len(selected) != expected:
        raise ValueError("pilot schedule must cover every query class per provider")
    return tuple(selected)


def _effective_replicas(args) -> int:
    if args.mode == "formal":
        return 4
    return 1 if args.replicas is None else args.replicas


def _fake_provider_identities(names) -> tuple[ProviderIdentity, ...]:
    selected = FAKE_PROVIDERS if names is None else tuple(names)
    if len(selected) != len(set(selected)):
        raise ValueError("providers must not contain duplicates")
    return tuple(
        provider_from_mapping(
            {
                "provider_id": name,
                "model_id": "synthetic-v1",
                "adapter_kind": "cli",
                "adapter_version": "1.0.0",
            }
        )
        for name in selected
    )


def _event_log(path: Path) -> FlywheelEventLog:
    return FlywheelEventLog(
        path,
        registered_agent_ids=(ACTION_AGENT_ID, VERIFIER_AGENT_ID),
        registered_verifier_ids=(VERIFIER_AGENT_ID,),
    )


def _validate_args(args) -> None:
    if args.replicas is not None and args.replicas <= 0:
        raise ValueError("replicas must be positive")
    if args.limit_pairs is not None and args.limit_pairs <= 0:
        raise ValueError("limit_pairs must be positive")
    if args.bootstrap_samples < 100:
        raise ValueError("bootstrap_samples must be at least 100")
    if args.timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if args.mode == "pilot" and args.replicas not in (None, 1):
        raise ValueError("pilot mode fixes replicas at 1")
    if args.mode == "formal" and args.replicas not in (None, 4):
        raise ValueError("formal mode fixes replicas at 4")
    if args.mode in {"pilot", "formal", "probe"} and args.limit_pairs is not None:
        raise ValueError("--limit-pairs is unavailable for live modes")
    if args.mode in {"pilot", "formal", "probe"} and args.provider is not None:
        if any(provider not in LIVE_PROVIDER_NAMES for provider in args.provider):
            raise ValueError("live modes accept only live providers")
    if args.mode in {"fake", "dry-run"} and args.provider is not None:
        if any(provider not in FAKE_PROVIDERS for provider in args.provider):
            raise ValueError("fake modes accept only fake providers")
    if args.resume and args.mode != "fake":
        raise ValueError("--resume is supported only for fake mode")


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, values) -> None:
    path.write_text(
        "".join(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            + "\n"
            for value in values
        ),
        encoding="utf-8",
    )


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> tuple[dict[str, object], ...]:
    return tuple(json.loads(line) for line in path.read_text(encoding="utf-8").splitlines())


def _print_json(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


__all__ = ["build_parser", "main", "replay_run"]
