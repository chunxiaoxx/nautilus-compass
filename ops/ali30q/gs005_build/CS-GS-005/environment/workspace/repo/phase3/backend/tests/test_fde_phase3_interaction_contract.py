from __future__ import annotations

import pytest

from services.fde_phase3_interaction_contract import InteractionEvidenceSubmission


def _payload(*, turns: int = 6) -> dict[str, object]:
    return {
        "tool_name": "豆包办公任务",
        "turn_count": turns,
        "round_feedback": [
            {
                "ordinal": ordinal,
                "rating": "like" if ordinal % 2 else "dislike",
                "issue_label": "correct" if ordinal % 2 else "incomplete",
                "reason": f"第{ordinal}轮回答给出了需要核对的具体业务信息。",
            }
            for ordinal in range(1, turns + 1)
        ],
        "dialogue_image_refs": ["file_token_001"],
        "trajectory_link": "https://example.invalid/trajectory/001",
        "log_id": "log_001",
        "attested_by_expert": True,
    }


def test_interaction_requires_six_complete_round_reviews() -> None:
    submission = InteractionEvidenceSubmission.from_mapping(_payload())

    assert submission.turn_count == 6
    assert tuple(item.ordinal for item in submission.round_feedback) == (1, 2, 3, 4, 5, 6)
    assert '"round_feedback"' in submission.canonical_json()


@pytest.mark.parametrize("turns", [0, 1, 5])
def test_interaction_rejects_fewer_than_six_reviewed_rounds(turns: int) -> None:
    with pytest.raises(ValueError):
        InteractionEvidenceSubmission.from_mapping(_payload(turns=turns))


def test_interaction_rejects_round_count_or_order_mismatch() -> None:
    count_mismatch = _payload()
    count_mismatch["turn_count"] = 7
    with pytest.raises(ValueError):
        InteractionEvidenceSubmission.from_mapping(count_mismatch)

    order_mismatch = _payload()
    rounds = order_mismatch["round_feedback"]
    assert isinstance(rounds, list)
    rounds[1]["ordinal"] = 3
    with pytest.raises(ValueError):
        InteractionEvidenceSubmission.from_mapping(order_mismatch)


def test_interaction_rejects_missing_or_vague_round_evaluation() -> None:
    missing = _payload()
    rounds = missing["round_feedback"]
    assert isinstance(rounds, list)
    del rounds[0]["rating"]
    with pytest.raises(ValueError):
        InteractionEvidenceSubmission.from_mapping(missing)

    vague = _payload()
    vague_rounds = vague["round_feedback"]
    assert isinstance(vague_rounds, list)
    vague_rounds[0]["reason"] = "不错"
    with pytest.raises(ValueError):
        InteractionEvidenceSubmission.from_mapping(vague)
