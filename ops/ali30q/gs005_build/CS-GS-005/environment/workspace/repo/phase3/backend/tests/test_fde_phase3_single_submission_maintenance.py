from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from services.fde_phase3_single_submission_maintenance import (
    MaintenanceConfirmationError,
    Phase3MaintenanceCoordinator,
)
from services.fde_phase3_single_submission_provisioning import (
    InitialFieldPlan,
    ReconciliationPlan,
    ReconciliationReceipt,
)
from services.fde_phase3_single_submission_schema import FieldSpec


TASK_TABLE = "第三期任务与交互提交"
EXPORT_TABLE = "第三期导出与回执"


class FakeReconciler:
    def __init__(self, events: list[str], fields: tuple[InitialFieldPlan, ...]) -> None:
        self._events = events
        self._fields = fields

    def plan(self) -> ReconciliationPlan:
        self._events.append("plan")
        return ReconciliationPlan((), self._fields, (), (), ())

    def apply(self, *, confirmed: bool) -> ReconciliationReceipt:
        assert confirmed is True
        self._events.append("schema")
        return ReconciliationReceipt((), self._fields, (), (), ())


class FakePublisher:
    def __init__(self, events: list[str], *, fail_reconfigure: bool = False) -> None:
        self._events = events
        self._fail_reconfigure = fail_reconfigure

    def pause_public_forms(self, *, confirmed: bool, form_names: tuple[str, ...]):
        assert confirmed is True
        self._events.append("pause:" + ",".join(form_names))
        return tuple(form_names)

    def reconfigure_public_forms(self, *, confirmed: bool):
        assert confirmed is True
        self._events.append("reconfigure")
        if self._fail_reconfigure:
            raise RuntimeError("form questions are not ready")
        return ("published",)


def maintenance_fields(*, task: bool) -> tuple[InitialFieldPlan, ...]:
    fields = [InitialFieldPlan(EXPORT_TABLE, FieldSpec("V5签名键ID", 1))]
    if task:
        fields.insert(0, InitialFieldPlan(TASK_TABLE, FieldSpec("返修关联码", 1)))
    return tuple(fields)


def test_maintenance_pauses_task_form_before_schema_and_reconfiguration() -> None:
    events: list[str] = []
    coordinator = Phase3MaintenanceCoordinator(
        FakeReconciler(events, maintenance_fields(task=True)),
        FakePublisher(events),
    )

    receipt = coordinator.apply(confirmed=True)

    assert receipt.task_form_was_paused is True
    assert events == [
        "plan",
        "pause:第三期任务与交互提交（正式）",
        "schema",
        "reconfigure",
    ]


def test_maintenance_skips_task_pause_when_only_non_form_fields_are_missing() -> None:
    events: list[str] = []
    coordinator = Phase3MaintenanceCoordinator(
        FakeReconciler(events, maintenance_fields(task=False)),
        FakePublisher(events),
    )

    receipt = coordinator.apply(confirmed=True)

    assert receipt.task_form_was_paused is False
    assert events == ["plan", "schema", "reconfigure"]


def test_maintenance_requires_confirmation_before_any_mutation() -> None:
    events: list[str] = []
    coordinator = Phase3MaintenanceCoordinator(
        FakeReconciler(events, maintenance_fields(task=True)),
        FakePublisher(events),
    )

    with pytest.raises(MaintenanceConfirmationError):
        coordinator.apply(confirmed=False)

    assert events == []


def test_maintenance_leaves_task_form_paused_when_reconfiguration_fails() -> None:
    events: list[str] = []
    coordinator = Phase3MaintenanceCoordinator(
        FakeReconciler(events, maintenance_fields(task=True)),
        FakePublisher(events, fail_reconfigure=True),
    )

    with pytest.raises(RuntimeError, match="not ready"):
        coordinator.apply(confirmed=True)

    assert events == [
        "plan",
        "pause:第三期任务与交互提交（正式）",
        "schema",
        "reconfigure",
    ]


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "maintain_phase3_single_submission.py"
)


def load_maintenance_cli_module():
    module_name = "phase3_single_submission_maintenance_cli_test"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_maintenance_cli_requires_its_own_confirmation_and_has_no_record_mode() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--help"],
        cwd=SCRIPT_PATH.parents[1],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "--apply" in result.stdout
    assert "FDE_PHASE3_MAINTENANCE_WINDOW" in result.stdout
    assert "records" not in result.stdout.lower()

    module = load_maintenance_cli_module()
    with pytest.raises(SystemExit, match="FDE_PHASE3_MAINTENANCE_WINDOW"):
        module.validate_args(
            argparse.Namespace(
                base_token="base-safe",
                secret_file="unused",
                apply=True,
                confirm="wrong",
            )
        )
    module.validate_args(
        argparse.Namespace(
            base_token="base-safe",
            secret_file="unused",
            apply=False,
            confirm=None,
        )
    )
