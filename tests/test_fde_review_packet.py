"""FDE expert-review packet generator.

`ops/fde_review_packet_build.build_packet` renders one expert-facing markdown
review packet per FDE task: the task prompt, every checklist item with the soul
一审 pass/fail marked (so the human can CHALLENGE the AI judge), veto items
flagged, and the structured 专家复核表单 whose filled output becomes the
source='expert' external verdict (the first non-self-referential PoI fuel).

The packet FORMAT was designed + user-approved via the data_004 worked example;
this generator replicates it across all 6 tasks. Reuses load_fde_tasks (DRY · no
re-invented loader). NO LLM (pure rendering).
"""
from __future__ import annotations

import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from ops import fde_review_packet_build as gen  # noqa: E402


def _checklist():
    return {"task_uid": "data_x", "level": "L2", "task": "复核餐厅噪音对评分的影响并推翻乐观方案。",
            "items": [
                {"id": "c1", "veto": False, "dimension": "task-specific",
                 "point": "揭示噪音对评分的负面影响", "expected": "具体数据对比"},
                {"id": "c2", "veto": False, "dimension": "task-specific",
                 "point": "引用访谈定性证据", "expected": "原文引用"},
                {"id": "c13", "veto": True, "dimension": "task-specific",
                 "point": "禁止编造附件不存在的数据", "expected": "引用可溯源"}]}


def _verdict():
    return {"task_uid": "data_x", "score": 0.6667, "passed": 2, "total": 3,
            "overall_pass": True, "veto_failed": False,
            "items": [{"id": "c1", "pass": True}, {"id": "c2", "pass": False},
                      {"id": "c13", "pass": True}]}


# ── RED 1 · packet carries task + every item with soul pass/fail marked ──────
def test_packet_renders_task_and_items_with_soul_marks():
    md = gen.build_packet("data_x", _checklist(), _verdict())

    assert "data_x" in md
    assert "复核餐厅噪音" in md           # the task prompt
    for cid in ("c1", "c2", "c13"):
        assert cid in md                  # every checklist item appears
    # soul 一审: c1 passed, c2 failed → opposing marks present
    assert "✅" in md and "❌" in md
    # the structured expert form → source='expert' verdict
    assert "通过" in md and "打回" in md
    assert "复核人" in md


# ── RED 2 · veto items are flagged (否决) so the expert weights them ─────────
def test_packet_flags_veto_items():
    md = gen.build_packet("data_x", _checklist(), _verdict())
    # c13 is a veto item; c1 is not — the packet must distinguish
    veto_line = [ln for ln in md.splitlines() if ln.strip().startswith("| c13")]
    assert veto_line, "c13 row should render"
    assert "否决" in veto_line[0]
    c1_line = [ln for ln in md.splitlines() if ln.strip().startswith("| c1 ")]
    assert c1_line and "否决" not in c1_line[0]


# ── RED 3 · soul mark matches the verdict (a passed item shows ✅, not ❌) ───
def test_soul_mark_matches_verdict():
    md = gen.build_packet("data_x", _checklist(), _verdict())
    c1_row = next(ln for ln in md.splitlines() if ln.strip().startswith("| c1 "))
    c2_row = next(ln for ln in md.splitlines() if ln.strip().startswith("| c2 "))
    assert "✅" in c1_row and "❌" not in c1_row   # c1 passed
    assert "❌" in c2_row and "✅" not in c2_row   # c2 failed


# ── RED 4 · deliverable present → packet lists the artifacts ─────────────────
def test_packet_lists_deliverable_when_present():
    md = gen.build_packet("data_x", _checklist(), _verdict(),
                          deliverable=["商业咨询报告.docx", "决策汇报演示.pptx"])
    assert "商业咨询报告.docx" in md
    assert "决策汇报演示.pptx" in md


# ── RED 5 · deliverable LOST → packet flags it, expert reviews task+checklist only
# (real case: data_001's product is gone — production didn't persist model_output
#  and there is no local _out dir; only its task+checklist+verdict survive.)
def test_packet_flags_lost_deliverable():
    md = gen.build_packet("data_001", _checklist(), _verdict(), deliverable=None)
    assert "交付物" in md and ("丢失" in md or "已丢失" in md)
    # still a usable packet: task + checklist review remain
    assert "复核餐厅噪音" in md
    assert "c1" in md


# ── RED 6 · build_all writes one packet per task + auto-detects deliverable dir
def test_build_all_writes_one_file_per_task(tmp_path, monkeypatch):
    tasks = [{"task_id": "data_001", "checklist": _checklist(), "verdict": _verdict()},
             {"task_id": "data_002", "checklist": _checklist(), "verdict": _verdict()}]
    monkeypatch.setattr(gen, "load_fde_tasks", lambda v, c, task_ids=None: tasks)
    # data_002 has a local deliverable dir; data_001 does not (lost)
    deliv_root = tmp_path / "vtf"
    (deliv_root / "_data002_out").mkdir(parents=True)
    (deliv_root / "_data002_out" / "报告.docx").write_text("x", encoding="utf-8")
    (deliv_root / "_data002_out" / "_model_output.txt").write_text("x", encoding="utf-8")

    out = tmp_path / "packets"
    written = gen.build_all("vdir", "cdir", str(out), deliverable_root=str(deliv_root))

    assert len(written) == 2
    p1 = (out / "复核包_data_001.md").read_text(encoding="utf-8")
    p2 = (out / "复核包_data_002.md").read_text(encoding="utf-8")
    assert "丢失" in p1                 # data_001 deliverable lost → flagged
    assert "报告.docx" in p2            # data_002 deliverable auto-detected
    assert "_model_output.txt" not in p2  # internal scratch file excluded
