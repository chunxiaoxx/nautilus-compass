"""S3 交付+财务最小记账 · 纯核心 TDD.

design: docs/plans/2026-06-11-fde-org-production-engine-design.md §S3 +
        docs/FRESH_SESSION_PROMPT_20260614_rsi_fde_full_pipeline.md.

S3 = QC 过稿(状态=已通过)→ 组装买方格式入交付表 + settlement 最小记录。
🔴 只组装+记账,绝不改写专家正文。门:仅 verdict.overall_pass=True 的稿可交付。
🔴 交付样本标 provisional:正文须专家过买方 AI 检测后才是终品(charter §2)。
"""
from services.fde_delivery import (
    assemble_buyer_payload,
    build_settlement_record,
    estimate_token_cost,
    is_deliverable,
    sync_deliveries,
)

# ---- 真实平台一手素材样稿(line2·drift 检测·结构齐全) ----
SAMPLE_MD = """# persona drift BGE 检测 v2:从逢触必报到 score 阈值

**领域tag**: 工程 / agent 可靠性工程

## 一、Instruction
设计一个长 session persona drift 检测器,用 BGE 句向量对锚点打分,
v1 逢触必报误报率高,v2 切到 drift_score 阈值。目标是让模型理解
为何要从 max_neg_hit 触发切到 score 阈值。

## 二、Knowledge Points
- BGE 句向量与锚点余弦相似度
- 逢触必报 vs 阈值触发的误报权衡
- 11.5k 真实流量验证误报率

## 三、Background Knowledge
长 session 中 agent 会逐步偏离用户战略锚点,需要一个在线检测器。
v1 设计用 max_neg_hit ≥ 0.538 逢触必报,即任一负锚点命中即报警;
11.5k 条真实流量回放证明该口径 64.5% 是误报,导致用户 tune out。
v2 改为 drift_score < -0.07 阈值触发,alert 率从频繁降到 0.5%,
触发即高价值。核心权衡是召回与精度:逢触必报召回高但精度差,
阈值触发牺牲部分召回换精度,在长 session 场景下精度更重要,
因为误报的代价是用户彻底忽略告警。drift_score 由 alignment 与
deviation 两个 BGE 余弦分量合成,alignment 高、deviation 低则 score 高。

## 四、Task示例
**输入**:给定 25 个正锚点 + 35 个负锚点的 BGE 向量,一条 agent 输出。

**执行**:算输出对每个锚点的余弦,合成 drift_score,与 -0.07 比较。

**结果/答案**:score=-0.094 → 触发 alert;score=+0.021 → 中性不报。
"""


def _passed_row(**over):
    base = {"task_uid": "expert_t2_drift_detection_20260612", "line": "2",
            "level": "L2", "assignee": "chunxiao",
            "title": "persona drift BGE 检测 v2",
            "category": "", "domain": "agent 可靠性工程",
            "acceptance": "五部分齐全·BK 字数达标", "submission": SAMPLE_MD}
    base.update(over)
    return base


def _verdict(passing=True, score=1.0):
    return {"overall_pass": passing, "veto_failed": not passing, "score": score,
            "verdict_id": "soul|qc|x|abc", "source": "soul"}


# ---------- Task 1: is_deliverable 门(只过 verdict 的稿可交付) ----------

def test_is_deliverable_requires_passing_verdict():
    assert is_deliverable(_passed_row(), _verdict(passing=True)) is True
    assert is_deliverable(_passed_row(), _verdict(passing=False)) is False
    assert is_deliverable(_passed_row(), None) is False  # 无 verdict = 不交付


def test_is_deliverable_rejects_empty_submission():
    assert is_deliverable(_passed_row(submission="  "), _verdict(True)) is False


def test_is_deliverable_blocks_phase3_from_legacy_s3():
    row = _passed_row(
        workflow_version="phase3_interactive_v1",
        interaction_mode="doubao_office_task",
    )
    assert is_deliverable(row, _verdict(passing=True)) is False


# ---------- Task 2: assemble_buyer_payload(line2 → 买方 4 段结构列) ----------

def test_assemble_line2_extracts_buyer_columns():
    p = assemble_buyer_payload(_passed_row())
    assert p["line"] == "2"
    assert p["title"] == "persona drift BGE 检测 v2:从逢触必报到 score 阈值"
    assert p["l1"] == "工程"
    assert "BGE" in p["instruction"]
    assert "BGE 句向量" in p["knowledge_points"]          # 多个 KP 合并成文本
    assert p["background_knowledge"].startswith("长 session")
    assert "余弦" in p["task_example"]
    assert p["delivery_body_md"] == _passed_row()["submission"]  # 交付正文=专家原稿
    assert p["status"] == "provisional"                  # 待专家 AI 检测润色
    assert p["task_uid"] == "expert_t2_drift_detection_20260612"


def test_assemble_line1_passes_through_with_metadata():
    # line1 题目:最小路径=原稿+元数据透传(16列 fde-row-assembler 为后续片)
    row = _passed_row(line="1", level="L3", category="科技软件与 AI 工作流",
                      submission="题目:设计一个判定 grounded-retrieval 是否真外部 RSI 的系统任务...")
    p = assemble_buyer_payload(row)
    assert p["line"] == "1"
    assert p["category"] == "科技软件与 AI 工作流"
    assert p["delivery_body_md"].startswith("题目")
    assert p["status"] == "provisional"


# ---------- Task 3: estimate_token_cost(教案=无LLM≈0·诚实) ----------

def test_estimate_token_cost_zero_when_no_model_usage():
    c = estimate_token_cost(line="2", model_calls=None)
    assert c["token_cost_usd"] == 0.0
    assert c["model"] == "none"                           # 教案 QC=离线 validate


def test_estimate_token_cost_from_usage_is_transparent():
    c = estimate_token_cost(line="1", model_calls=[
        {"model": "doubao-seed-2.0-pro", "input_tokens": 1000, "output_tokens": 500}])
    assert c["token_cost_usd"] > 0.0
    assert c["input_tokens"] == 1000 and c["output_tokens"] == 500
    assert "doubao" in c["model"]


# ---------- Task 4: build_settlement_record(任务/专家/应付/token/状态) ----------

def test_build_settlement_record_shape():
    r = build_settlement_record(_passed_row(), _verdict(True, 1.0),
                                estimate_token_cost(line="2"))
    assert r["task_uid"] == "expert_t2_drift_detection_20260612"
    assert r["expert"] == "chunxiao"
    assert r["line"] == "2" and r["level"] == "L2"
    assert r["verdict_score"] == 1.0
    assert r["token_cost_usd"] == 0.0
    assert r["payable_status"] == "pending"              # 应付真专家·未结算
    assert r["payable_amount"] is None                   # 金额待人定价(最小记账不臆造)
    assert r["status"] == "delivered_provisional"


# ---------- Task 4b: 应付真算(wire fde_expert_rates·单价×工时) ----------

def test_build_settlement_computes_payable_from_rates_and_hours():
    row = _passed_row(assignee="平台专家#1", hours=8)
    rates = {"平台专家#1": 300.0}
    r = build_settlement_record(row, _verdict(True, 1.0),
                                estimate_token_cost(line="2"), rates=rates)
    assert r["payable_amount"] == 2400.0                 # 300 × 8
    assert r["payable_status"] == "computed"
    assert r["payable_rate"] == 300.0


def test_build_settlement_pending_when_expert_not_in_roster():
    row = _passed_row(assignee="不在名册的人", hours=8)
    r = build_settlement_record(row, _verdict(True, 1.0),
                                estimate_token_cost(line="2"),
                                rates={"平台专家#1": 300.0})
    assert r["payable_amount"] is None
    assert r["payable_status"] == "pending"
    assert r["payable_reason"] == "expert_not_in_roster"


def test_build_settlement_pending_when_hours_unknown():
    row = _passed_row(assignee="平台专家#1")              # 无 hours
    r = build_settlement_record(row, _verdict(True, 1.0),
                                estimate_token_cost(line="2"),
                                rates={"平台专家#1": 300.0})
    assert r["payable_amount"] is None
    assert r["payable_status"] == "pending"
    assert r["payable_reason"] == "hours_unknown"


def test_build_settlement_backward_compatible_no_rates():
    r = build_settlement_record(_passed_row(hours=8), _verdict(True, 1.0),
                                estimate_token_cost(line="2"))
    assert r["payable_amount"] is None                   # 无 rates 维持旧行为
    assert r["payable_status"] == "pending"


def test_sync_reads_expert_rates_and_records_computed_payable():
    src = _FakeSource([_passed_row(assignee="平台专家#1", hours=8)])
    src._rates = {"平台专家#1": 300.0}
    out = sync_deliveries(src, verdict_fn=lambda uid: _verdict(True, 1.0))
    assert out["delivered"] == ["expert_t2_drift_detection_20260612"]
    assert src.settlement_writes[0]["payable_amount"] == 2400.0
    assert src.settlement_writes[0]["payable_status"] == "computed"


# ---------- Task 5: sync_deliveries(编排·fail-soft·幂等) ----------

class _FakeSource:
    def __init__(self, rows, delivered=None):
        self._rows = rows
        self._delivered = set(delivered or ())
        self._rates = {}
        self.delivered_writes = []
        self.settlement_writes = []
        self.marked = []

    def read_passed_rows(self):
        return self._rows

    def read_expert_rates(self):
        return self._rates

    def already_delivered(self):
        return self._delivered

    def write_delivery(self, payload):
        self.delivered_writes.append(payload)
        return "rec_" + payload["task_uid"]

    def write_settlement(self, record):
        self.settlement_writes.append(record)

    def mark_delivered(self, task_uid):
        self.marked.append(task_uid)


def test_sync_delivers_passing_rows_and_records_settlement():
    src = _FakeSource([_passed_row()])
    out = sync_deliveries(src, verdict_fn=lambda uid: _verdict(True, 1.0))
    assert out["delivered"] == ["expert_t2_drift_detection_20260612"]
    assert len(src.delivered_writes) == 1
    assert len(src.settlement_writes) == 1
    assert src.marked == ["expert_t2_drift_detection_20260612"]
    # 交付与结算一一对应
    assert src.settlement_writes[0]["task_uid"] == src.delivered_writes[0]["task_uid"]


def test_sync_skips_unpassed_and_already_delivered():
    rows = [_passed_row(),
            _passed_row(task_uid="expert_t2_fail"),
            _passed_row(task_uid="expert_t2_done")]
    src = _FakeSource(rows, delivered={"expert_t2_done"})

    def vf(uid):
        if uid == "expert_t2_fail":
            return _verdict(passing=False)
        return _verdict(passing=True)

    out = sync_deliveries(src, verdict_fn=vf)
    assert out["delivered"] == ["expert_t2_drift_detection_20260612"]
    assert "expert_t2_fail" in out["skipped"]
    assert "expert_t2_done" in out["skipped"]            # 幂等:已交付不重复
    assert len(src.delivered_writes) == 1


def test_sync_does_not_release_phase3_row_through_legacy_s3():
    row = _passed_row(
        workflow_version="phase3_interactive_v1",
        interaction_mode="doubao_office_task",
    )
    src = _FakeSource([row])

    out = sync_deliveries(src, verdict_fn=lambda uid: _verdict(passing=True))

    assert out["delivered"] == []
    assert out["skipped"] == ["expert_t2_drift_detection_20260612"]
    assert src.delivered_writes == []
    assert src.settlement_writes == []
    assert src.marked == []


def test_sync_failsoft_one_bad_row_does_not_block_batch():
    rows = [_passed_row(task_uid="expert_boom"), _passed_row()]
    src = _FakeSource(rows)

    def vf(uid):
        if uid == "expert_boom":
            raise RuntimeError("verdict lookup down")
        return _verdict(True)

    out = sync_deliveries(src, verdict_fn=vf)
    assert out["delivered"] == ["expert_t2_drift_detection_20260612"]
    assert out["failed"] == ["expert_boom"]
