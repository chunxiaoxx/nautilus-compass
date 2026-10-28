"""Pure Phase 3 field-ownership and export-boundary contract.

This module intentionally has no Feishu client, environment access, or I/O.
It defines the offline checks that a later approved adapter must satisfy with
Bitable read-back and authenticated reviewer identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
import re
from types import MappingProxyType
from typing import Any, ClassVar, Iterable, Mapping, Protocol, Sequence


def _require_identity(value: str | None, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} record identity is required")


EVENT_ID_PATTERN = re.compile(r"evt_[A-Za-z0-9_-]{1,80}\Z")
SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
V3_TASK_ID_PATTERN = re.compile(r"task_v3_[A-Za-z0-9_-]{1,80}\Z")


class FeishuBitableClient(Protocol):
    """The only read operations permitted to a Phase 3 schema probe."""

    def list_tables(self, base_token: str) -> Sequence[Mapping[str, Any]]:
        """Return table metadata for one explicitly selected Bitable base."""

    def list_fields(
        self, base_token: str, table_id: str
    ) -> Sequence[Mapping[str, Any]]:
        """Return field metadata for one table in that Bitable base."""


@dataclass(frozen=True)
class SchemaOption:
    """Audit-safe selected-field option metadata, without any row values."""

    name: str
    option_id: str | None = None
    color: int | str | None = None

    def to_audit_dict(self) -> dict[str, Any]:
        value: dict[str, Any] = {"name": self.name}
        if self.option_id is not None:
            value["id"] = self.option_id
        if self.color is not None:
            value["color"] = self.color
        return value


@dataclass(frozen=True)
class SchemaField:
    """One immutable field description retained by the read-only probe."""

    name: str
    field_type: str
    options: tuple[SchemaOption, ...]

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.field_type,
            "options": [option.to_audit_dict() for option in self.options],
        }


@dataclass(frozen=True)
class SchemaTable:
    """One immutable table schema without its Feishu table identity or rows."""

    name: str
    fields: tuple[SchemaField, ...]

    def to_audit_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "fields": [field.to_audit_dict() for field in self.fields],
        }


@dataclass(frozen=True)
class SchemaProbeResult:
    """An immutable, audit-safe Phase 3 Bitable schema summary."""

    tables: tuple[SchemaTable, ...]
    schema_sha256: str

    @property
    def table_names(self) -> tuple[str, ...]:
        return tuple(table.name for table in self.tables)

    @property
    def schema_hash(self) -> str:
        """Compatibility alias for callers that use the shorter audit label."""

        return self.schema_sha256

    def to_audit_dict(self) -> dict[str, Any]:
        """Return only schema metadata; this object never retains the base token."""

        return {
            "tables": [table.to_audit_dict() for table in self.tables],
            "schema_sha256": self.schema_sha256,
        }


def probe_schema(
    client: FeishuBitableClient,
    *,
    base_token: str,
) -> SchemaProbeResult:
    """Inspect only table/field metadata and return a deterministic safe digest."""

    base_token = validate_explicit_base_token(base_token)
    raw_tables = _require_schema_sequence(client.list_tables(base_token), "table list")
    if not raw_tables:
        raise ValueError("schema must contain at least one table")

    table_metadata = _normalize_tables(raw_tables)
    tables: list[tuple[str, SchemaTable]] = []
    for table_id, table_name in table_metadata:
        raw_fields = _require_schema_sequence(
            client.list_fields(base_token, table_id), f"field list for {table_name}"
        )
        if not raw_fields:
            raise ValueError(f"schema table {table_name} must contain at least one field")
        tables.append((table_id, SchemaTable(table_name, _normalize_fields(raw_fields))))

    ordered_tables = tuple(table for _, table in sorted(tables, key=lambda item: (item[1].name, item[0])))
    audit_payload = {
        "tables": [table.to_audit_dict() for table in ordered_tables],
    }
    encoded = json.dumps(
        audit_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return SchemaProbeResult(
        tables=ordered_tables,
        schema_sha256=hashlib.sha256(encoded).hexdigest(),
    )


def validate_explicit_base_token(base_token: str) -> str:
    """Validate one explicit Base token without I/O or retaining the token."""

    if not isinstance(base_token, str) or not base_token or base_token != base_token.strip():
        raise ValueError("base token must be a non-empty explicit value")
    return base_token


def _require_schema_sequence(value: Any, label: str) -> tuple[Mapping[str, Any], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{label} must be a sequence of metadata mappings")
    if not all(isinstance(item, Mapping) for item in value):
        raise ValueError(f"{label} must contain only metadata mappings")
    return tuple(value)


def _normalize_tables(raw_tables: Sequence[Mapping[str, Any]]) -> tuple[tuple[str, str], ...]:
    table_ids: set[str] = set()
    tables: list[tuple[str, str]] = []
    for raw_table in raw_tables:
        table_id = _require_schema_identity(raw_table.get("table_id"), "table")
        if table_id in table_ids:
            raise ValueError(f"duplicate table identity: {table_id}")
        table_ids.add(table_id)
        tables.append((table_id, _require_schema_name(raw_table.get("name"), "table")))
    return tuple(tables)


def _normalize_fields(raw_fields: Sequence[Mapping[str, Any]]) -> tuple[SchemaField, ...]:
    field_ids: set[str] = set()
    fields: list[tuple[str, SchemaField]] = []
    for raw_field in raw_fields:
        field_id = _require_schema_identity(raw_field.get("field_id"), "field")
        if field_id in field_ids:
            raise ValueError(f"duplicate field identity: {field_id}")
        field_ids.add(field_id)
        fields.append(
            (
                field_id,
                SchemaField(
                    name=_require_schema_name(raw_field.get("field_name"), "field"),
                    field_type=_normalize_field_type(raw_field.get("type")),
                    options=_normalize_field_options(raw_field.get("property")),
                ),
            )
        )
    return tuple(field for _, field in sorted(fields, key=lambda item: (item[1].name, item[0])))


def _require_schema_identity(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        raise ValueError(f"{label} identity must be a non-empty compact string")
    return value


def _require_schema_name(value: Any, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value.strip()
        or value != value.strip()
        or any(ord(character) < 32 for character in value)
    ):
        raise ValueError(f"{label} name must be a non-empty string")
    return value


def _normalize_field_type(value: Any) -> str:
    if isinstance(value, bool):
        raise ValueError("field type must be a non-boolean string or integer")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str) and value.strip() and value == value.strip():
        return value
    raise ValueError("field type must be a non-boolean string or integer")


def _normalize_field_options(raw_property: Any) -> tuple[SchemaOption, ...]:
    if raw_property is None:
        return ()
    if not isinstance(raw_property, Mapping):
        raise ValueError("field property must be metadata mapping")
    raw_options = raw_property.get("options", ())
    if raw_options is None:
        return ()
    if isinstance(raw_options, (str, bytes)) or not isinstance(raw_options, Sequence):
        raise ValueError("field options must be metadata sequence")
    if len(raw_options) > 100:
        raise ValueError("field options exceed audit-safe limit")

    option_ids: set[str] = set()
    options: list[SchemaOption] = []
    for raw_option in raw_options:
        if not isinstance(raw_option, Mapping):
            raise ValueError("field options must contain metadata mappings")
        option_id = raw_option.get("id")
        if option_id is not None:
            option_id = _require_schema_identity(option_id, "option")
            if option_id in option_ids:
                raise ValueError(f"duplicate option identity: {option_id}")
            option_ids.add(option_id)
        color = raw_option.get("color")
        if color is not None and (isinstance(color, bool) or not isinstance(color, (str, int))):
            raise ValueError("option color must be a string or integer")
        options.append(
            SchemaOption(
                name=_require_schema_name(raw_option.get("name"), "option"),
                option_id=option_id,
                color=color,
            )
        )
    return tuple(
        sorted(
            options,
            key=_schema_option_sort_key,
        )
    )


def _schema_option_sort_key(option: SchemaOption) -> tuple[str, str, tuple[int, int | str]]:
    """Sort option colors without collapsing their JSON value types."""

    if option.color is None:
        color_key: tuple[int, int | str] = (0, "")
    elif isinstance(option.color, int):
        color_key = (1, option.color)
    else:
        color_key = (2, option.color)
    return (option.name, option.option_id or "", color_key)


class FieldOwner(str, Enum):
    """The only roles that may originate a mapped Phase 3 field."""

    EXTERNAL = "external_expert"
    INTERNAL = "internal_reviewer"
    BUYER = "buyer"
    V5 = "v5"
    COMPASS = "compass"
    AUTOMATION = "bitable_automation"
    OUTBOUND = "outbound"
    PROHIBITED = "prohibited"


class ReviewStatus(str, Enum):
    P0_REVIEW = "p0_review"
    BUYER_REVIEW = "buyer_review"


@dataclass(frozen=True)
class ReviewContext:
    """Read-back facts after a future adapter authenticates the reviewer."""

    review_record_id: str
    task_record_id: str
    attempt_record_id: str
    validated_reviewer_id: str
    review_status: ReviewStatus

    def __post_init__(self) -> None:
        _require_identity(self.review_record_id, "review")
        _require_identity(self.task_record_id, "task")
        _require_identity(self.attempt_record_id, "attempt")
        if not isinstance(self.validated_reviewer_id, str) or not self.validated_reviewer_id.strip():
            raise ValueError("validated reviewer identity is required")
        if not isinstance(self.review_status, ReviewStatus):
            raise ValueError("review status must be a ReviewStatus")


@dataclass(frozen=True)
class PredecessorReadback:
    """The direct prior attempt as read back by a future controlled adapter."""

    task_record_id: str
    attempt_record_id: str
    business_status: str

    def __post_init__(self) -> None:
        _require_identity(self.task_record_id, "predecessor task")
        _require_identity(self.attempt_record_id, "predecessor attempt")
        if not isinstance(self.business_status, str) or not self.business_status.strip():
            raise ValueError("predecessor business status is required")


@dataclass(frozen=True)
class ExportReadback:
    """Bitable facts supplied by a future controlled read-back adapter only."""

    task_record_id: str
    attempt_record_id: str
    review_record_id: str
    export_record_id: str
    business_status: str
    export_status: str
    p0_passed: bool
    feedback_class: str
    buyer_verdict: str
    redaction_passed: bool
    is_repair: bool = False
    predecessor: PredecessorReadback | None = None

    def __post_init__(self) -> None:
        _require_identity(self.task_record_id, "task")
        _require_identity(self.attempt_record_id, "attempt")
        _require_identity(self.review_record_id, "review")
        _require_identity(self.export_record_id, "export")
        if not isinstance(self.p0_passed, bool):
            raise ValueError("p0_passed must be a boolean read-back value")
        if not isinstance(self.redaction_passed, bool):
            raise ValueError("redaction_passed must be a boolean read-back value")
        if not isinstance(self.is_repair, bool):
            raise ValueError("is_repair must be a boolean read-back value")
        if self.predecessor is not None and not isinstance(
            self.predecessor, PredecessorReadback
        ):
            raise ValueError("predecessor must be a PredecessorReadback")

    def assert_eligible(self) -> None:
        if self.business_status != "accepted":
            raise ValueError("business status must be accepted before export")
        if self.export_status != "canonical_pending":
            raise ValueError("export status must be canonical_pending before export")
        if self.p0_passed is not True:
            raise ValueError("P0 must be passed before export")
        if not isinstance(self.feedback_class, str) or not self.feedback_class.strip():
            raise ValueError("feedback_class must be written before export")
        if self.buyer_verdict not in {"Gold", "Repair"}:
            raise ValueError("buyer verdict must be Gold or Repair before export")
        if self.redaction_passed is not True:
            raise ValueError("redaction must pass before export")
        if self.is_repair:
            if self.buyer_verdict != "Repair":
                raise ValueError("repair export requires Repair buyer verdict")
            _validate_revision_lineage(
                task_record_id=self.task_record_id,
                attempt_record_id=self.attempt_record_id,
                predecessor=self.predecessor,
            )
        else:
            if self.buyer_verdict != "Gold":
                raise ValueError("initial export requires Gold buyer verdict")
            if self.predecessor is not None:
                raise ValueError("non-repair export must not carry revision lineage")


@dataclass(frozen=True)
class FieldRule:
    """One approved logical-to-external field binding."""

    logical_field: str
    owner: FieldOwner
    external_field: str
    compass_export: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.owner, FieldOwner):
            raise ValueError("unknown field owner")
        if not self.logical_field.strip() or not self.external_field.strip():
            raise ValueError("field names must be non-empty")
        if not isinstance(self.compass_export, bool):
            raise ValueError("compass_export must be a boolean")


@dataclass(frozen=True)
class Transition:
    """A bounded Bitable transition anchored by task and attempt records."""

    task_record_id: str
    attempt_record_id: str
    from_state: str
    to_state: str
    predecessor: PredecessorReadback | None = None

    ALLOWED_STATES: ClassVar[Mapping[str, frozenset[str]]] = MappingProxyType(
        {
            "draft": frozenset({"assigned"}),
            "assigned": frozenset({"evidence_submitted"}),
            "evidence_submitted": frozenset({"p0_review"}),
            "p0_review": frozenset({"p0_failed", "buyer_review"}),
            "p0_failed": frozenset({"assigned"}),
            "buyer_review": frozenset(
                {"accepted", "repair_required", "rejected"}
            ),
        }
    )

    def __post_init__(self) -> None:
        self._require_identity(self.task_record_id, "task")
        self._require_identity(self.attempt_record_id, "attempt")
        if self.from_state == "repair_required":
            self._validate_repair_lineage()
            return
        if self.predecessor is not None:
            raise ValueError("revision lineage is only valid for a repair transition")
        if self.to_state not in self.ALLOWED_STATES.get(self.from_state, frozenset()):
            raise ValueError(
                f"state transition not allowed: {self.from_state} -> {self.to_state}"
            )

    @classmethod
    def advance(
        cls,
        task_record_id: str,
        attempt_record_id: str,
        *,
        from_state: str,
        to_state: str,
    ) -> "Transition":
        if from_state == "repair_required":
            raise ValueError("repair transitions require direct predecessor validation")
        return cls(
            task_record_id=task_record_id,
            attempt_record_id=attempt_record_id,
            from_state=from_state,
            to_state=to_state,
        )

    @classmethod
    def repair(
        cls,
        task_record_id: str,
        attempt_record_id: str,
        *,
        predecessor: PredecessorReadback | None,
    ) -> "Transition":
        return cls(
            task_record_id=task_record_id,
            attempt_record_id=attempt_record_id,
            from_state="repair_required",
            to_state="assigned",
            predecessor=predecessor,
        )

    def _validate_repair_lineage(self) -> None:
        if self.to_state != "assigned":
            raise ValueError("repair transition must create a new assigned attempt")
        _validate_revision_lineage(
            task_record_id=self.task_record_id,
            attempt_record_id=self.attempt_record_id,
            predecessor=self.predecessor,
        )

    @property
    def revision_of(self) -> str | None:
        """Derived lineage; callers cannot set a divergent bare revision ID."""

        return None if self.predecessor is None else self.predecessor.attempt_record_id

    @staticmethod
    def _require_identity(record_id: str | None, label: str) -> None:
        _require_identity(record_id, label)


def _validate_revision_lineage(
    *,
    task_record_id: str,
    attempt_record_id: str,
    predecessor: PredecessorReadback | None,
) -> None:
    if not isinstance(predecessor, PredecessorReadback):
        raise ValueError("repair export requires a PredecessorReadback")
    if predecessor.task_record_id != task_record_id:
        raise ValueError("repair predecessor must belong to the same task")
    if predecessor.business_status != "repair_required":
        raise ValueError("repair predecessor business status must be repair_required")
    if predecessor.attempt_record_id == attempt_record_id:
        raise ValueError("repair predecessor must not be the new attempt")


class FieldMap:
    """Immutable approved map for authorization and default-deny V5 v3 export."""

    __slots__ = ("_rules", "_by_logical_field")

    REQUIRED_NEW_TASK_FIELDS = frozenset(
        {
            "title",
            "task_type",
            "attachment_format_tags",
            "source_materials",
            "expected_output",
            "key_steps",
        }
    )
    REVIEW_STATUS_BY_FIELD = MappingProxyType(
        {
            "p0": ReviewStatus.P0_REVIEW,
            "p0_status": ReviewStatus.P0_REVIEW,
            "feedback_class": ReviewStatus.BUYER_REVIEW,
            "verdict": ReviewStatus.BUYER_REVIEW,
        }
    )
    V3_EXPORT_FIELDS = frozenset({"event_id", "evidence_hash", "manifest_hash"})
    COMPASS_EXCLUDED_FIELDS = frozenset(
        {
            "record_id",
            "bitable_record_id",
            "revision_of",
            "raw_conversation",
            "conversation_transcript",
            "conversation_screenshot",
            "screenshots",
            "raw_evidence",
            "evidence_pack",
            "attachments",
            "attachment",
            "share_reference",
            "platform_log_id",
            "credentials",
            "personal_identity",
            "contact_information",
            "bank_account",
            "buyer_identity",
            "reviewer_notes",
            "review_text",
            "review_raw_text",
        }
    )
    SENSITIVE_EXPORT_TOKENS = frozenset(
        {
            "identity",
            "contact",
            "bank",
            "account",
            "conversation",
            "screenshot",
            "attachment",
            "share",
            "credential",
            "review",
            "revision",
        }
    )

    def __init__(self, rules: Iterable[FieldRule]):
        immutable_rules = tuple(rules)
        self._validate_rules(immutable_rules)
        object.__setattr__(self, "_rules", immutable_rules)
        object.__setattr__(
            self,
            "_by_logical_field",
            MappingProxyType({rule.logical_field: rule for rule in immutable_rules}),
        )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("FieldMap is immutable after approval")

    @property
    def rules(self) -> tuple[FieldRule, ...]:
        return self._rules

    def authorize_write(
        self,
        *,
        actor: FieldOwner,
        record_id: str,
        updates: Mapping[str, Any],
        review_context: ReviewContext | None = None,
        task_record_id: str | None = None,
        attempt_record_id: str | None = None,
    ) -> None:
        """Reject a write before an adapter can pass it to Bitable."""

        Transition._require_identity(record_id, "Bitable")
        if not isinstance(actor, FieldOwner):
            raise PermissionError("unknown write actor")
        if actor in {FieldOwner.AUTOMATION, FieldOwner.OUTBOUND}:
            raise PermissionError("automation may not write Phase 3 owned fields")
        if not updates:
            raise ValueError("updates must not be empty")

        for logical_field in updates:
            rule = self._by_logical_field.get(logical_field)
            if rule is None:
                raise PermissionError(f"field is not in the approved map: {logical_field}")
            if rule.owner is FieldOwner.PROHIBITED:
                raise PermissionError(f"prohibited field cannot be written: {logical_field}")
            if rule.owner is not actor:
                raise PermissionError(
                    f"{actor.value} may not write {logical_field}; owned by {rule.owner.value}"
                )
            expected_status = self.REVIEW_STATUS_BY_FIELD.get(logical_field)
            if expected_status is not None:
                self._validate_review_context(
                    actor=actor,
                    record_id=record_id,
                    task_record_id=task_record_id,
                    attempt_record_id=attempt_record_id,
                    expected_status=expected_status,
                    review_context=review_context,
                )

    def compass_payload(self, values: Mapping[str, Any]) -> dict[str, Any]:
        """Emit only explicitly approved minimal v3 fields for Compass."""

        payload: dict[str, Any] = {}
        for rule in self._rules:
            if not rule.compass_export or rule.logical_field not in values:
                continue
            value = values[rule.logical_field]
            self._validate_v3_value(rule.logical_field, value)
            payload[rule.logical_field] = value
        return payload

    def v5_v3_payload(
        self,
        *,
        export_readback: ExportReadback,
        task_record_id: str,
        attempt_record_id: str,
        review_record_id: str,
        export_record_id: str,
        task_id: str,
        values: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Require eligible read-back anchors but never expose them to Compass."""

        if not isinstance(export_readback, ExportReadback):
            raise ValueError("v3 export requires an ExportReadback from the adapter")
        export_readback.assert_eligible()
        self._validate_export_anchor(
            task_record_id, export_readback.task_record_id, "task"
        )
        self._validate_export_anchor(
            attempt_record_id, export_readback.attempt_record_id, "attempt"
        )
        self._validate_export_anchor(
            review_record_id, export_readback.review_record_id, "review"
        )
        self._validate_export_anchor(
            export_record_id, export_readback.export_record_id, "export"
        )
        self._validate_derived_task_id(task_id, export_readback)
        return {"task_id": task_id, "fields": self.compass_payload(values)}

    def validate_new_task(self, submission: Mapping[str, Any]) -> dict[str, Any]:
        """Keep the task contract explicit; Evidence Pack remains additive proof."""

        missing = sorted(
            field
            for field in self.REQUIRED_NEW_TASK_FIELDS
            if not submission.get(field)
        )
        if missing:
            raise ValueError(f"missing new-task fields: {', '.join(missing)}")
        return dict(submission)

    @classmethod
    def _validate_rules(cls, rules: tuple[FieldRule, ...]) -> None:
        logical_fields: set[str] = set()
        external_fields: set[str] = set()
        for rule in rules:
            if not isinstance(rule, FieldRule):
                raise ValueError("field map rules must be FieldRule instances")
            if rule.logical_field in logical_fields:
                raise ValueError(f"duplicate logical field: {rule.logical_field}")
            if rule.external_field in external_fields:
                raise ValueError(f"duplicate external field: {rule.external_field}")
            if (
                rule.logical_field in cls.REVIEW_STATUS_BY_FIELD
                and rule.owner is not FieldOwner.INTERNAL
            ):
                raise ValueError(
                    f"{rule.logical_field} must be owned by an internal reviewer"
                )
            if rule.logical_field == "revision_of" and rule.owner is not FieldOwner.PROHIBITED:
                raise ValueError("revision_of must remain a prohibited lineage field")
            if rule.compass_export:
                cls._validate_v3_rule(rule)
            logical_fields.add(rule.logical_field)
            external_fields.add(rule.external_field)

    @classmethod
    def _validate_v3_rule(cls, rule: FieldRule) -> None:
        if cls._is_sensitive_export_field(rule.logical_field):
            raise ValueError(
                f"sensitive field cannot be exported to Compass: {rule.logical_field}"
            )
        if rule.logical_field not in cls.V3_EXPORT_FIELDS:
            raise ValueError(
                f"field is not an approved v3 export field: {rule.logical_field}"
            )
        if rule.owner is not FieldOwner.V5:
            raise ValueError("approved v3 export fields must be owned by V5")

    @classmethod
    def _is_sensitive_export_field(cls, logical_field: str) -> bool:
        normalized = logical_field.lower()
        return (
            normalized in cls.COMPASS_EXCLUDED_FIELDS
            or any(token in normalized for token in cls.SENSITIVE_EXPORT_TOKENS)
        )

    @staticmethod
    def _validate_v3_value(logical_field: str, value: Any) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{logical_field} must be a non-empty string")
        if logical_field == "event_id" and not EVENT_ID_PATTERN.fullmatch(value):
            raise ValueError("event_id must match the restricted evt_ identifier format")
        if logical_field in {"evidence_hash", "manifest_hash"} and not SHA256_PATTERN.fullmatch(
            value
        ):
            raise ValueError(f"{logical_field} must use a lowercase sha256 hash")

    @staticmethod
    def _validate_review_context(
        *,
        actor: FieldOwner,
        record_id: str,
        task_record_id: str | None,
        attempt_record_id: str | None,
        expected_status: ReviewStatus,
        review_context: ReviewContext | None,
    ) -> None:
        if actor is not FieldOwner.INTERNAL:
            raise PermissionError("review fields require an internal reviewer")
        if not isinstance(review_context, ReviewContext):
            raise PermissionError("review fields require a validated ReviewContext")
        if review_context.review_record_id != record_id:
            raise PermissionError("review fields require the matching review record")
        try:
            _require_identity(task_record_id, "task")
            _require_identity(attempt_record_id, "attempt")
        except ValueError as exc:
            raise PermissionError(
                "review fields require task and attempt identities from adapter read-back"
            ) from exc
        if review_context.task_record_id != task_record_id:
            raise PermissionError("review fields require the matching task record")
        if review_context.attempt_record_id != attempt_record_id:
            raise PermissionError("review fields require the matching attempt record")
        if review_context.review_status is not expected_status:
            raise PermissionError(
                f"review field requires review status {expected_status.value}"
            )

    @staticmethod
    def _validate_export_anchor(
        supplied_record_id: str,
        readback_record_id: str,
        label: str,
    ) -> None:
        _require_identity(supplied_record_id, label)
        if supplied_record_id != readback_record_id:
            raise ValueError(f"{label} record identity does not match ExportReadback")

    @staticmethod
    def _validate_derived_task_id(
        task_id: Any,
        export_readback: ExportReadback,
    ) -> None:
        """Keep Compass IDs distinct from Bitable identities.

        A future controlled adapter must create the stable, irreversible mapping.
        This offline contract only enforces its v3 format and non-identity boundary.
        """

        record_identities = (
            export_readback.task_record_id,
            export_readback.attempt_record_id,
            export_readback.review_record_id,
            export_readback.export_record_id,
        )
        if export_readback.is_repair:
            predecessor = export_readback.predecessor
            if isinstance(predecessor, PredecessorReadback):
                record_identities += (
                    predecessor.task_record_id,
                    predecessor.attempt_record_id,
                )
        if task_id in record_identities:
            raise ValueError("derived task_id must not equal a Bitable record identity")
        if not isinstance(task_id, str) or not V3_TASK_ID_PATTERN.fullmatch(task_id):
            raise ValueError(
                "derived task_id must match the restricted task_v3_ identifier format"
            )
