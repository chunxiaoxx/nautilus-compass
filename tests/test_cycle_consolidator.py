"""TDD for cycle_consolidator.py · 纯解析/分类 + 注入 I/O。用真 cycle-auto 样本格式。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import cycle_consolidator as cc  # noqa: E402


# 真样本(2026-06-22 抽自 T4 cycle-auto):learn 空 = 噪声
NOISE_MD = """---
name: ingest_20260523_013229_48990
type: ingest
agent_id: nautilus-prime-001
tags: ['drift:red']
drift: red
---
think: 停止辩论，直接认领一个 bounties，让真实反馈打破 85% stagnation。
learn:
evolve: 停止辩论，直接认领一个 bounties。
"""

# 构造 learn 非空 = 有价值教训
VALUABLE_MD = """---
name: ingest_x
agent_id: nautilus-prime-001
drift: green
---
think: 调 pf_task_detail 看交付。
learn: pf_score_bounty 必须在 pf_task_detail 之后调,否则拿不到 deliverable 上下文导致评分为空。
evolve: 先 detail 再 score。
"""


def test_parse_extracts_fields():
    p = cc.parse_cycle_md(NOISE_MD)
    assert p["learn"] == ""
    assert "停止辩论" in p["think"]
    assert p["agent_id"] == "nautilus-prime-001"
    assert p["drift"] == "red"


def test_parse_valuable_learn():
    p = cc.parse_cycle_md(VALUABLE_MD)
    assert "pf_score_bounty" in p["learn"]
    assert "deliverable" in p["learn"]


def test_classify_empty_learn_is_noise():
    assert cc.classify(cc.parse_cycle_md(NOISE_MD)) == "noise"


def test_classify_substantive_learn_is_valuable():
    assert cc.classify(cc.parse_cycle_md(VALUABLE_MD)) == "valuable"


def test_classify_short_learn_is_noise():
    assert cc.classify({"learn": "ok"}) == "noise"  # < MIN_LEARN_LEN


def test_lesson_to_capsule_body():
    b = cc.lesson_to_capsule_body(cc.parse_cycle_md(VALUABLE_MD), "cycle-123-auto")
    assert "pf_score_bounty" in b["content"]
    assert b["project"] == "distilled-capsules"
    assert "cycle-distilled" in b["tags"]
    assert len(b["description"]) <= 200


def test_consolidate_routes_and_counts():
    written, archived = [], []
    entries = [
        ("cycle-1-auto", NOISE_MD),
        ("cycle-2-auto", VALUABLE_MD),
        ("cycle-3-auto", NOISE_MD),
    ]
    stats = cc.consolidate_cycles(
        entries, lambda b: written.append(b), lambda d: archived.append(d)
    )
    assert stats["valuable"] == 1
    assert stats["noise"] == 2
    assert stats["distilled"] == 1
    assert stats["archived"] == 2
    assert archived == ["cycle-1-auto", "cycle-3-auto"]
    assert "pf_score_bounty" in written[0]["content"]


def test_dry_run_no_side_effects():
    written, archived = [], []
    entries = [("cycle-1-auto", NOISE_MD), ("cycle-2-auto", VALUABLE_MD)]
    stats = cc.consolidate_cycles(
        entries, lambda b: written.append(b), lambda d: archived.append(d), dry_run=True
    )
    assert stats["valuable"] == 1 and stats["noise"] == 1
    assert stats["distilled"] == 0 and stats["archived"] == 0
    assert written == [] and archived == []
