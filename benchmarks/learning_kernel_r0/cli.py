"""One-command, provider-free CLI for the frozen Learning Kernel R0 fixture."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any

from benchmarks.poi_gate2.action_metrics import percentile_95
from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_bytes, hash_json
from gep.experience_packet import ExperiencePacket, from_args as experience_from_args
from gep.verdict_packet import VerdictPacket, from_args as verdict_from_args

from .interventions import build_memory_views
from .metrics import aggregate_metrics
from .policy import evaluate_candidate_policy
from .runner import (
    EvaluationTask,
    ExecutionObservation,
    VerificationObservation,
    read_result_journal,
    result_to_mapping,
    run_mechanism_matrix,
    write_result_journal,
)
from .schema import INTERVENTIONS, SELECTORS, LearningRunResult, MemoryView
from .utility import UtilityKey


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
_OUTPUT_PATTERN = re.compile(r"[A-Z][A-Z0-9_]{0,63}")
_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "fixture_id",
        "file_hashes",
        "selectors",
        "interventions",
        "query_classes",
        "protected_query_classes",
        "replicas",
        "selection_limit",
        "now_iso",
        "runtime_recommendation",
        "improvement_claim",
    }
)


@dataclass(frozen=True, slots=True)
class FixtureBundle:
    schema_version: str
    fixture_id: str
    fixture_dir: Path
    manifest_hash: str
    file_hashes: Mapping[str, str]
    selectors: tuple[str, ...]
    interventions: tuple[str, ...]
    query_classes: tuple[str, ...]
    protected_query_classes: frozenset[str]
    replicas: int
    selection_limit: int
    now_iso: str
    runtime_recommendation: str
    improvement_claim: bool
    tasks: tuple[EvaluationTask, ...]
    packets: tuple[ExperiencePacket, ...]
    packet_hashes: Mapping[str, str]
    source_query_classes: Mapping[str, str]
    semantic_scores: Mapping[str, float]
    independent_verdicts: Mapping[str, VerdictPacket | None]
    utility_scores: Mapping[UtilityKey, float]
    poi_scores: Mapping[str, tuple[float, float]]
    execute: Callable[[Any], ExecutionObservation]
    verify: Callable[[EvaluationTask, str, ExecutionObservation], VerificationObservation]

    def views_for(
        self,
        task: EvaluationTask,
        query_class: str,
        intervention: str,
    ) -> tuple[MemoryView, ...]:
        if task not in self.tasks:
            raise ValueError("task is not part of this fixture")
        return build_memory_views(
            self.packets,
            intervention=intervention,
            query_class=query_class,
            now_iso=self.now_iso,
            packet_hashes=self.packet_hashes,
            source_query_classes=self.source_query_classes,
            semantic_scores=self.semantic_scores,
            independent_verdicts=self.independent_verdicts,
        )


def load_fixture(fixture_dir: Path) -> FixtureBundle:
    root = Path(fixture_dir).resolve()
    manifest_path = root / "manifest.json"
    manifest_raw, manifest_bytes = _read_canonical_json(manifest_path)
    manifest = _exact_mapping("manifest", manifest_raw, _MANIFEST_FIELDS)
    if manifest["schema_version"] != "compass.learning_kernel.fixture.v1":
        raise ValueError("fixture schema_version is unsupported")
    _validate_token("fixture_id", manifest["fixture_id"])
    file_hashes = _file_hashes(manifest["file_hashes"])
    for name, expected_hash in file_hashes.items():
        actual_hash = hash_bytes((root / name).read_bytes())
        if actual_hash != expected_hash:
            raise ValueError(f"{name} hash mismatch")

    selectors = _axis("selectors", manifest["selectors"], SELECTORS)
    interventions = _axis("interventions", manifest["interventions"], INTERVENTIONS)
    query_classes = _token_axis("query_classes", manifest["query_classes"])
    protected = frozenset(
        _token_axis("protected_query_classes", manifest["protected_query_classes"])
    )
    if not protected.issubset(query_classes):
        raise ValueError("protected_query_classes must be query classes")
    replicas = _positive_int("replicas", manifest["replicas"])
    selection_limit = _positive_int("selection_limit", manifest["selection_limit"])
    if not isinstance(manifest["now_iso"], str) or not manifest["now_iso"].endswith("Z"):
        raise ValueError("now_iso must be an explicit UTC timestamp")
    if manifest["runtime_recommendation"] != "flat":
        raise ValueError("runtime_recommendation must be flat")
    if manifest["improvement_claim"] is not False:
        raise ValueError("improvement_claim must be false")

    tasks = _load_tasks(root / "tasks.json")
    (
        packets,
        packet_hashes,
        source_query_classes,
        semantic_scores,
        independent_verdicts,
    ) = _load_experiences(root / "experiences.json")
    execute, verify = _load_verifier(root / "verifier.json")
    utility_scores, poi_scores = _selector_evidence(
        packets=packets,
        query_classes=query_classes,
        interventions=interventions,
        now_iso=manifest["now_iso"],
        packet_hashes=packet_hashes,
        source_query_classes=source_query_classes,
        semantic_scores=semantic_scores,
        independent_verdicts=independent_verdicts,
    )
    return FixtureBundle(
        schema_version=manifest["schema_version"],
        fixture_id=manifest["fixture_id"],
        fixture_dir=root,
        manifest_hash=hash_bytes(manifest_bytes),
        file_hashes=MappingProxyType(file_hashes),
        selectors=selectors,
        interventions=interventions,
        query_classes=query_classes,
        protected_query_classes=protected,
        replicas=replicas,
        selection_limit=selection_limit,
        now_iso=manifest["now_iso"],
        runtime_recommendation="flat",
        improvement_claim=False,
        tasks=tasks,
        packets=packets,
        packet_hashes=MappingProxyType(packet_hashes),
        source_query_classes=MappingProxyType(source_query_classes),
        semantic_scores=MappingProxyType(semantic_scores),
        independent_verdicts=MappingProxyType(independent_verdicts),
        utility_scores=MappingProxyType(utility_scores),
        poi_scores=MappingProxyType(poi_scores),
        execute=execute,
        verify=verify,
    )


def run_fixture(bundle: FixtureBundle) -> tuple[LearningRunResult, ...]:
    return run_mechanism_matrix(
        tasks=bundle.tasks,
        query_classes=bundle.query_classes,
        selectors=bundle.selectors,
        interventions=bundle.interventions,
        replicas=bundle.replicas,
        view_provider=bundle.views_for,
        executor=bundle.execute,
        verifier=bundle.verify,
        utility_scores=bundle.utility_scores,
        poi_scores=bundle.poi_scores,
        protected_query_classes=bundle.protected_query_classes,
        selection_limit=bundle.selection_limit,
    )


def summarize_results(
    bundle: FixtureBundle,
    results: tuple[LearningRunResult, ...],
    *,
    actual_journal_hash: str | None = None,
) -> dict[str, Any]:
    expected = run_fixture(bundle)
    if expected != results:
        raise ValueError("result journal does not reproduce the frozen matrix")
    metrics = aggregate_metrics(results)
    baseline = _result_slice(results, "flat", "no_memory")
    candidate = _result_slice(results, "governed", "distilled")
    shuffled = _result_slice(results, "governed", "shuffled")
    candidate_delta = _matched_delta(baseline, candidate)
    permutation_deltas = tuple(
        _matched_delta(
            tuple(row for row in baseline if row.replica == replica),
            tuple(row for row in shuffled if row.replica == replica),
        )
        for replica in range(bundle.replicas)
    )
    permutation_p95 = percentile_95(permutation_deltas)
    protected_deltas = {
        query_class: _matched_delta(
            tuple(row for row in baseline if row.query_class == query_class),
            tuple(row for row in candidate if row.query_class == query_class),
        )
        for query_class in sorted(bundle.protected_query_classes)
    }
    blocked_poison_ids = _blocked_poison_view_ids(bundle)
    admitted_poisoned = tuple(
        sorted(
            {
                view_id
                for row in _result_slice(results, "governed", "poisoned")
                for view_id in row.selected_view_ids
                if view_id in blocked_poison_ids
            }
        )
    )
    expected_payload = b"".join(
        canonical_json_bytes(result_to_mapping(row)) + b"\n" for row in expected
    )
    actual_payload = b"".join(
        canonical_json_bytes(result_to_mapping(row)) + b"\n" for row in results
    )
    expected_replay_hash = hash_bytes(expected_payload)
    actual_replay_hash = actual_journal_hash or hash_bytes(actual_payload)
    _validate_hash("actual_journal_hash", actual_replay_hash)
    decision = evaluate_candidate_policy(
        aggregate_delta=candidate_delta,
        permutation_p95=permutation_p95,
        candidate_selector="governed",
        protected_deltas=protected_deltas,
        protected_query_classes=tuple(sorted(bundle.protected_query_classes)),
        required_query_classes=bundle.query_classes,
        observed_query_classes=tuple(sorted({row.query_class for row in results})),
        admitted_poisoned_view_ids=admitted_poisoned,
        expected_replay_hash=expected_replay_hash,
        actual_replay_hash=actual_replay_hash,
    )
    preimage = {
        "schema_version": "compass.learning_kernel.summary.v1",
        "fixture_id": bundle.fixture_id,
        "fixture_manifest_hash": bundle.manifest_hash,
        "expected_journal_hash": expected_replay_hash,
        "journal_hash": actual_replay_hash,
        "matrix_runs": len(results),
        "selectors": list(bundle.selectors),
        "interventions": list(bundle.interventions),
        "causal": {
            "candidate_delta": candidate_delta,
            "permutation_deltas": list(permutation_deltas),
            "permutation_p95": permutation_p95,
        },
        "safety": {
            "protected_deltas": protected_deltas,
            "admitted_poisoned_view_ids": list(admitted_poisoned),
        },
        "forgetting": {
            "regret": metrics.forgetting_regret,
            "recovery_rate": metrics.recovery_rate,
        },
        "efficiency": {
            "latency_p50_ms": metrics.latency_p50_ms,
            "latency_p95_ms": metrics.latency_p95_ms,
            "total_input_tokens": metrics.total_input_tokens,
            "total_output_tokens": metrics.total_output_tokens,
            "total_estimated_cost_usd": metrics.total_estimated_cost_usd,
        },
        "decision": asdict(decision),
        "runtime_recommendation": "flat",
        "improvement_claim": False,
    }
    return {**preimage, "summary_hash": hash_json(preimage)}


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    bundle = load_fixture(Path(args.fixture_dir))
    if args.command == "dry-run":
        report = {
            "schema_version": "compass.learning_kernel.dry_run.v1",
            "fixture_id": bundle.fixture_id,
            "fixture_manifest_hash": bundle.manifest_hash,
            "matrix_runs": (
                len(bundle.tasks)
                * len(bundle.query_classes)
                * len(bundle.selectors)
                * len(bundle.interventions)
                * bundle.replicas
            ),
            "runtime_recommendation": "flat",
            "improvement_claim": False,
        }
        _print_json(report)
        return 0
    if args.command == "run":
        results = run_fixture(bundle)
        path = write_result_journal(Path(args.out), results)
        _print_json(
            {
                "schema_version": "compass.learning_kernel.run_receipt.v1",
                "fixture_manifest_hash": bundle.manifest_hash,
                "journal_hash": hash_bytes(path.read_bytes()),
                "matrix_runs": len(results),
                "runtime_recommendation": "flat",
                "improvement_claim": False,
            }
        )
        return 0

    results = read_result_journal(Path(args.runs))
    journal_path = Path(args.runs) / "results.jsonl"
    summary = summarize_results(
        bundle,
        results,
        actual_journal_hash=hash_bytes(journal_path.read_bytes()),
    )
    if args.write_summary is not None:
        _write_canonical(Path(args.write_summary), summary)
    _print_json(summary)
    return 0


def _load_tasks(path: Path) -> tuple[EvaluationTask, ...]:
    raw, _ = _read_canonical_json(path)
    values = _exact_mapping("tasks file", raw, frozenset({"schema_version", "tasks"}))
    if values["schema_version"] != "compass.learning_kernel.tasks.v1":
        raise ValueError("tasks schema_version is unsupported")
    rows = _sequence("tasks", values["tasks"])
    tasks = []
    for raw_task in rows:
        task = _exact_mapping(
            "task",
            raw_task,
            frozenset({"task_id", "task_hash", "route_key", "action_kind"}),
        )
        expected_hash = hash_json(
            {
                "task_id": task["task_id"],
                "route_key": task["route_key"],
                "action_kind": task["action_kind"],
            }
        )
        if task["task_hash"] != expected_hash:
            raise ValueError("task_hash does not match canonical task content")
        tasks.append(EvaluationTask(**task))
    result = tuple(tasks)
    if not result or len({task.task_id for task in result}) != len(result):
        raise ValueError("tasks must contain unique task_id values")
    return result


def _load_experiences(path: Path):
    raw, _ = _read_canonical_json(path)
    values = _exact_mapping(
        "experiences file",
        raw,
        frozenset({"schema_version", "experiences"}),
    )
    if values["schema_version"] != "compass.learning_kernel.experiences.v1":
        raise ValueError("experiences schema_version is unsupported")
    packets = []
    packet_hashes = {}
    source_query_classes = {}
    semantic_scores = {}
    verdicts = {}
    for raw_row in _sequence("experiences", values["experiences"]):
        row = _exact_mapping(
            "experience",
            raw_row,
            frozenset(
                {
                    "packet",
                    "packet_hash",
                    "source_query_class",
                    "semantic_score",
                    "independent_verdict",
                }
            ),
        )
        packet = experience_from_args(row["packet"])
        if packet.episode_id is None:
            raise ValueError("experience packet requires episode_id")
        packet_hash = hash_json(row["packet"])
        if row["packet_hash"] != packet_hash:
            raise ValueError("packet_hash does not match canonical packet content")
        verdict = None if row["independent_verdict"] is None else verdict_from_args(
            row["independent_verdict"]
        )
        if verdict is not None and (
            verdict.episode_id != packet.episode_id
            or verdict.episode_event_hash != packet_hash
        ):
            raise ValueError("independent verdict does not bind to its packet")
        query_class = row["source_query_class"]
        _validate_token("source_query_class", query_class)
        semantic_score = _finite_number("semantic_score", row["semantic_score"])
        packets.append(packet)
        packet_hashes[packet.episode_id] = packet_hash
        source_query_classes[packet.episode_id] = query_class
        semantic_scores[packet.episode_id] = semantic_score
        verdicts[packet.episode_id] = verdict
    if not packets or len(packet_hashes) != len(packets):
        raise ValueError("experiences must contain unique episode_id values")
    return (
        tuple(packets),
        packet_hashes,
        source_query_classes,
        semantic_scores,
        verdicts,
    )


def _selector_evidence(**kwargs):
    utility_scores: dict[UtilityKey, float] = {}
    poi_scores = {}
    query_classes = kwargs.pop("query_classes")
    interventions = kwargs.pop("interventions")
    for query_class in query_classes:
        for intervention in interventions:
            views = build_memory_views(
                kwargs["packets"],
                intervention=intervention,
                query_class=query_class,
                now_iso=kwargs["now_iso"],
                packet_hashes=kwargs["packet_hashes"],
                source_query_classes=kwargs["source_query_classes"],
                semantic_scores=kwargs["semantic_scores"],
                independent_verdicts=kwargs["independent_verdicts"],
            )
            for view in views:
                if view.verification_state == "independent_verified":
                    utility_scores[
                        (view.route_key, view.query_class, view.action_kind, view.view_id)
                    ] = 1.0 if view.verdict == "success" else -1.0
                poi_scores[view.view_id] = (
                    view.semantic_score,
                    1.0 if view.verdict == "success" else 0.0,
                )
    return utility_scores, poi_scores


def _load_verifier(path: Path):
    raw, _ = _read_canonical_json(path)
    values = _exact_mapping(
        "verifier",
        raw,
        frozenset({"schema_version", "cost_model", "protected_rule", "task_rules"}),
    )
    if values["schema_version"] != "compass.learning_kernel.verifier.v1":
        raise ValueError("verifier schema_version is unsupported")
    cost = _exact_mapping(
        "cost_model",
        values["cost_model"],
        frozenset({"base_input_tokens", "base_latency_ms", "output_tokens"}),
    )
    for name, value in cost.items():
        _positive_int(name, value)
    protected = _exact_mapping(
        "protected_rule",
        values["protected_rule"],
        frozenset({"output", "expected_output"}),
    )
    _validate_output("protected output", protected["output"])
    _validate_output("protected expected_output", protected["expected_output"])
    rules = {}
    for raw_rule in _sequence("task_rules", values["task_rules"]):
        rule = _exact_mapping(
            "task_rule",
            raw_rule,
            frozenset(
                {
                    "task_id",
                    "default_output",
                    "expected_output",
                    "memory_token",
                    "memory_output",
                }
            ),
        )
        task_id = rule["task_id"]
        _validate_token("task_rule task_id", task_id)
        for name in ("default_output", "expected_output", "memory_output"):
            _validate_output(name, rule[name])
        memory_token = rule["memory_token"]
        if memory_token is not None:
            _validate_output("memory_token", memory_token)
        if task_id in rules:
            raise ValueError("task_rules must contain unique task_id values")
        rules[task_id] = MappingProxyType(rule)
    if not rules:
        raise ValueError("task_rules must not be empty")
    frozen_rules = MappingProxyType(rules)

    def execute(request) -> ExecutionObservation:
        rule = frozen_rules.get(request.task.task_id)
        if rule is None:
            raise ValueError("fixture task has no declarative verifier rule")
        if request.query_class == "protected":
            output = protected["output"]
        elif rule["memory_token"] is not None and any(
            rule["memory_token"] in view.rendered_text
            and not view.rendered_text.startswith("DO_NOT_USE:")
            for view in request.selected_views
        ):
            output = rule["memory_output"]
        else:
            output = rule["default_output"]
        selected_tokens = sum(
            len(view.rendered_text.split()) for view in request.selected_views
        )
        return ExecutionObservation(
            output_text=output,
            latency_ms=cost["base_latency_ms"]
            + request.replica
            + len(request.selected_views),
            input_tokens=cost["base_input_tokens"] + selected_tokens,
            output_tokens=cost["output_tokens"],
            estimated_cost_usd=0.0,
        )

    def verify(task, query_class, observation) -> VerificationObservation:
        rule = frozen_rules.get(task.task_id)
        if rule is None:
            raise ValueError("fixture task has no declarative verifier rule")
        expected = (
            protected["expected_output"]
            if query_class == "protected"
            else rule["expected_output"]
        )
        passed = observation.output_text == expected
        return VerificationObservation(
            success=passed,
            first_pass_success=passed,
            verifier_code="mechanical_pass" if passed else "mechanical_fail",
        )

    return execute, verify


def _blocked_poison_view_ids(bundle: FixtureBundle) -> frozenset[str]:
    blocked = set()
    for task in bundle.tasks:
        for query_class in bundle.query_classes:
            for view in bundle.views_for(task, query_class, "poisoned"):
                if view.verification_state == "blocked":
                    blocked.add(view.view_id)
    return frozenset(blocked)


def _result_slice(
    results: tuple[LearningRunResult, ...],
    selector: str,
    intervention: str,
) -> tuple[LearningRunResult, ...]:
    return tuple(
        row
        for row in results
        if row.selector == selector and row.intervention == intervention
    )


def _matched_delta(
    baseline: tuple[LearningRunResult, ...],
    candidate: tuple[LearningRunResult, ...],
) -> float:
    def key(row):
        return (row.task_id, row.task_hash, row.query_class, row.replica)

    before = {key(row): row for row in baseline}
    after = {key(row): row for row in candidate}
    if not before or set(before) != set(after):
        raise ValueError("causal result slices must contain exact matched cases")
    return sum(float(after[item].success) - float(before[item].success) for item in before) / len(
        before
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m benchmarks.learning_kernel_r0")
    subparsers = parser.add_subparsers(dest="command", required=True)
    dry_run = subparsers.add_parser("dry-run")
    dry_run.add_argument("--fixture-dir", required=True)
    run = subparsers.add_parser("run")
    run.add_argument("--fixture-dir", required=True)
    run.add_argument("--out", required=True)
    read_back = subparsers.add_parser("read-back")
    read_back.add_argument("--fixture-dir", required=True)
    read_back.add_argument("--runs", required=True)
    read_back.add_argument("--write-summary")
    return parser


def _read_canonical_json(path: Path) -> tuple[Mapping[str, Any], bytes]:
    content = path.read_bytes()
    raw = json.loads(content)
    if not isinstance(raw, Mapping):
        raise TypeError(f"{path.name} must contain a JSON object")
    if content != canonical_json_bytes(raw) + b"\n":
        raise ValueError(f"{path.name} must use canonical JSON with one final newline")
    return raw, content


def _write_canonical(path: Path, payload: Mapping[str, Any]) -> None:
    content = canonical_json_bytes(payload) + b"\n"
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError("summary path already contains conflicting evidence")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)


def _print_json(payload: Mapping[str, Any]) -> None:
    print(canonical_json_bytes(payload).decode("utf-8"))


def _exact_mapping(label: str, raw: Any, fields: frozenset[str]) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TypeError(f"{label} must be a mapping")
    unknown = set(raw) - fields
    missing = fields - set(raw)
    if unknown or missing:
        raise TypeError(f"{label} fields must exactly match the frozen schema")
    return dict(raw)


def _file_hashes(raw: Any) -> dict[str, str]:
    values = _exact_mapping(
        "file_hashes",
        raw,
        frozenset({"tasks.json", "experiences.json", "verifier.json"}),
    )
    for name, value in values.items():
        _validate_hash(name, value)
    return values


def _axis(name: str, raw: Any, allowed: tuple[str, ...]) -> tuple[str, ...]:
    values = _sequence(name, raw)
    if tuple(values) != allowed:
        raise ValueError(f"{name} must equal the frozen complete axis")
    return tuple(values)


def _token_axis(name: str, raw: Any) -> tuple[str, ...]:
    values = tuple(_sequence(name, raw))
    if not values or len(set(values)) != len(values):
        raise ValueError(f"{name} must contain unique values")
    for value in values:
        _validate_token(name, value)
    return values


def _sequence(name: str, raw: Any) -> tuple[Any, ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise TypeError(f"{name} must be a sequence")
    return tuple(raw)


def _positive_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a positive integer")
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


def _finite_number(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def _validate_token(name: str, value: Any) -> None:
    if not isinstance(value, str) or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe token")


def _validate_hash(name: str, value: Any) -> None:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 value")


def _validate_output(name: str, value: Any) -> None:
    if not isinstance(value, str) or _OUTPUT_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe declarative output token")


__all__ = [
    "FixtureBundle",
    "load_fixture",
    "main",
    "run_fixture",
    "summarize_results",
]
