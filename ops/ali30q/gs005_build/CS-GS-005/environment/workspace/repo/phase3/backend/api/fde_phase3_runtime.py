"""Authenticated, metadata-only runtime entrypoints for the Phase 3 Feishu loop."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import re
from typing import Any, Protocol, runtime_checkable

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from services.fde_phase3_event_orchestrator import (
    AuthenticatedEventEnvelope,
    EventHandlingResult,
    EventInProgressError,
    StaleEventError,
)
from services.fde_phase3_feishu_runtime_contract import (
    AppRole,
    BitableEventEnvelope,
    MentorProjection,
    RuntimeRoute,
)
from services.fde_phase3_interaction_contract import (
    InteractionEvidenceSubmission,
    InteractionSubmissionResult,
    MentorInteractionPage,
)
from services.fde_phase3_t1_workbench_contract import public_interface_contract_payload


router = APIRouter(prefix="/api/platform/fde/phase3", tags=["FDE Phase 3 Runtime"])
_MENTOR_EXPERT_HANDLE_PATTERN = re.compile(r"mentor_expert_[A-Za-z0-9_-]{1,80}\Z")
_MENTOR_TASK_HANDLE_PATTERN = re.compile(r"mentor_task_[A-Za-z0-9_-]{1,80}\Z")
_MENTOR_CONTINUATION_PATTERN = re.compile(r"mentor_continue_[A-Za-z0-9_-]{20,128}\Z")


@dataclass(frozen=True)
class EventVerification:
    """Verifier result that can support Feishu's URL verification challenge."""

    authenticated: bool
    challenge: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.authenticated, bool):
            raise ValueError("authenticated must be a boolean")
        if self.challenge is not None and (
            not isinstance(self.challenge, str) or not self.challenge.strip()
        ):
            raise ValueError("challenge must be a non-empty string when present")


@runtime_checkable
class FeishuEventVerifier(Protocol):
    """Production binding verifies Feishu signatures outside the API body parser."""

    def verify(
        self,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
    ) -> EventVerification: ...


@runtime_checkable
class Phase3EventHandler(Protocol):
    """The event orchestrator's narrow public interface."""

    def handle(self, authenticated: AuthenticatedEventEnvelope) -> EventHandlingResult: ...


@runtime_checkable
class MentorSessionVerifier(Protocol):
    """Bind an app-authenticated caller to one opaque expert scope."""

    def authenticate(self, headers: Mapping[str, str]) -> str | None: ...


@runtime_checkable
class MentorStatusResolver(Protocol):
    """Resolve a projection only within the already-authenticated expert scope."""

    def resolve(
        self,
        *,
        expert_scope_handle: str,
        task_handle: str,
    ) -> MentorProjection | None: ...


@runtime_checkable
class MentorContinuationWorkflow(Protocol):
    """Server-side resolver for opaque handles and controlled interaction writes.

    The implementation owns durable continuation consumption, session-scope
    validation, question/expert relation resolution, Bitable read-back and the
    controlled writer. None of those identities are accepted from this API.
    """

    def open(
        self,
        *,
        expert_scope_handle: str,
        continuation_reference: str,
    ) -> MentorInteractionPage | None: ...

    def submit(
        self,
        *,
        expert_scope_handle: str,
        continuation_reference: str,
        evidence: InteractionEvidenceSubmission,
        request_key: str,
    ) -> InteractionSubmissionResult: ...


@dataclass(frozen=True)
class Phase3RuntimeDependencies:
    """Injected runtime integration. No credential or Base identity is retained here."""

    event_verifier: FeishuEventVerifier
    event_handler: Phase3EventHandler
    mentor_session_verifier: MentorSessionVerifier
    mentor_status_resolver: MentorStatusResolver
    mentor_continuation_workflow: MentorContinuationWorkflow | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.event_verifier, FeishuEventVerifier):
            raise ValueError("event_verifier must implement FeishuEventVerifier")
        if not isinstance(self.event_handler, Phase3EventHandler):
            raise ValueError("event_handler must implement Phase3EventHandler")
        if not isinstance(self.mentor_session_verifier, MentorSessionVerifier):
            raise ValueError("mentor_session_verifier must implement MentorSessionVerifier")
        if not isinstance(self.mentor_status_resolver, MentorStatusResolver):
            raise ValueError("mentor_status_resolver must implement MentorStatusResolver")
        if self.mentor_continuation_workflow is not None and not isinstance(
            self.mentor_continuation_workflow,
            MentorContinuationWorkflow,
        ):
            raise ValueError(
                "mentor_continuation_workflow must implement MentorContinuationWorkflow"
            )


_runtime: Phase3RuntimeDependencies | None = None


def configure_phase3_runtime(dependencies: Phase3RuntimeDependencies | None) -> None:
    """Set dependencies at application startup or reset them in isolated tests."""

    global _runtime
    _runtime = dependencies


def _require_runtime() -> Phase3RuntimeDependencies:
    if _runtime is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="phase3 runtime is not configured",
        )
    return _runtime


@router.post("/events")
async def receive_phase3_event(request: Request) -> JSONResponse:
    """Authenticate and route only a bounded Feishu Bitable event envelope."""

    runtime = _require_runtime()
    payload = await _read_mapping_payload(request)
    try:
        verification = runtime.event_verifier.verify(
            headers=dict(request.headers),
            payload=payload,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="event verifier is unavailable",
        ) from None
    if not isinstance(verification, EventVerification):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="event verifier is unavailable",
        )
    if verification.authenticated is not True:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="event authentication failed",
        )
    if verification.challenge is not None:
        return JSONResponse({"challenge": verification.challenge})

    try:
        event = _parse_event_metadata(payload)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid event metadata",
        ) from None

    try:
        result = runtime.event_handler.handle(
            AuthenticatedEventEnvelope(actor=AppRole.NAUTILUS, event=event)
        )
    except StaleEventError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="event is stale") from None
    except EventInProgressError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="event pending recovery",
        ) from None
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="event rejected") from None
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="event rejected") from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="event handler is unavailable",
        ) from None

    if not isinstance(result, EventHandlingResult):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="event handler is unavailable",
        )
    if result.outcome == "written_and_read_back":
        return JSONResponse({"status": "accepted"}, status_code=status.HTTP_202_ACCEPTED)
    if result.outcome == "already_processed":
        return JSONResponse({"status": "already_processed"})
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="event unavailable")


@router.get("/mentor/status")
async def mentor_status(
    request: Request,
    task_handle: str = Query(..., min_length=1, max_length=100),
) -> dict[str, Any]:
    """Return only the caller's redacted Mentor projection for one opaque task."""

    runtime = _require_runtime()
    if _MENTOR_TASK_HANDLE_PATTERN.fullmatch(task_handle) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid task handle")
    expert_scope_handle = _authenticate_mentor_scope(runtime, request)
    try:
        projection = runtime.mentor_status_resolver.resolve(
            expert_scope_handle=expert_scope_handle,
            task_handle=task_handle,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="mentor status is unavailable",
        ) from None
    if projection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task status not found")
    if projection.expert_scope_handle != expert_scope_handle:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="mentor scope mismatch")
    if projection.task_handle != task_handle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task status not found")
    return projection.to_workbench_payload()


@router.get("/mentor/interface-contract")
async def mentor_interface_contract(request: Request) -> dict[str, Any]:
    """Return reviewed expert UI vocabulary to an authenticated Mentor user."""

    runtime = _require_runtime()
    _authenticate_mentor_scope(runtime, request)
    return public_interface_contract_payload()


@router.get("/mentor/continuations/{continuation_reference}")
async def open_mentor_continuation(
    continuation_reference: str,
    request: Request,
) -> dict[str, object]:
    """Open a Mentor-scoped interaction page without exposing business identities."""

    runtime = _require_runtime()
    if _MENTOR_CONTINUATION_PATTERN.fullmatch(continuation_reference) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="continuation unavailable")
    expert_scope_handle = _authenticate_mentor_scope(runtime, request)
    workflow = _require_continuation_workflow(runtime)
    try:
        page = workflow.open(
            expert_scope_handle=expert_scope_handle,
            continuation_reference=continuation_reference,
        )
    except (PermissionError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="continuation unavailable") from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="continuation workflow is unavailable",
        ) from None
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="continuation unavailable")
    if not isinstance(page, MentorInteractionPage):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="continuation workflow is unavailable",
        )
    return page.to_payload()


@router.post("/mentor/continuations/{continuation_reference}/interaction")
async def submit_mentor_interaction(
    continuation_reference: str,
    request: Request,
) -> JSONResponse:
    """Submit only public interaction evidence through an authenticated continuation."""

    runtime = _require_runtime()
    if _MENTOR_CONTINUATION_PATTERN.fullmatch(continuation_reference) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="continuation unavailable")
    expert_scope_handle = _authenticate_mentor_scope(runtime, request)
    evidence = await _read_interaction_submission(request)
    workflow = _require_continuation_workflow(runtime)
    request_key = _interaction_request_key(continuation_reference, evidence)
    try:
        result = workflow.submit(
            expert_scope_handle=expert_scope_handle,
            continuation_reference=continuation_reference,
            evidence=evidence,
            request_key=request_key,
        )
    except (PermissionError, ValueError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="continuation unavailable") from None
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="continuation workflow is unavailable",
        ) from None
    if not isinstance(result, InteractionSubmissionResult):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="continuation workflow is unavailable",
        )
    if result.outcome == "submitted":
        return JSONResponse({"status": "submitted"}, status_code=status.HTTP_202_ACCEPTED)
    return JSONResponse({"status": "already_submitted"})


async def _read_mapping_payload(request: Request) -> Mapping[str, object]:
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid event metadata",
        ) from None
    if not isinstance(payload, Mapping):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid event metadata",
        )
    return payload


async def _read_interaction_submission(request: Request) -> InteractionEvidenceSubmission:
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid interaction submission",
        ) from None
    if not isinstance(payload, Mapping):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid interaction submission",
        )
    try:
        return InteractionEvidenceSubmission.from_mapping(payload)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="invalid interaction submission",
        ) from None


def _authenticate_mentor_scope(
    runtime: Phase3RuntimeDependencies,
    request: Request,
) -> str:
    try:
        expert_scope_handle = runtime.mentor_session_verifier.authenticate(dict(request.headers))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="mentor authentication is unavailable",
        ) from None
    if (
        not isinstance(expert_scope_handle, str)
        or _MENTOR_EXPERT_HANDLE_PATTERN.fullmatch(expert_scope_handle) is None
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="mentor authentication failed",
        )
    return expert_scope_handle


def _require_continuation_workflow(
    runtime: Phase3RuntimeDependencies,
) -> MentorContinuationWorkflow:
    workflow = runtime.mentor_continuation_workflow
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="continuation workflow is unavailable",
        )
    return workflow


def _interaction_request_key(
    continuation_reference: str,
    evidence: InteractionEvidenceSubmission,
) -> str:
    material = "\x1f".join((continuation_reference, evidence.canonical_json())).encode("utf-8")
    return "interaction_request_" + hashlib.sha256(material).hexdigest()


def _parse_event_metadata(payload: Mapping[str, object]) -> BitableEventEnvelope:
    raw_event = payload.get("event")
    if not isinstance(raw_event, Mapping):
        raise ValueError("event metadata is required")
    return BitableEventEnvelope(
        route=RuntimeRoute(raw_event.get("route")),
        record_id=_required_string(raw_event.get("record_id")),
        record_version=_required_version(raw_event.get("record_version")),
        source_event_id=_required_string(raw_event.get("source_event_id")),
    )


def _required_string(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("event metadata field is invalid")
    return value


def _required_version(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("record version is invalid")
    return value
