"""Small user-facing command for the deterministic Compass Gate A loop."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from gep.live_coding_adapter import (
    AnthropicCompatibleProvider,
    ClaudeCliProvider,
    GateBSoftwareVerifier,
    LiveCodingAdapter,
    LiveCodingError,
    load_value_suite,
    preflight_value_suite,
)
from gep.loop_run import ActionArtifact, LoopRunError, run_loop, verify_run
from gep.verdict_packet import VerdictPacket


class _GateAAction:
    """Deterministic fixture actor; it is not a provider or live agent."""

    def execute(
        self,
        task: dict[str, object],
        advice: str | None,
        work_dir: Path,
    ) -> ActionArtifact:
        del work_dir
        answer = "fixed" if advice else "broken"
        return ActionArtifact(
            episode_id=str(task["episode_id"]),
            content={"answer": answer},
            tool_chain=("fixture_edit", "fixture_test"),
        )


class _GateAVerifier:
    """Deterministic software oracle used only to prove evidence plumbing."""

    def __init__(self, policy_hash: object, environment_hash: object) -> None:
        self._policy_hash = policy_hash
        self._environment_hash = environment_hash

    def verify(
        self,
        task: dict[str, object],
        artifact: ActionArtifact,
        oracle: dict[str, object],
    ) -> VerdictPacket:
        del task
        outcome = (
            "success" if artifact.content.get("answer") == oracle.get("expected") else "failure"
        )
        return VerdictPacket(
            episode_id=artifact.episode_id,
            episode_event_hash=artifact.episode_event_hash or "",
            outcome=outcome,
            verifier_kind="software_test",
            verifier_version="compass-gate-a-fixture-v1",
            verifier_policy_hash=str(self._policy_hash),
            evidence_hash=artifact.evidence_hash,
            environment_fingerprint_hash=str(self._environment_hash),
            failure_class=None if outcome == "success" else "oracle.mismatch",
        )


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            plan = _load_plan(args.suite)
            _prepare_output(args.out)
            verifier = _GateAVerifier(
                plan.get("verifier_policy_hash"),
                plan.get("environment_fingerprint_hash"),
            )
            report = run_loop(plan, args.out, _GateAAction(), verifier)
        elif args.command == "verify":
            report = verify_run(args.out)
        elif args.command == "preflight":
            receipt = preflight_value_suite(load_value_suite(args.suite))
            _print_preflight(receipt)
            return 0
        else:
            suite = load_value_suite(args.suite)
            preflight_value_suite(suite)
            _prepare_output(args.out)
            report = run_loop(
                suite.loop_plan,
                args.out,
                LiveCodingAdapter(suite, _live_provider(suite)),
                GateBSoftwareVerifier(suite),
            )
    except (
        LiveCodingError,
        LoopRunError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"nautilus-compass loop: {exc}", file=sys.stderr)
        return 2
    _print_summary(report)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nautilus-compass loop",
        description="Run or independently replay deterministic local Compass evidence.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run", help="run a frozen deterministic Gate A suite")
    run.add_argument("suite", type=Path, help="frozen JSON task suite")
    run.add_argument("--out", type=Path, required=True, help="new or empty evidence directory")
    verify = commands.add_parser("verify", help="replay an existing evidence directory")
    verify.add_argument("out", type=Path, help="evidence directory")
    preflight = commands.add_parser(
        "preflight",
        help="bind a Gate B provider request set without calling the provider",
    )
    preflight.add_argument("suite", type=Path, help="frozen Gate B value suite")
    live_run = commands.add_parser(
        "live-run",
        help="run one bounded Gate B live provider comparison after preflight",
    )
    live_run.add_argument("suite", type=Path, help="frozen Gate B value suite")
    live_run.add_argument("--out", type=Path, required=True, help="new or empty evidence directory")
    return parser


def _load_plan(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LoopRunError("suite is missing or invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise LoopRunError("suite must be a JSON object")
    return dict(value)


def _prepare_output(path: Path) -> None:
    if not path.exists():
        return
    if not path.is_dir() or any(path.iterdir()):
        raise LoopRunError("output directory must be new or empty")
    path.rmdir()


def _live_provider(suite: object):
    provider = getattr(suite, "provider", None)
    if not isinstance(provider, Mapping):
        raise LiveCodingError("provider_config_invalid")
    adapter_kind = provider.get("adapter_kind")
    if adapter_kind == "claude_cli":
        return ClaudeCliProvider(suite)
    if adapter_kind == "anthropic_compatible":
        return AnthropicCompatibleProvider(suite)
    raise LiveCodingError("provider_adapter_not_runnable")


def _print_summary(report: Mapping[str, object]) -> None:
    arms = report.get("arms")
    promotion = report.get("promotion")
    if not isinstance(arms, Mapping) or not isinstance(promotion, Mapping):
        raise LoopRunError("report has an invalid summary shape")
    print(f"Compass learning loop: {report.get('decision')}")
    print(f"reason: {report.get('reason_code')}")
    for label in ("control", "treatment"):
        arm = arms.get(label)
        if not isinstance(arm, Mapping):
            raise LoopRunError(f"report is missing {label} arm")
        print(f"{label}: {arm.get('outcome')}")
    print(f"automatic promotion: {str(promotion.get('automatic_promotion_authorized')).lower()}")


def _print_preflight(receipt: Mapping[str, object]) -> None:
    print("Compass live preflight: ready")
    print(f"expected provider calls: {receipt.get('expected_calls')}")
    print(f"zero provider calls: {str(receipt.get('zero_provider_calls')).lower()}")
    print(f"zero writes: {str(receipt.get('zero_writes')).lower()}")
    print(f"automatic promotion: {str(receipt.get('automatic_promotion_authorized')).lower()}")


if __name__ == "__main__":
    sys.exit(main())
