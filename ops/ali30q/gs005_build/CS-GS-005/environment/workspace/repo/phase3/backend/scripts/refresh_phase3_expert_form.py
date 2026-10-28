"""Probe or refresh expert Form metadata; browser acceptance remains required."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
for path in (BACKEND_ROOT, SCRIPT_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from publish_phase3_single_submission_forms import FeishuFormClient
from reconcile_phase3_single_submission_base import _load_env, _load_lark_client
from services.fde_phase3_single_submission_forms import ExpertFormProbe, FormPublisher


CONFIRMATION = "FDE_PHASE3_EXPERT_FORM_REFRESH"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-token", default=os.environ.get("FDE_PHASE3_BASE_TOKEN"))
    parser.add_argument(
        "--secret-file",
        default=str(Path.home() / ".claude" / ".cache" / ".fde_api_secrets.env"),
    )
    parser.add_argument("--probe", action="store_true", help="read expert Form metadata only")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="refresh expert Form metadata only; browser acceptance is still required",
    )
    parser.add_argument("--confirm", help=f"required with --apply: {CONFIRMATION}")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not isinstance(args.base_token, str) or not args.base_token.strip():
        raise SystemExit("--base-token or FDE_PHASE3_BASE_TOKEN is required")
    if args.apply and args.probe:
        raise SystemExit("--probe and --apply cannot be used together")
    if args.apply and args.confirm != CONFIRMATION:
        raise SystemExit(f"--apply requires --confirm {CONFIRMATION}")


def probe_output(probe: ExpertFormProbe) -> dict[str, Any]:
    """Return the intentionally small operator-safe Form status payload."""

    return {
        "form_name": probe.form_name,
        "shared": probe.shared,
        "shared_limit": probe.shared_limit,
        "submit_limit_once": probe.submit_limit_once,
        "question_count": probe.question_count,
        "visible_question_count": probe.visible_question_count,
    }


def result_output(
    probe: ExpertFormProbe,
    *,
    metadata_refreshed: bool,
) -> dict[str, Any]:
    """Report metadata state without claiming an externally usable Form."""

    return {
        "mode": "metadata_refresh" if metadata_refreshed else "metadata_probe",
        "external_fillability": "unverified",
        "form": probe_output(probe),
    }


def main() -> int:
    args = _args()
    validate_args(args)
    _load_env(Path(args.secret_file))
    publisher = FormPublisher(FeishuFormClient(_load_lark_client(args.base_token), args.base_token))
    probe = (
        publisher.refresh_expert_form(confirmed=True)
        if args.apply
        else publisher.probe_expert_form()
    )
    print(
        json.dumps(result_output(probe, metadata_refreshed=args.apply), ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
