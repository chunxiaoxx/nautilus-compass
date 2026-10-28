"""S1 派活+验收标准 · 纯编排核心 TDD(design: 2026-06-11-fde-org-production-engine-design.md S1)."""
import json
from services.fde_assignment import build_assignment_dispatch


def _row(**over):
    base = {
        "task_uid": "expert_t1_crossend_20260612",
        "title": "跨端体验一致性方案(二期 L2)",
        "line": "1",
        "category": "互联网与平台业务",
        "domain": "跨端产品架构",
        "level": "L2",
        "assignee": "chunxiao",
        "acceptance": "c1 方案≥2套(否决)\nc2 附Excel分析表\nc3 引用全部8附件",
    }
    base.update(over)
    return base


def test_build_dispatch_packs_human_spec_into_description_json():
    body = build_assignment_dispatch(_row())
    assert body["task_uid"] == "expert_t1_crossend_20260612"
    assert body["title"].startswith("跨端")
    spec = json.loads(body["description"])
    assert spec["producer"] == "human"
    assert spec["assignee"] == "chunxiao"
    assert spec["level"] == "L2"
    assert "c1" in spec["acceptance"]
    assert spec["assignee_source"] == "assignee"


def test_build_dispatch_prefers_open_id_over_empty_expert_id():
    body = build_assignment_dispatch(_row(expert_id="", open_id="open_id_901"))
    assert body is not None
    spec = json.loads(body["description"])
    assert spec["assignee"] == "open_id_901"
    assert spec["assignee_source"] == "open_id"


def test_build_dispatch_missing_required_returns_none():
    assert build_assignment_dispatch(_row(task_uid="")) is None
    assert build_assignment_dispatch(_row(assignee="")) is None
    assert build_assignment_dispatch(_row(acceptance="")) is None


from services.fde_assignment import sync_assignments


class _FakeSource:
    def __init__(self, rows): self._rows = rows
    def read_assignment_rows(self): return self._rows


def test_sync_dispatches_then_claims_for_named_expert():
    calls = []
    src = _FakeSource([_row()])
    out = sync_assignments(
        src,
        dispatch_fn=lambda b: calls.append(("dispatch", b["task_uid"])),
        claim_fn=lambda uid, agent: calls.append(("claim", uid, agent)),
    )
    assert calls == [
        ("dispatch", "expert_t1_crossend_20260612"),
        ("claim", "expert_t1_crossend_20260612", "expert:chunxiao"),
    ]
    assert out["assigned"] == ["expert_t1_crossend_20260612"]


def test_sync_skips_invalid_and_already_assigned_failsoft():
    rows = [_row(), _row(task_uid="expert_t2_dup", acceptance=""),
            _row(task_uid="expert_t1_crossend_20260612")]
    boom = _row(task_uid="expert_t9_boom")
    rows.append(boom)
    def _claim(uid, agent):
        if uid == "expert_t9_boom":
            raise RuntimeError("409 already claimed")
    out = sync_assignments(_FakeSource(rows), dispatch_fn=lambda b: None, claim_fn=_claim,
                           already_assigned={"expert_known"})
    assert out["assigned"] == ["expert_t1_crossend_20260612"]
    assert "expert_t2_dup" in out["skipped"]
    assert out["lost_to_agent"] == ["expert_t9_boom"]
