"""Pure public-field contract for an authenticated Phase 3 interaction page."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import json


_PUBLIC_INTERACTION_FIELDS = frozenset(
    {
        "tool_name",
        "turn_count",
        "round_feedback",
        "dialogue_image_refs",
        "trajectory_link",
        "log_id",
        "attested_by_expert",
    }
)
_PUBLIC_ROUND_FIELDS = frozenset({"ordinal", "rating", "issue_label", "reason"})
_ALLOWED_RATINGS = frozenset({"like", "dislike"})


@dataclass(frozen=True)
class RoundFeedback:
    """One required human evaluation bound to one interaction round."""

    ordinal: int
    rating: str
    issue_label: str
    reason: str

    def __post_init__(self) -> None:
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int) or self.ordinal < 1:
            raise ValueError("round ordinal must be a positive integer")
        if self.rating not in _ALLOWED_RATINGS:
            raise ValueError("round rating must be like or dislike")
        _require_compact_public_value(self.issue_label, "round issue_label", maximum=80)
        _require_compact_public_value(self.reason, "round reason", maximum=1000)
        if len(self.reason) < 6:
            raise ValueError("round reason must be specific")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "RoundFeedback":
        if set(payload) != _PUBLIC_ROUND_FIELDS:
            raise ValueError("round feedback fields are not approved")
        return cls(
            ordinal=payload["ordinal"],  # type: ignore[arg-type]
            rating=payload["rating"],  # type: ignore[arg-type]
            issue_label=payload["issue_label"],  # type: ignore[arg-type]
            reason=payload["reason"],  # type: ignore[arg-type]
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "ordinal": self.ordinal,
            "rating": self.rating,
            "issue_label": self.issue_label,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class InteractionEvidenceSubmission:
    """The only interaction fields accepted from a Mentor continuation page."""

    tool_name: str
    turn_count: int
    round_feedback: tuple[RoundFeedback, ...]
    dialogue_image_refs: tuple[str, ...]
    trajectory_link: str
    log_id: str
    attested_by_expert: bool

    def __post_init__(self) -> None:
        _require_compact_public_value(self.tool_name, "tool_name", maximum=80)
        if self.tool_name != "豆包办公任务":
            raise ValueError("tool_name must be 豆包办公任务")
        if isinstance(self.turn_count, bool) or not isinstance(self.turn_count, int):
            raise ValueError("turn_count must be an integer")
        if self.turn_count < 6:
            raise ValueError("turn_count must be at least six")
        if not isinstance(self.round_feedback, tuple) or len(self.round_feedback) < 6:
            raise ValueError("round_feedback must contain at least six rounds")
        if any(not isinstance(item, RoundFeedback) for item in self.round_feedback):
            raise ValueError("round_feedback must contain RoundFeedback values")
        if len(self.round_feedback) != self.turn_count:
            raise ValueError("turn_count must match round_feedback")
        ordinals = tuple(item.ordinal for item in self.round_feedback)
        if ordinals != tuple(range(1, self.turn_count + 1)):
            raise ValueError("round_feedback ordinals must be consecutive")
        if not isinstance(self.dialogue_image_refs, tuple) or not self.dialogue_image_refs:
            raise ValueError("dialogue_image_refs must be a non-empty tuple")
        for image_ref in self.dialogue_image_refs:
            _require_compact_public_value(
                image_ref,
                "dialogue_image_refs entry",
                maximum=512,
            )
        if len(set(self.dialogue_image_refs)) != len(self.dialogue_image_refs):
            raise ValueError("dialogue_image_refs must not contain duplicates")
        _require_compact_public_value(self.trajectory_link, "trajectory_link", maximum=2048)
        _require_compact_public_value(self.log_id, "log_id", maximum=512)
        if not isinstance(self.attested_by_expert, bool):
            raise ValueError("attested_by_expert must be a boolean")
        if not self.attested_by_expert:
            raise ValueError("attested_by_expert must be true")

    @classmethod
    def from_mapping(cls, payload: Mapping[str, object]) -> "InteractionEvidenceSubmission":
        if set(payload) != _PUBLIC_INTERACTION_FIELDS:
            raise ValueError("interaction payload fields are not approved")
        raw_image_refs = payload["dialogue_image_refs"]
        if isinstance(raw_image_refs, (str, bytes)) or not isinstance(raw_image_refs, Sequence):
            raise ValueError("dialogue_image_refs must be an array")
        raw_round_feedback = payload["round_feedback"]
        if isinstance(raw_round_feedback, (str, bytes)) or not isinstance(
            raw_round_feedback, Sequence
        ):
            raise ValueError("round_feedback must be an array")
        rounds: list[RoundFeedback] = []
        for raw_round in raw_round_feedback:
            if not isinstance(raw_round, Mapping):
                raise ValueError("round_feedback entries must be objects")
            rounds.append(RoundFeedback.from_mapping(raw_round))
        return cls(
            tool_name=payload["tool_name"],  # type: ignore[arg-type]
            turn_count=payload["turn_count"],  # type: ignore[arg-type]
            round_feedback=tuple(rounds),
            dialogue_image_refs=tuple(raw_image_refs),  # type: ignore[arg-type]
            trajectory_link=payload["trajectory_link"],  # type: ignore[arg-type]
            log_id=payload["log_id"],  # type: ignore[arg-type]
            attested_by_expert=payload["attested_by_expert"],  # type: ignore[arg-type]
        )

    def canonical_json(self) -> str:
        """Stable private material for a server-derived idempotency key."""

        return json.dumps(
            {
                "attested_by_expert": self.attested_by_expert,
                "dialogue_image_refs": self.dialogue_image_refs,
                "log_id": self.log_id,
                "round_feedback": [item.to_payload() for item in self.round_feedback],
                "tool_name": self.tool_name,
                "trajectory_link": self.trajectory_link,
                "turn_count": self.turn_count,
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )


@dataclass(frozen=True)
class MentorInteractionPage:
    """Safe page configuration, intentionally without any Bitable identity."""

    action: str = "submit_interaction_evidence"
    allowed_tool: str = "豆包办公任务"
    minimum_turn_count: int = 6
    required_fields: tuple[str, ...] = (
        "round_feedback",
        "dialogue_image_refs",
        "trajectory_link",
        "log_id",
        "attested_by_expert",
    )

    def __post_init__(self) -> None:
        if self.action != "submit_interaction_evidence":
            raise ValueError("action must be submit_interaction_evidence")
        if self.allowed_tool != "豆包办公任务":
            raise ValueError("allowed_tool must be 豆包办公任务")
        if self.minimum_turn_count != 6:
            raise ValueError("minimum_turn_count must be 6")
        if self.required_fields != (
            "round_feedback",
            "dialogue_image_refs",
            "trajectory_link",
            "log_id",
            "attested_by_expert",
        ):
            raise ValueError("required_fields must match the public interaction contract")

    def to_payload(self) -> dict[str, object]:
        return {
            "action": self.action,
            "allowed_tool": self.allowed_tool,
            "minimum_turn_count": self.minimum_turn_count,
            "required_fields": list(self.required_fields),
        }


@dataclass(frozen=True)
class InteractionSubmissionResult:
    """Sanitized result after internal continuation and Bitable handling."""

    outcome: str

    def __post_init__(self) -> None:
        if self.outcome not in {"submitted", "already_submitted"}:
            raise ValueError("outcome must be submitted or already_submitted")


def _require_compact_public_value(value: object, label: str, *, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(character.isspace() and character not in {" ", "\t"} for character in value)
    ):
        raise ValueError(f"{label} must be a compact string")
