"""S2 亲笔提交→QC 反馈环 · 纯核心 TDD(design: 2026-06-11-fde-org-production-engine-design.md §B S2)."""
from services.fde_qc_feedback import parse_tutorial_md

SAMPLE_MD = """# FreeCad CLI建模教学

**领域tag**: 工程 / 工程建模

## 一、Instruction
面向 FreeCAD 1.0.2 的命令行建模与自动化验证场景。

## 二、Knowledge Points
- CAD 与实体建模的历史背景
- 实体建模的三种典型表示方法

## 三、Background Knowledge
CAD 的发展并不是从画得更漂亮开始的,而是从如何让计算机理解工程设计开始的。

## 四、Task示例
**输入**:FreeCAD 1.0.2 中文界面,Part Design,单位 mm。

**执行**:新建Body→XY面草图画φ40圆→Pad 40。

**结果/答案**:Volume≈56548.67 mm³。
"""


def test_parse_tutorial_md_extracts_buyer_format_sections():
    m = parse_tutorial_md(SAMPLE_MD)
    assert m["title"] == "FreeCad CLI建模教学"
    assert m["l1"] == "工程" and m["l2"] == "工程建模"
    assert "FreeCAD 1.0.2" in m["instruction"]
    assert m["knowledge_points"] == ["CAD 与实体建模的历史背景", "实体建模的三种典型表示方法"]
    assert m["background_knowledge"].startswith("CAD 的发展")
    assert "中文界面" in m["task_example"]["input"]
    assert "Pad 40" in m["task_example"]["steps"]
    assert "56548.67" in m["task_example"]["answer"]


def test_parse_tutorial_md_tolerates_loose_drafts():
    # 专家草稿常见变体:无 ## 前缀、领域行写法不同、步骤用「步骤」、缺段落=空值(交给 validate 报)
    loose = ("任务标题:RSI 诊断教案\n领域:工程/系统诊断\n"
             "一、Instruction\n诊断说明。\n二、Knowledge Points\n- 点1\n"
             "三、Background Knowledge\n正文。\n四、Task示例\n"
             "输入:现象描述\n步骤:看日志\n答案:根因X\n")
    m = parse_tutorial_md(loose)
    assert m["title"] == "RSI 诊断教案"
    assert m["l1"] == "工程"
    assert m["knowledge_points"] == ["点1"]
    assert m["task_example"]["answer"] == "根因X"


def test_parse_tutorial_md_missing_sections_yield_empty():
    m = parse_tutorial_md("随便一段话,没有结构。")
    assert m["background_knowledge"] == ""
    assert m["task_example"] == {"input": "", "steps": "", "answer": ""}


# ---------- Task 2: line2_score(assembler validate 报告 → 逐项 items) ----------
from services.fde_qc_feedback import line2_score  # noqa: E402


def test_line2_score_maps_violations_to_per_item_failures():
    report = {"violations": ["缺 instruction", "Background Knowledge 字数 612 不在 [1000,30000]"],
              "bk_chars": 612, "bk_digits": 3,
              "density_advisory": " [!] 数值/参数偏少(知识密度/可搜索风险·请专家自检)",
              "compliant": False}
    s = line2_score(report)
    assert s["overall_pass"] is False and s["veto_failed"] is True
    by_id = {i["id"]: i for i in s["items"]}
    assert by_id["complete"]["pass"] is False and "缺 instruction" in by_id["complete"]["reason"]
    assert by_id["bk_chars"]["pass"] is False and "612" in by_id["bk_chars"]["reason"]
    assert by_id["domain"]["pass"] is True          # 未违反的维度=pass(逐项可读)
    assert by_id["task_example"]["pass"] is True
    # 反AI/密度 advisory:透传给专家自检·不否决(买方 AI 检测是终判·我们只预警)
    assert by_id["density"]["pass"] is True and "自检" in by_id["density"]["reason"]
    assert 0.0 <= s["score"] < 1.0


def test_line2_score_compliant_passes_all():
    report = {"violations": [], "bk_chars": 1500, "bk_digits": 30,
              "density_advisory": "", "compliant": True}
    s = line2_score(report)
    assert s["overall_pass"] is True and s["veto_failed"] is False
    assert s["score"] == 1.0
    assert all(i["pass"] for i in s["items"])
    assert s["checklist_uid"] == "tutorial_v1"


# ---------- 真 assembler 集成冒烟(本地 skill·cloud vendored·无文件自动 skip) ----------
import os  # noqa: E402

import pytest  # noqa: E402

_ASSEMBLER = os.environ.get(
    "FDE_TUTORIAL_ASSEMBLER",
    os.path.expanduser("~/.claude/skills/knowledge-tutorial-assembler/scripts/assemble_tutorial.py"))


@pytest.mark.skipif(not os.path.exists(_ASSEMBLER), reason="assembler skill not present")
def test_line2_roundtrip_with_real_assembler_demo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("assemble_tutorial", _ASSEMBLER)
    at = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(at)
    md = at.assemble_md(at.DEMO)                  # 专家格式样稿(买方 docx 真例)
    s = line2_score(at.validate(parse_tutorial_md(md)))
    assert s["overall_pass"] is True              # 解析→校验 roundtrip 全过


# ---------- Task 3: verdict body + 飞书反馈格式化 ----------
from services.fde_qc_feedback import build_qc_verdict_body, format_feedback  # noqa: E402


def _scored(passing=False):
    return {"score": 0.6, "passed": 3, "total": 5, "veto_failed": not passing,
            "overall_pass": passing, "checklist_uid": "tutorial_v1",
            "items": [{"id": "complete", "pass": passing, "veto": True,
                       "reason": "ok" if passing else "缺 instruction"},
                      {"id": "density", "pass": True, "veto": False, "reason": "ok"}]}


def test_build_qc_verdict_body_is_deterministic_per_submission_version():
    b1 = build_qc_verdict_body("expert_t2_x", _scored(), "稿v1")
    b2 = build_qc_verdict_body("expert_t2_x", _scored(), "稿v1")
    b3 = build_qc_verdict_body("expert_t2_x", _scored(), "稿v2 改过了")
    assert b1["verdict_id"] == b2["verdict_id"]          # 同稿幂等(ingest 去重)
    assert b1["verdict_id"] != b3["verdict_id"]          # 改稿=新 verdict(每轮留痕)
    assert b1["verdict_id"].startswith("soul|qc|expert_t2_x|")
    assert b1["source"] == "soul" and b1["task_uid"] == "expert_t2_x"
    assert b1["overall_pass"] is False and isinstance(b1["items"], list)


def test_format_feedback_renders_per_item_pass_fail_reason():
    txt = format_feedback(build_qc_verdict_body("expert_t2_x", _scored(), "稿v1"))
    assert "已打回" in txt and "✗" in txt and "缺 instruction" in txt
    assert "✓" in txt and "density" in txt
    ok = format_feedback(build_qc_verdict_body("expert_t2_x", _scored(True), "稿v3"))
    assert "已通过" in ok


# ---------- Task 4: sync_submissions(编排:QC→verdict→report·fail-soft) ----------
from services.fde_qc_feedback import sync_submissions  # noqa: E402


class _FakeSubSource:
    def __init__(self, rows): self._rows = rows
    def read_submission_rows(self): return self._rows


def _subrow(**over):
    base = {"task_uid": "expert_t2_rsi_20260612", "line": "2", "level": "L2",
            "assignee": "chunxiao", "acceptance": "5部分齐", "submission": "# 教案\n正文"}
    base.update(over)
    return base


def test_sync_orders_verdict_before_report_and_summarizes():
    calls = []
    out = sync_submissions(
        _FakeSubSource([_subrow()]),
        qc_fn=lambda row, sub: {"score": 1.0, "overall_pass": True, "veto_failed": False,
                                "items": [], "checklist_uid": "tutorial_v1"},
        verdict_fn=lambda body: calls.append(("verdict", body["task_uid"])),
        report_fn=lambda uid, agent, sub: calls.append(("report", uid, agent)),
    )
    # 🔴 顺序契约:verdict 先 → /tasks 视图即 settled → soul-scorer 不会抢判 human 稿
    assert calls == [("verdict", "expert_t2_rsi_20260612"),
                     ("report", "expert_t2_rsi_20260612", "expert:chunxiao")]
    assert out["results"][0]["passed"] is True
    assert "已通过" in out["results"][0]["feedback"]


def test_sync_failsoft_and_skips_empty():
    rows = [_subrow(), _subrow(task_uid="", submission="x"),         # 缺 uid → skip
            _subrow(task_uid="expert_boom")]                          # qc 爆 → failed
    def qc(row, sub):
        if row["task_uid"] == "expert_boom":
            raise RuntimeError("judge down")
        return {"score": 0.5, "overall_pass": False, "veto_failed": True,
                "items": [{"id": "complete", "pass": False, "veto": True, "reason": "缺 KP"}],
                "checklist_uid": "tutorial_v1"}
    out = sync_submissions(_FakeSubSource(rows), qc_fn=qc,
                           verdict_fn=lambda b: None, report_fn=lambda u, a, s: None)
    assert [r["task_uid"] for r in out["results"]] == ["expert_t2_rsi_20260612"]
    assert out["results"][0]["passed"] is False and "缺 KP" in out["results"][0]["feedback"]
    assert out["skipped"] == [None] and out["failed"] == ["expert_boom"]


def test_sync_skips_submitted_row_with_empty_submission_exposing_uid():
    # 专家先置「已提交」后才粘稿:必须以可写回的 uid 暴露在 skipped(runner 据此回打回提示)
    out = sync_submissions(_FakeSubSource([_subrow(submission="")]),
                           qc_fn=lambda r, s: {}, verdict_fn=lambda b: None,
                           report_fn=lambda u, a, s: None)
    assert out["skipped"] == ["expert_t2_rsi_20260612"] and out["results"] == []


# ---------- review 修复回归(2026-06-12 三 finder 确认) ----------


def test_title_regex_ignores_h2_headings_and_falls_back():
    # ① 无 H1 草稿:## 节标题不得被当成标题;任务标题: fallback 生效
    no_h1 = "任务标题:真标题X\n## 一、Instruction\n说明。\n"
    assert parse_tutorial_md(no_h1)["title"] == "真标题X"
    only_h2 = "## 一、Instruction\n说明。\n"
    assert parse_tutorial_md(only_h2)["title"] == ""


def test_section_not_truncated_by_chinese_enumeration_lines():
    # ② Background 正文里的「一、历史背景」枚举行不得截断本节
    md = ("# 标题\n## 三、Background Knowledge\n"
          "正文开头。\n一、历史背景:很长。\n二、演化:更长。\n"
          "## 四、Task示例\n输入:x\n")
    bk = parse_tutorial_md(md)["background_knowledge"]
    assert "历史背景" in bk and "演化" in bk


def test_task_example_labels_are_line_anchored():
    # ③ 正文里行中的「执行:」不得劫持字段
    md = ("# 标题\n## 四、Task示例\n"
          "输入:在终端执行:python run.py 得到现象\n"
          "执行:看日志定位\n结果/答案:根因X\n")
    te = parse_tutorial_md(md)["task_example"]
    assert te["input"] == "在终端执行:python run.py 得到现象"
    assert te["steps"] == "看日志定位"
    assert te["answer"] == "根因X"


def test_line2_score_task_example_violation_does_not_fail_complete_dim():
    # ④ 'Task示例缺 输入' 只 fail task_example,不连坐 complete(needle 子串撞修复)
    report = {"violations": ["Task示例缺 输入"], "bk_chars": 1500, "bk_digits": 20,
              "density_advisory": "", "compliant": False}
    by_id = {i["id"]: i for i in line2_score(report)["items"]}
    assert by_id["task_example"]["pass"] is False
    assert by_id["complete"]["pass"] is True


# ---------- line_code: 业务线「2·教案」→ 路由编码「2」(RGDK schema 集成) ----------
from services.fde_qc_feedback import line_code as core_line_code  # noqa: E402
from services.fde_qc_feedback_runner import line_code  # noqa: E402


def test_line_code_extracts_leading_digit_from_rgdk_singleselect():
    # RGDK v06_派活 业务线 SingleSelect 选项 = 「1·出题 / 2·教案 / 3·评测」
    assert line_code("2·教案") == "2"
    assert line_code("1·出题") == "1"
    assert line_code("3·评测") == "3"


def test_line_code_tolerates_bare_digit_and_empty():
    assert line_code("2") == "2"        # 旧格式向后兼容
    assert line_code("") == ""
    assert line_code(None) == ""
    assert line_code("  2·教案  ") == "2"


def test_line_code_normalizes_doc_variants():
    # SOP↔引擎 reconcile(6/17):前台文档/旧 schema 用中文数字 + 全名,
    # 引擎必须容错归一,否则文档格式行进来 → 路由 fallback 错(Drift 1)。
    # 中文数字
    assert line_code("一") == "1"
    assert line_code("二") == "2"
    assert line_code("三") == "3"
    # references json 全名变体
    assert line_code("第一类-题目") == "1"
    assert line_code("第二类-知识教案") == "2"
    assert line_code("第三类-基准样例") == "3"
    # 含数字的全名(顺手)
    assert line_code("第2类") == "2"
    # 无法识别 → 原样返回(不臆造·让上游路由走默认+暴露)
    assert line_code("未知业务") == "未知业务"


def test_core_line_code_matches_runner_compatibility():
    assert core_line_code("2·教案") == line_code("2·教案")
    assert core_line_code("第3类-基准样例") == line_code("第3类-基准样例")
