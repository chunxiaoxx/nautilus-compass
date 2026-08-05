"""One-command dry-run, synthetic E2E, and replay entry point for Compass C2."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Optional, Sequence

from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_json
from gep.flywheel_log import FlywheelEventLog

from .checkpoints import CheckpointStore
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
from .schema import (
    LiveTask,
    ProviderIdentity,
    provider_from_mapping,
    provider_to_mapping,
)
from .task_pack import C2TaskPack, read_task_pack
from .verifier import response_hash, verify_output


ACTION_AGENT_ID = 4101
VERIFIER_AGENT_ID = 4201
RUN_MANIFEST_SCHEMA = "compass.live_agent_c2.run_manifest.v3"
PROVIDER_PROTOCOL_VERSION = "compass.live_agent_c2.provider.v2"
RUN_RECEIPT_SCHEMA = "compass.live_agent_c2.run_receipt.v1"
RUN_CONFIG_FIELDS = (
    "bootstrap_samples",
    "mode",
    "provider_protocol_version",
    "providers",
    "replicas",
    "scheduled_pairs",
    "seed",
    "task_pack_hash",
)
RUN_MANIFEST_FIELDS = frozenset(
    (*RUN_CONFIG_FIELDS, "config_hash", "evidence_tier", "schema_version", "verifier_public_key")
)
RUN_RECEIPT_FIELDS = frozenset(
    {
        "bundle_set_hash",
        "invalid_attempt_count",
        "manifest_hash",
        "pairs_hash",
        "retry_count",
        "schema_version",
        "signature",
        "summary_hash",
        "verifier_public_key",
    }
)
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
    resume_existing = False
    if args.output.exists() and any(args.output.iterdir()):
        if not args.resume:
            raise ValueError("output directory must be absent or empty unless --resume is used")
        manifest = _validate_run_manifest(_read_json(args.output / "run_manifest.json"))
        if manifest.get("config_hash") != config["config_hash"]:
            raise ValueError("run manifest does not match resume configuration")
        if args.mode == "fake":
            report = replay_run(args.output)
            _print_json(report)
            return 0
        if not (args.output / ".verifier_signing_key").exists():
            report = replay_run(args.output)
            _print_json(report)
            return 0
        resume_existing = True
    elif args.resume:
        raise ValueError("resume requires an existing non-empty run directory")
    if args.mode in {"pilot", "formal"}:
        report = _run_live(
            args.output,
            pack,
            assignments,
            config,
            args.bootstrap_samples,
            adapters,
            args.timeout_seconds,
            resume=resume_existing,
        )
    else:
        report = _run_synthetic(
            args.output, pack, assignments, config, args.bootstrap_samples
        )
    _print_json(report)
    return 0


def replay_run(output: Path) -> dict[str, object]:
    root = Path(output)
    manifest = _validate_run_manifest(_read_json(root / "run_manifest.json"))
    pack = read_task_pack()
    if manifest.get("task_pack_hash") != pack.pack_hash:
        raise ValueError("run manifest task pack mismatch")
    bundles = tuple(
        bundle_from_mapping(item) for item in _read_jsonl(root / "bundles.jsonl")
    )
    outcomes = tuple(
        outcome_from_mapping(item) for item in _read_jsonl(root / "outcomes.jsonl")
    )
    manifest_providers = {
        provider.provider_key: provider
        for provider in (
            provider_from_mapping(item) for item in manifest["providers"]
        )
    }
    tasks_by_hash = {task.task_hash: task for task in pack.tasks}
    event_log = _event_log(root / "flywheel.sqlite")
    try:
        for bundle in bundles:
            _verify_manifest_provider_binding(bundle, manifest_providers)
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
    _verify_outcome_evidence_binding(outcomes, bundles, tasks_by_hash)
    receipt = _validate_run_receipt(
        _read_json(root / "run_receipt.json"),
        manifest=manifest,
        bundles=bundles,
    )
    stored_summary = _read_json(root / "summary.json")
    metrics = compute_metrics(
        outcomes,
        seed=int(manifest["seed"]),
        bootstrap_samples=int(manifest["bootstrap_samples"]),
        invalid_attempt_count=receipt["invalid_attempt_count"],
        retry_count=receipt["retry_count"],
    )
    if metrics.pairs_hash != receipt["pairs_hash"]:
        raise ValueError("outcome replay hash mismatch")
    expected_summary = _summary(
        metrics,
        evidence_tier=manifest["evidence_tier"],
        task_pack_hash=pack.pack_hash,
    )
    if stored_summary != expected_summary:
        raise ValueError("run summary replay mismatch")
    if receipt["summary_hash"] != _summary_hash(expected_summary):
        raise ValueError("run summary replay mismatch")
    return expected_summary


def _verify_manifest_provider_binding(
    bundle: EpisodeEvidenceBundle,
    manifest_providers: dict[str, ProviderIdentity],
) -> None:
    tool_chain = bundle.packet.tool_chain
    if len(tool_chain) != 1 or not tool_chain[0].startswith("provider:"):
        raise ValueError("run manifest provider binding mismatch")
    provider = manifest_providers.get(tool_chain[0].removeprefix("provider:"))
    if provider is None:
        raise ValueError("run manifest provider binding mismatch")
    if bundle.attempt.provider_identity != provider:
        raise ValueError("run manifest provider binding mismatch")
    expected_environment = hash_json(
        {
            "domain": "compass.live_agent_c2.provider_environment.v1",
            "provider": provider_to_mapping(provider),
        }
    )
    if bundle.verdict.environment_fingerprint_hash != expected_environment:
        raise ValueError("run manifest provider binding mismatch")


def _verify_outcome_evidence_binding(
    outcomes: tuple[PairOutcome, ...],
    bundles: tuple[EpisodeEvidenceBundle, ...],
    tasks_by_hash: dict[str, LiveTask],
) -> None:
    bundles_by_pair: dict[str, list[EpisodeEvidenceBundle]] = {}
    for bundle in bundles:
        bundles_by_pair.setdefault(bundle.attempt.pair_id, []).append(bundle)
    if len({outcome.pair_id for outcome in outcomes}) != len(outcomes):
        raise ValueError("outcome evidence binding mismatch")
    if set(bundles_by_pair) != {outcome.pair_id for outcome in outcomes}:
        raise ValueError("outcome evidence binding mismatch")
    for outcome in outcomes:
        pair_bundles = bundles_by_pair[outcome.pair_id]
        if len(pair_bundles) != 2:
            raise ValueError("outcome evidence binding mismatch")
        by_arm = {bundle.attempt.arm: bundle for bundle in pair_bundles}
        if set(by_arm) != {"flat", "governed"}:
            raise ValueError("outcome evidence binding mismatch")
        flat = by_arm["flat"]
        governed = by_arm["governed"]
        if flat.attempt.order_index == governed.attempt.order_index:
            raise ValueError("outcome evidence binding mismatch")
        if flat.attempt.provider_identity != governed.attempt.provider_identity:
            raise ValueError("outcome evidence binding mismatch")
        if flat.task_hash != governed.task_hash:
            raise ValueError("outcome evidence binding mismatch")
        task = tasks_by_hash.get(flat.task_hash)
        if task is None or any(
            bundle.attempt.task_id != task.task_id
            or bundle.packet.task != f"{task.task_id}@{task.task_hash}"
            for bundle in pair_bundles
        ):
            raise ValueError("outcome evidence binding mismatch")
        expected = _outcome_from_verified_bundles(task, flat, governed)
        if outcome_to_mapping(outcome) != outcome_to_mapping(expected):
            raise ValueError("outcome evidence binding mismatch")


def _outcome_from_verified_bundles(
    task: LiveTask,
    flat: EpisodeEvidenceBundle,
    governed: EpisodeEvidenceBundle,
) -> PairOutcome:
    poison_admissions = len(flat.selected_view_ids)
    if task.protected:
        poison_admissions += len(governed.selected_view_ids)
    elif len(governed.selected_view_ids) != 1:
        poison_admissions += 1
    return PairOutcome(
        pair_id=flat.attempt.pair_id,
        provider_key=flat.attempt.provider_identity.provider_key,
        query_class=task.query_class,
        protected=task.protected,
        flat_success=flat.verdict.outcome == "success",
        governed_success=governed.verdict.outcome == "success",
        flat_latency_ms=flat.attempt.latency_ms,
        governed_latency_ms=governed.attempt.latency_ms,
        flat_input_tokens=flat.attempt.input_tokens,
        flat_output_tokens=flat.attempt.output_tokens,
        governed_input_tokens=governed.attempt.input_tokens,
        governed_output_tokens=governed.attempt.output_tokens,
        flat_cost_usd=flat.attempt.estimated_cost_usd,
        governed_cost_usd=governed.attempt.estimated_cost_usd,
        flat_bundle_hash=flat.bundle_hash,
        governed_bundle_hash=governed.bundle_hash,
        replay_verified=True,
        poison_admissions=poison_admissions,
    )


def _validate_run_manifest(raw: object) -> dict[str, object]:
    if not isinstance(raw, dict) or set(raw) != RUN_MANIFEST_FIELDS:
        raise ValueError("run manifest fields are invalid")
    if raw["schema_version"] != RUN_MANIFEST_SCHEMA:
        raise ValueError("run manifest schema is unsupported")
    if raw["provider_protocol_version"] != PROVIDER_PROTOCOL_VERSION:
        raise ValueError("run manifest provider protocol is unsupported")
    providers_raw = raw["providers"]
    if not isinstance(providers_raw, list) or len(providers_raw) < 2:
        raise ValueError("run manifest providers are invalid")
    try:
        providers = tuple(provider_from_mapping(item) for item in providers_raw)
    except (TypeError, ValueError) as error:
        raise ValueError("run manifest providers are invalid") from error
    if [provider_to_mapping(provider) for provider in providers] != providers_raw:
        raise ValueError("run manifest providers are not canonical")
    if len({provider.provider_key for provider in providers}) != len(providers):
        raise ValueError("run manifest providers must be unique")
    mode = raw["mode"]
    if mode not in {"fake", "pilot", "formal"}:
        raise ValueError("run manifest mode is invalid")
    expected_tier = "live" if mode in {"pilot", "formal"} else "synthetic"
    if raw["evidence_tier"] != expected_tier:
        raise ValueError("run manifest evidence tier is invalid")
    for field, minimum in (
        ("bootstrap_samples", 100),
        ("replicas", 1),
        ("scheduled_pairs", 1),
    ):
        value = raw[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"run manifest {field} is invalid")
    if isinstance(raw["seed"], bool) or not isinstance(raw["seed"], int):
        raise ValueError("run manifest seed is invalid")
    verifier_key = raw["verifier_public_key"]
    try:
        verifier_key_bytes = bytes.fromhex(verifier_key) if isinstance(verifier_key, str) else b""
    except ValueError as error:
        raise ValueError("run manifest verifier key is invalid") from error
    if len(verifier_key_bytes) != 32:
        raise ValueError("run manifest verifier key is invalid")
    config = {field: raw[field] for field in RUN_CONFIG_FIELDS}
    if raw["config_hash"] != hash_json(config):
        raise ValueError("run manifest config hash mismatch")
    return dict(raw)


def _validate_run_receipt(
    raw: object,
    *,
    manifest: dict[str, object],
    bundles: tuple[EpisodeEvidenceBundle, ...],
) -> dict[str, object]:
    if not isinstance(raw, dict) or set(raw) != RUN_RECEIPT_FIELDS:
        raise ValueError("run receipt fields are invalid")
    if raw["schema_version"] != RUN_RECEIPT_SCHEMA:
        raise ValueError("run receipt schema is unsupported")
    for field in (
        "bundle_set_hash",
        "manifest_hash",
        "pairs_hash",
        "summary_hash",
    ):
        if not _is_sha256(raw[field]):
            raise ValueError(f"run receipt {field} is invalid")
    for field in ("invalid_attempt_count", "retry_count"):
        value = raw[field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"run receipt {field} is invalid")
    if raw["verifier_public_key"] != manifest["verifier_public_key"]:
        raise ValueError("run receipt verifier key mismatch")
    signature = raw["signature"]
    if (
        not isinstance(signature, str)
        or len(signature) != 128
        or any(character not in "0123456789abcdef" for character in signature)
    ):
        raise ValueError("run receipt signature is invalid")
    try:
        from nacl.exceptions import BadSignatureError
        from nacl.signing import VerifyKey

        VerifyKey(bytes.fromhex(raw["verifier_public_key"])).verify(
            _run_receipt_signature_payload(_receipt_unsigned(raw)),
            bytes.fromhex(signature),
        )
    except (BadSignatureError, ValueError) as error:
        raise ValueError("run receipt signature verification failed") from error
    if raw["manifest_hash"] != _manifest_hash(manifest):
        raise ValueError("run receipt manifest binding mismatch")
    if raw["bundle_set_hash"] != _bundle_set_hash(bundles):
        raise ValueError("run receipt bundle binding mismatch")
    return dict(raw)


def _write_run_receipt(
    output: Path,
    *,
    manifest: dict[str, object],
    bundles: tuple[EpisodeEvidenceBundle, ...],
    metrics: C2Metrics,
    summary: dict[str, object],
    signing_key,
) -> None:
    unsigned = {
        "bundle_set_hash": _bundle_set_hash(bundles),
        "invalid_attempt_count": metrics.invalid_attempt_count,
        "manifest_hash": _manifest_hash(manifest),
        "pairs_hash": metrics.pairs_hash,
        "retry_count": metrics.retry_count,
        "schema_version": RUN_RECEIPT_SCHEMA,
        "summary_hash": _summary_hash(summary),
        "verifier_public_key": signing_key.verify_key.encode().hex(),
    }
    signature = signing_key.sign(_run_receipt_signature_payload(unsigned)).signature.hex()
    _write_json(output / "run_receipt.json", {**unsigned, "signature": signature})


def _receipt_unsigned(receipt: dict[str, object]) -> dict[str, object]:
    return {field: receipt[field] for field in RUN_RECEIPT_FIELDS if field != "signature"}


def _run_receipt_signature_payload(unsigned: dict[str, object]) -> bytes:
    return canonical_json_bytes(
        {
            "domain": "compass.live_agent_c2.run_receipt_signature.v1",
            "receipt": unsigned,
        }
    )


def _manifest_hash(manifest: dict[str, object]) -> str:
    return hash_json(
        {"domain": "compass.live_agent_c2.manifest_binding.v1", "manifest": manifest}
    )


def _bundle_set_hash(bundles: tuple[EpisodeEvidenceBundle, ...]) -> str:
    return hash_json(
        {
            "bundle_hashes": sorted(bundle.bundle_hash for bundle in bundles),
            "domain": "compass.live_agent_c2.bundle_set.v1",
        }
    )


def _summary_hash(summary: dict[str, object]) -> str:
    return hash_json(
        {"domain": "compass.live_agent_c2.summary.v1", "summary": summary}
    )


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 71
        and value.startswith("sha256:")
        and all(character in "0123456789abcdef" for character in value[7:])
    )


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
    *,
    resume: bool,
) -> dict[str, object]:
    from nacl.signing import SigningKey

    by_provider = {adapter.identity.provider_key: adapter for adapter in adapters}
    if len(by_provider) != len(adapters):
        raise ValueError("live adapters must have unique provider identities")
    if resume:
        manifest = _validate_run_manifest(_read_json(output / "run_manifest.json"))
        try:
            signing_key = SigningKey(
                bytes.fromhex((output / ".verifier_signing_key").read_text("ascii"))
            )
        except (OSError, ValueError) as error:
            raise ValueError("resume verifier signing key is invalid") from error
        if signing_key.verify_key.encode().hex() != manifest["verifier_public_key"]:
            raise ValueError("resume verifier signing key mismatch")
    else:
        signing_key = SigningKey.generate()
    return _run_experiment(
        output,
        pack,
        assignments,
        config,
        bootstrap_samples,
        evidence_tier="live",
        signing_key=signing_key,
        adapter_resolver=lambda assignment, _task: by_provider[
            assignment.provider_identity.provider_key
        ],
        timeout_seconds=timeout_seconds,
        resume=resume,
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
    resume: bool = False,
) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    raw_directory = output / "raw"
    raw_directory.mkdir(exist_ok=resume)
    pair_log_directory = output / ".pair_event_logs"
    pair_log_directory.mkdir(exist_ok=resume)
    if not resume:
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
    store = CheckpointStore(output)
    store.initialize()
    if resume:
        store.prepare_resume()
    tasks = {task.task_id: task for task in pack.tasks}
    terminal = set(store.terminal_pair_ids())
    for assignment in assignments:
        if assignment.pair_id in terminal:
            continue
        task = tasks[assignment.task_id]
        store.mark_started(assignment.pair_id)
        execution = run_pair(
            assignment,
            task,
            adapter_resolver(assignment, task),
            timeout_seconds=timeout_seconds,
            max_retries=1,
        )
        invalid_count = len(execution.invalid_attempts)
        retries = execution.flat.retry_count + execution.governed.retry_count
        failure_codes = tuple(
            attempt.error_code
            for attempt in execution.invalid_attempts
            if attempt.error_code is not None
        )
        if execution.pair is None:
            store.write_checkpoint(
                pair_id=assignment.pair_id,
                status="incomplete",
                bundles=(),
                outcome=None,
                invalid_attempt_count=invalid_count,
                retry_count=retries,
                failure_codes=failure_codes,
            )
            terminal.add(assignment.pair_id)
            continue
        pair_log = _event_log(pair_log_directory / f"{assignment.pair_id}.sqlite")
        try:
            flat = _project_and_write_raw(
                execution.flat, task, pack, pair_log, signing_key, raw_directory
            )
            governed = _project_and_write_raw(
                execution.governed, task, pack, pair_log, signing_key, raw_directory
            )
        finally:
            pair_log.close()
        outcome = _pair_outcome(execution, task, flat, governed)
        store.write_checkpoint(
            pair_id=assignment.pair_id,
            status="complete",
            bundles=(bundle_to_mapping(flat), bundle_to_mapping(governed)),
            outcome=outcome_to_mapping(outcome),
            invalid_attempt_count=invalid_count,
            retry_count=retries,
            failure_codes=failure_codes,
        )
        terminal.add(assignment.pair_id)
    return _finalize_run(
        output,
        pack,
        store,
        evidence_tier=evidence_tier,
        bootstrap_samples=bootstrap_samples,
        signing_key=signing_key,
    )


def _finalize_run(
    output: Path,
    pack: C2TaskPack,
    store: CheckpointStore,
    *,
    evidence_tier: str,
    bootstrap_samples: int,
    signing_key,
) -> dict[str, object]:
    checkpoints = store.checkpoints()
    bundle_rows = tuple(
        bundle
        for checkpoint in checkpoints
        if checkpoint["status"] == "complete"
        for bundle in checkpoint["bundles"]
    )
    outcome_rows = tuple(
        checkpoint["outcome"]
        for checkpoint in checkpoints
        if checkpoint["status"] == "complete"
    )
    bundles = tuple(bundle_from_mapping(item) for item in bundle_rows)
    outcomes = tuple(outcome_from_mapping(item) for item in outcome_rows)
    if not outcomes:
        raise ValueError("experiment produced no complete pairs")
    if len(bundles) != 2 * len(outcomes):
        raise ValueError("complete checkpoints must contain exactly two bundles per pair")
    _rebuild_event_log(output, bundles)
    _write_jsonl(output / "bundles.jsonl", bundle_rows)
    _write_jsonl(output / "outcomes.jsonl", outcome_rows)
    invalid_attempt_count = sum(item["invalid_attempt_count"] for item in checkpoints)
    retry_count = sum(item["retry_count"] for item in checkpoints)
    metrics = compute_metrics(
        outcomes,
        seed=pack.seed,
        bootstrap_samples=bootstrap_samples,
        invalid_attempt_count=invalid_attempt_count,
        retry_count=retry_count,
    )
    summary = _summary(metrics, evidence_tier=evidence_tier, task_pack_hash=pack.pack_hash)
    _write_json(output / "summary.json", summary)
    manifest = _validate_run_manifest(_read_json(output / "run_manifest.json"))
    _write_run_receipt(
        output,
        manifest=manifest,
        bundles=bundles,
        metrics=metrics,
        summary=summary,
        signing_key=signing_key,
    )
    report = replay_run(output)
    signing_key_path = output / ".verifier_signing_key"
    if signing_key_path.exists():
        signing_key_path.unlink()
    return report


def _rebuild_event_log(
    output: Path, bundles: Sequence[EpisodeEvidenceBundle]
) -> None:
    temporary = output / ".flywheel.sqlite.tmp"
    if temporary.exists():
        temporary.unlink()
    event_log = _event_log(temporary)
    try:
        for bundle in bundles:
            for event in (bundle.episode_event, bundle.verdict_event):
                receipt = event_log.append(event.to_mapping())
                if receipt.status != "accepted" or receipt.event_hash != event.event_hash:
                    raise ValueError("checkpoint event admission failed")
            verify_episode_bundle(bundle, event_log=event_log)
    finally:
        event_log.close()
    temporary.replace(output / "flywheel.sqlite")


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
        "provider_protocol_version": PROVIDER_PROTOCOL_VERSION,
        "providers": [provider_to_mapping(provider) for provider in providers],
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
        return 5
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
    if args.mode == "formal" and args.replicas not in (None, 5):
        raise ValueError("formal mode fixes replicas at 5")
    if args.mode in {"pilot", "formal", "probe"} and args.limit_pairs is not None:
        raise ValueError("--limit-pairs is unavailable for live modes")
    if args.mode in {"pilot", "formal", "probe"} and args.provider is not None:
        if any(provider not in LIVE_PROVIDER_NAMES for provider in args.provider):
            raise ValueError("live modes accept only live providers")
    if args.mode in {"fake", "dry-run"} and args.provider is not None:
        if any(provider not in FAKE_PROVIDERS for provider in args.provider):
            raise ValueError("fake modes accept only fake providers")
    if args.resume and args.mode not in {"fake", "pilot", "formal"}:
        raise ValueError("--resume is supported only for experiment modes")


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
