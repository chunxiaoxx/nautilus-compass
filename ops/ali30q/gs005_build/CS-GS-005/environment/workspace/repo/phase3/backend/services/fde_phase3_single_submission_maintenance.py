"""Fail-closed coordination for a Phase 3 public-Form maintenance window.

The coordinator performs metadata-only operations. It never reads or writes a
Bitable business record. When a new task-table field affects the public Form,
it first unshares that Form, then adds approved fields, validates the Form
contract, and finally lets the Form publisher republish it. A failure leaves
the Form private instead of exposing an incomplete intake path.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from services.fde_phase3_single_submission_forms import PausedForm
from services.fde_phase3_single_submission_provisioning import (
    InitialFieldPlan,
    ReconciliationPlan,
    ReconciliationReceipt,
)
from services.fde_phase3_single_submission_schema import TASK_FORM_NAME


TASK_SUBMISSION_TABLE = "第三期任务与交互提交"


class MaintenanceConfirmationError(ValueError):
    """Raised when a maintenance mutation lacks explicit confirmation."""


class ReconciliationPort(Protocol):
    def plan(self) -> ReconciliationPlan: ...

    def apply(self, *, confirmed: bool) -> ReconciliationReceipt: ...


class FormMaintenancePort(Protocol):
    def pause_public_forms(
        self,
        *,
        confirmed: bool,
        form_names: tuple[str, ...],
    ) -> tuple[PausedForm, ...]: ...

    def reconfigure_public_forms(self, *, confirmed: bool) -> Any: ...


@dataclass(frozen=True)
class MaintenancePlan:
    create_initial_fields: tuple[InitialFieldPlan, ...]
    task_form_requires_private_window: bool


@dataclass(frozen=True)
class MaintenanceReceipt:
    schema: ReconciliationReceipt
    task_form_was_paused: bool
    paused_forms: tuple[PausedForm, ...]
    forms: Any


class Phase3MaintenanceCoordinator:
    """Sequence additive schema and public-Form changes without row access."""

    def __init__(
        self,
        reconciler: ReconciliationPort,
        forms: FormMaintenancePort,
    ) -> None:
        self._reconciler = reconciler
        self._forms = forms

    def plan(self) -> MaintenancePlan:
        reconciliation = self._reconciler.plan()
        fields = reconciliation.create_initial_fields
        return MaintenancePlan(
            create_initial_fields=fields,
            task_form_requires_private_window=any(
                field.table_name == TASK_SUBMISSION_TABLE for field in fields
            ),
        )

    def apply(self, *, confirmed: bool) -> MaintenanceReceipt:
        if not confirmed:
            raise MaintenanceConfirmationError(
                "Phase 3 maintenance requires explicit confirmation"
            )
        plan = self.plan()
        paused: tuple[PausedForm, ...] = ()
        if plan.task_form_requires_private_window:
            paused = self._forms.pause_public_forms(
                confirmed=True,
                form_names=(TASK_FORM_NAME,),
            )
            if not paused:
                raise RuntimeError("task Form pause did not return a receipt")

        schema = self._reconciler.apply(confirmed=True)
        forms = self._forms.reconfigure_public_forms(confirmed=True)
        return MaintenanceReceipt(
            schema=schema,
            task_form_was_paused=plan.task_form_requires_private_window,
            paused_forms=paused,
            forms=forms,
        )
