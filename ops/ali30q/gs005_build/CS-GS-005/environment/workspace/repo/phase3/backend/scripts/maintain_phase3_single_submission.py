"""Run a fail-closed Phase 3 schema and public-Form maintenance window."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
SCRIPTS_ROOT = Path(__file__).resolve().parent
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from publish_phase3_single_submission_forms import (  # noqa: E402
    FeishuFormClient,
    _load_env,
    _load_lark_client,
)
from reconcile_phase3_single_submission_base import FeishuSchemaClient  # noqa: E402
from services.fde_phase3_single_submission_forms import FormPublisher  # noqa: E402
from services.fde_phase3_single_submission_maintenance import (  # noqa: E402
    Phase3MaintenanceCoordinator,
)
from services.fde_phase3_single_submission_provisioning import BitableReconciler  # noqa: E402


CONFIRMATION = "FDE_PHASE3_MAINTENANCE_WINDOW"


def _args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-token", default=os.environ.get("FDE_PHASE3_BASE_TOKEN"))
    parser.add_argument(
        "--secret-file",
        default=str(Path.home() / ".claude" / ".cache" / ".fde_api_secrets.env"),
    )
    parser.add_argument("--apply", action="store_true", help="apply the approved maintenance sequence")
    parser.add_argument(
        "--confirm",
        help=f"required with --apply: {CONFIRMATION}",
    )
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    if not isinstance(args.base_token, str) or not args.base_token.strip():
        raise SystemExit("--base-token or FDE_PHASE3_BASE_TOKEN is required")
    if args.apply and args.confirm != CONFIRMATION:
        raise SystemExit(f"--apply requires --confirm {CONFIRMATION}")


def _output_plan(coordinator: Phase3MaintenanceCoordinator) -> dict[str, object]:
    plan = coordinator.plan()
    return {
        "mode": "dry_run",
        "create_fields": [
            {"table": field.table_name, "field": field.field.name}
            for field in plan.create_initial_fields
        ],
        "task_form_private_window": plan.task_form_requires_private_window,
    }


def main() -> int:
    args = _args()
    validate_args(args)
    _load_env(Path(args.secret_file))
    lark = _load_lark_client(args.base_token)
    coordinator = Phase3MaintenanceCoordinator(
        BitableReconciler(FeishuSchemaClient(lark, args.base_token)),
        FormPublisher(FeishuFormClient(lark, args.base_token)),
    )
    if not args.apply:
        print(json.dumps(_output_plan(coordinator), ensure_ascii=False))
        return 0

    receipt = coordinator.apply(confirmed=True)
    print(
        json.dumps(
            {
                "mode": "applied",
                "task_form_was_paused": receipt.task_form_was_paused,
                "created_fields": [
                    {"table": field.table_name, "field": field.field.name}
                    for field in receipt.schema.created_initial_fields
                ],
                "published_forms": [
                    {"name": form.form_name, "shared_url": form.shared_url}
                    for form in receipt.forms.forms
                ],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
