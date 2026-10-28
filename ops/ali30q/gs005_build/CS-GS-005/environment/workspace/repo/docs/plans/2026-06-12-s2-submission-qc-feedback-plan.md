# S2 亲笔提交→QC 反馈环(human-author 路径)Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 专家在飞书派活表「提交内容」粘亲笔稿(状态=已提交)→ 平台 poller 拉提交 → QC 判(线1=checklist_scorer·线2=knowledge-tutorial-assembler 完整性+反AI校验)→ 逐项 pass/fail+reason 写回飞书「QC反馈」+ 状态(已通过/已打回)→ 专家按 reason 改 → 再提交 → 过。全程不碰 CLI。

**Architecture:** 零后端 API 改动——复用现成 `/api/platform/fde/report`(claimed→produced·持久化 output)+ `/api/platform/fde/verdict`(verdict_id 幂等)。新增:① 纯核心 `services/fde_qc_feedback.py`(md 解析+line2 判分映射+verdict body+反馈格式化+sync 编排·本地 TDD)② effect runner `services/fde_qc_feedback_runner.py`(镜像 `fde_assignment_runner` 模式·读飞书「已提交」→QC→写回)③ 飞书派活表加 2 列+2 状态值(一次性 bootstrap·本地金库凭据)④ cloud 部署并进现有 `fde-assignment` timer。设计来源:`2026-06-11-fde-org-production-engine-design.md` §B S2。

**Tech Stack:** Python 3.10(cloud)/3.13(本地)· 现成端点 report/verdict(无需 platform key)· 飞书 bitable v1(凭据 `~/.claude/.cache/.fde_api_secrets.env`·cloud `~/.fde_feishu.env`)· 线2 判分=vendored `assemble_tutorial.validate`(skill 脚本·importlib 加载·同 scorer 加载 harness 模式)· 线1 判分=`services.fde_scorer_runner.make_soul_score_fn`(cloud 已部署)。

**🔴 关键 gotcha(实证·设计依据):**
1. **verdict-join 遮蔽反着用**(`api/fde_dispatch.py:157`):QC 必须**先 POST /verdict 再 POST /report**。verdict 先在 → `/tasks` 视图报 settled → soul-scorer 的 `?status=produced` + `verdict is None` 过滤器跳过 human 行 → 防止它用 T1 checklist judge 误判教案(双判污染)。
2. **`_http` 捕 HTTPError 返 envelope**(S1 C1 教训):4xx 带 JSON body 要解析返回,不能让网络层异常误判成 QC 失败。
3. **cloud = fork(soul-audit-increment1)只 scp 不 pull**;本地 master main.py 不可 import——S2 纯新模块不碰 main.py,无此风险。
4. **人是作者红线**:QC 反馈=指出哪不达标(reason),绝不代写正文。线2 反 AI:assembler validate 的 density advisory 原样透传给专家自检。
5. **防抢单**:S2 只读「已提交」行,不碰 claim(S1 已 expert: 占座)。report 的 agent_id=expert:<assignee>(人产出·非 agent 冒充)。
6. 本地测试:`cd phase3/backend && python -m pytest`(Windows 用 `python`)。

---

### Task 1: 纯核心 · `parse_tutorial_md`(飞书提交 md → material dict)

**Files:**
- Create: `phase3/backend/services/fde_qc_feedback.py`
- Test: `phase3/backend/tests/test_fde_qc_feedback.py`

**Step 1: 写失败测试**

```python
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
```

**Step 2: 跑测试确认失败**

Run: `cd phase3/backend && python -m pytest tests/test_fde_qc_feedback.py -v`
Expected: FAIL `ModuleNotFoundError: services.fde_qc_feedback`

**Step 3: 最小实现**

```python
"""S2 亲笔提交→QC 反馈环 · 纯核心.

turf:平台 own 提交轮询+反馈写回;QC 判分=soul lane 现成件(线1 checklist_scorer·
线2 assemble_tutorial.validate·均 effect 注入);引擎=现成 report/verdict API(零改动)。
🔴 人是作者:本模块只判+给 reason,绝不生成/改写稿件正文。
🔴 顺序契约:verdict 先于 report POST(verdict-join 遮蔽反用·防 soul-scorer 双判)。
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Callable

_SEC = {
    "instruction": r"一[、.]\s*Instruction",
    "knowledge_points": r"二[、.]\s*Knowledge\s*Points",
    "background_knowledge": r"三[、.]\s*Background\s*Knowledge",
    "task_example": r"四[、.]\s*Task\s*示例",
}


def _section(text: str, pat: str) -> str:
    """取「标题行之后到下一节标题/文末」的正文。"""
    m = re.search(r"^[#\s]*(?:" + pat + r")\s*$(.*?)(?=^[#\s]*(?:一|二|三|四)[、.]|\Z)",
                  text, re.M | re.S | re.I)
    return m.group(1).strip() if m else ""


def parse_tutorial_md(text: str) -> dict:
    """飞书「提交内容」md/草稿 → 买方教案 material dict(缺段=空值·交 validate 报)。"""
    text = text or ""
    title = ""
    m = re.search(r"^#\s*(.+)$", text, re.M)
    if m:
        title = m.group(1).strip()
    else:
        m = re.search(r"^(?:任务)?标题[::]\s*(.+)$", text, re.M)
        title = m.group(1).strip() if m else ""
    l1 = l2 = ""
    m = re.search(r"^\**领域(?:tag)?\**[::]\**\s*([^/\n]+?)\s*/\s*(.+?)\**\s*$", text, re.M)
    if m:
        l1, l2 = m.group(1).strip(), m.group(2).strip()
    kp_raw = _section(text, _SEC["knowledge_points"])
    kps = [ln.lstrip("-•* ").strip() for ln in kp_raw.splitlines()
           if ln.strip().lstrip("-•* ").strip()]
    te_raw = _section(text, _SEC["task_example"])

    def _te(label_pat: str) -> str:
        m2 = re.search(r"\**(?:" + label_pat + r")\**[::]\**\s*(.+?)(?=\n\s*\**(?:输入|执行|步骤|结果|答案)|\Z)",
                       te_raw, re.S)
        return m2.group(1).strip() if m2 else ""

    return {
        "title": title,
        "l1": l1, "l2": l2,
        "instruction": _section(text, _SEC["instruction"]),
        "knowledge_points": kps,
        "background_knowledge": _section(text, _SEC["background_knowledge"]),
        "task_example": {"input": _te("输入"), "steps": _te("执行|步骤"),
                         "answer": _te(r"结果/?答案|答案|结果")},
    }
```

**Step 4: 跑测试确认通过**

Run: `cd phase3/backend && python -m pytest tests/test_fde_qc_feedback.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add phase3/backend/services/fde_qc_feedback.py phase3/backend/tests/test_fde_qc_feedback.py
git commit -m "feat(s2): parse_tutorial_md 飞书亲笔稿→买方教案 material dict(TDD)"
```

---

### Task 2: 纯核心 · `line2_score`(assembler validate 报告 → 逐项 items + scored)

**Files:**
- Modify: `phase3/backend/services/fde_qc_feedback.py`(追加)
- Test: `phase3/backend/tests/test_fde_qc_feedback.py`(追加)

**Step 1: 追加失败测试**

```python
from services.fde_qc_feedback import line2_score


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
```

**Step 2: 跑测试确认失败**

Run: `cd phase3/backend && python -m pytest tests/test_fde_qc_feedback.py -v`
Expected: 新 2 个 FAIL(ImportError)

**Step 3: 追加最小实现**

```python
# 线2 教案 QC 维度(validate() violations 子串 → 维度归属·与 assemble_tutorial.py 文案锚定)
_L2_DIMS = (
    ("complete", "五部分齐全(标题/领域/Instruction/KP/Background)", ("缺 ",)),
    ("domain", "领域一级 ∈ {金融,法律,医疗,工程,农业,其他}", ("领域一级非法",)),
    ("bk_chars", "Background Knowledge 字数 ∈ [1000,30000]", ("字数",)),
    ("task_example", "Task示例含 输入+执行+结果/答案", ("Task示例缺",)),
)


def line2_score(report: dict) -> dict:
    """assemble_tutorial.validate() 报告 → checklist_scorer 同形 scored dict。

    买方红线维度(完整性/字数/领域/示例)任一违反 = veto(打回);
    density advisory 只预警不否决(终判=买方 AI 检测·专家自检)。
    """
    violations = report.get("violations") or []
    items = []
    for dim_id, text, needles in _L2_DIMS:
        hits = [v for v in violations if any(n in v for n in needles)]
        items.append({"id": dim_id, "text": text, "veto": True,
                      "pass": not hits, "reason": "; ".join(hits) if hits else "ok"})
    advisory = (report.get("density_advisory") or "").strip()
    items.append({"id": "density", "text": "知识密度/反AI自检(advisory)", "veto": False,
                  "pass": True,
                  "reason": advisory if advisory else
                  f"ok(数值数={report.get('bk_digits', 0)}·终判=买方AI检测·请专家自检)"})
    passed = sum(1 for i in items if i["pass"])
    compliant = bool(report.get("compliant"))
    return {"score": passed / len(items), "passed": passed, "total": len(items),
            "veto_failed": not compliant, "overall_pass": compliant,
            "items": items, "checklist_uid": "tutorial_v1"}
```

**Step 4: 跑测试确认通过**

Run: `cd phase3/backend && python -m pytest tests/test_fde_qc_feedback.py -v`
Expected: 5 passed

**Step 5(可选·有 skill 文件时):真 assembler 集成冒烟**

追加(本地有 skill·cloud 用 vendored 副本·无文件自动 skip):

```python
import os
import pytest

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
```

Run: `cd phase3/backend && python -m pytest tests/test_fde_qc_feedback.py -v`
Expected: 6 passed

**Step 6: Commit**

```bash
git add phase3/backend/services/fde_qc_feedback.py phase3/backend/tests/test_fde_qc_feedback.py
git commit -m "feat(s2): line2_score validate报告→逐项items(红线veto·advisory透传·TDD+真assembler冒烟)"
```

---

### Task 3: 纯核心 · `build_qc_verdict_body` + `format_feedback`

**Files:**
- Modify: `phase3/backend/services/fde_qc_feedback.py`(追加)
- Test: `phase3/backend/tests/test_fde_qc_feedback.py`(追加)

**Step 1: 追加失败测试**

```python
from services.fde_qc_feedback import build_qc_verdict_body, format_feedback


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
```

**Step 2: 跑测试确认失败** → Expected: 新 2 FAIL(ImportError)

**Step 3: 追加最小实现**

```python
def _sub_hash(submission: str) -> str:
    return hashlib.sha1((submission or "").strip().encode("utf-8")).hexdigest()[:10]


def build_qc_verdict_body(task_uid: str, scored: dict, submission: str) -> dict:
    """scored → POST /verdict body。verdict_id 含稿 hash:同稿幂等·改稿新 verdict。

    (镜像 services.fde_scorer_poll.build_verdict_body·区别=按提交版本留痕)
    """
    return {
        "verdict_id": f"soul|qc|{task_uid}|{_sub_hash(submission)}",
        "task_uid": task_uid,
        "source": "soul",
        "checklist_uid": scored.get("checklist_uid") or "default",
        "overall_pass": bool(scored.get("overall_pass")),
        "veto_failed": bool(scored.get("veto_failed")),
        "score": float(scored.get("score", 0.0)),
        "items": scored.get("items") or [],
    }


def format_feedback(body: dict) -> str:
    """verdict body → 飞书「QC反馈」逐项文本(专家可读·指出哪不达标·不代写)。"""
    items = body.get("items") or []
    passed = sum(1 for i in items if i.get("pass"))
    head = ("✅ 已通过" if body.get("overall_pass") else "❌ 已打回") + \
        f" · {passed}/{len(items)} 项过 · QC批次 {body['verdict_id'].rsplit('|', 1)[-1]}"
    lines = [head]
    for i in items:
        mark = "✓" if i.get("pass") else "✗"
        veto = "(红线)" if i.get("veto") and not i.get("pass") else ""
        lines.append(f"{mark} {i.get('id')}{veto}: {str(i.get('reason') or '')[:160]}")
    if not body.get("overall_pass"):
        lines.append("→ 请按 ✗ 项修改后将状态改回「已提交」(正文须专家亲笔·QC不代写)")
    return "\n".join(lines)[:1900]
```

**Step 4: 跑全部测试确认通过** → Expected: 8 passed

**Step 5: Commit**

```bash
git add phase3/backend/services/fde_qc_feedback.py phase3/backend/tests/test_fde_qc_feedback.py
git commit -m "feat(s2): qc verdict body(稿hash留痕幂等)+飞书逐项反馈格式化(TDD)"
```

---

### Task 4: 纯核心 · `sync_submissions`(编排:QC→verdict→report·fail-soft)

**Files:**
- Modify: `phase3/backend/services/fde_qc_feedback.py`(追加)
- Test: `phase3/backend/tests/test_fde_qc_feedback.py`(追加)

**Step 1: 追加失败测试**

```python
from services.fde_qc_feedback import sync_submissions


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
```

**Step 2: 跑测试确认失败** → Expected: 新 2 FAIL(ImportError)

**Step 3: 追加最小实现**

```python
def sync_submissions(
    source,
    qc_fn: Callable[[dict, str], dict],
    verdict_fn: Callable[[dict], object],
    report_fn: Callable[[str, str, str], object],
) -> dict:
    """读「已提交」行 → QC → verdict → report → 反馈汇总。fail-soft 单行不拖批。

    顺序契约(🔴):verdict_fn 必须先于 report_fn —— verdict-join 遮蔽反用,
    使 soul-scorer 的 produced+无verdict 过滤器跳过 human 稿(防 T1 checklist 双判)。
    Returns {"results": [{task_uid, passed, feedback}], "skipped": [...], "failed": [...]}
    """
    results, skipped, failed = [], [], []
    for row in source.read_submission_rows():
        uid = str(row.get("task_uid") or "").strip() or None
        sub = str(row.get("submission") or "").strip()
        if not uid or not sub:
            skipped.append(uid)
            continue
        try:
            scored = qc_fn(row, sub)
            body = build_qc_verdict_body(uid, scored, sub)
            verdict_fn(body)
            report_fn(uid, "expert:" + str(row.get("assignee") or "").strip(), sub)
        except Exception:  # noqa: BLE001 — fail-soft·runner 日志暴露
            failed.append(uid)
            continue
        results.append({"task_uid": uid, "passed": bool(body["overall_pass"]),
                        "feedback": format_feedback(body)})
    return {"results": results, "skipped": skipped, "failed": failed}
```

**Step 4: 跑全部测试确认通过** → Expected: 10 passed

**Step 5: 回归既有 FDE 测试不碰坏**

Run: `cd phase3/backend && python -m pytest tests/test_fde_assignment.py tests/test_fde_scorer_poll.py tests/test_fde_poller.py tests/test_fde_dispatch_v1.py -v`
Expected: 全 passed(没动它们·确认即可)

**Step 6: Commit**

```bash
git add phase3/backend/services/fde_qc_feedback.py phase3/backend/tests/test_fde_qc_feedback.py
git commit -m "feat(s2): sync_submissions 编排(verdict先于report防双判·fail-soft·TDD)"
```

---

### Task 5: effect runner(镜像 fde_assignment_runner·不单测)

**Files:**
- Create: `phase3/backend/services/fde_qc_feedback_runner.py`

**Step 1: 写 runner**

```python
"""S2 effect runner · 飞书派活表「已提交」→ QC → verdict/report → 反馈写回飞书.

Run(cloud): python3 -m services.fde_qc_feedback_runner --base http://localhost:8000 \
    --app-token <BASE_EOVH> --table-id tbl69fankpoBhJfw [--dry-run]

环境:FEISHU_APP_ID/FEISHU_APP_SECRET(飞书)。report/verdict 端点无需 platform key。
线2 判分:FDE_TUTORIAL_ASSEMBLER 指 vendored assemble_tutorial.py(默认本地 skill 路径)。
线1 判分:复用 services.fde_scorer_runner.make_soul_score_fn(LLM judge·需 MiniMax key·
惰性构建——纯线2 批次不碰 LLM)。逻辑核在 services.fde_qc_feedback(TDD green)。
🔴 人是作者:本 runner 只写「QC反馈」+状态,绝不动「提交内容」。
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import urllib.error
import urllib.request

from services.fde_qc_feedback import line2_score, parse_tutorial_md, sync_submissions

FEISHU = "https://open.feishu.cn/open-apis"
_DEFAULT_ASSEMBLER = os.path.expanduser(
    "~/.claude/skills/knowledge-tutorial-assembler/scripts/assemble_tutorial.py")


def _http(method: str, url: str, token: str | None = None,
          body: dict | None = None, extra_headers: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        # 4xx/5xx 带 JSON envelope → 解析返回供调用方判;非 JSON 才视为传输故障(S1 C1)。
        try:
            return json.loads(e.read().decode())
        except Exception:
            raise e


def tenant_token() -> str:
    j = _http("POST", f"{FEISHU}/auth/v3/tenant_access_token/internal", body={
        "app_id": os.environ["FEISHU_APP_ID"],
        "app_secret": os.environ["FEISHU_APP_SECRET"]})
    return j["tenant_access_token"]


def _plain(v) -> str:
    if isinstance(v, list):
        return "".join(seg.get("text", "") for seg in v if isinstance(seg, dict))
    return "" if v is None else str(v)


class FeishuSubmissionSource:
    """读派活表「状态=已提交」行 → row dict(含提交内容)。记 record_id 供写回。"""

    FIELD_MAP = {"task_uid": "task_uid", "业务线": "line", "L级": "level",
                 "指派专家": "assignee", "验收标准": "acceptance",
                 "标题": "title", "提交内容": "submission"}

    def __init__(self, token: str, app_token: str, table_id: str):
        self.token, self.app, self.table = token, app_token, table_id
        self.record_ids: dict[str, str] = {}

    def read_submission_rows(self) -> list[dict]:
        url = (f"{FEISHU}/bitable/v1/apps/{self.app}/tables/{self.table}"
               f"/records?page_size=100")
        j = _http("GET", url, token=self.token)
        rows = []
        for item in (j.get("data") or {}).get("items") or []:
            f = item.get("fields") or {}
            if _plain(f.get("状态")).strip() != "已提交":
                continue
            row = {std: _plain(f.get(feishu)) for feishu, std in self.FIELD_MAP.items()}
            self.record_ids[row.get("task_uid") or ""] = item["record_id"]
            rows.append(row)
        return rows

    def write_feedback(self, task_uid: str, passed: bool, feedback: str) -> None:
        rid = self.record_ids.get(task_uid)
        if not rid:
            return
        url = (f"{FEISHU}/bitable/v1/apps/{self.app}/tables/{self.table}"
               f"/records/{rid}")
        _http("PUT", url, token=self.token, body={"fields": {
            "状态": "已通过" if passed else "已打回",
            "QC反馈": feedback[:1900]}})


def _load_module(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_qc_fn():
    """按业务线路由:线2=assembler validate(无LLM)·其余=checklist scorer(LLM judge·惰性)。"""
    assembler = _load_module(
        os.environ.get("FDE_TUTORIAL_ASSEMBLER", _DEFAULT_ASSEMBLER), "assemble_tutorial")
    _line1 = {}

    def qc_fn(row: dict, submission: str) -> dict:
        if str(row.get("line") or "").strip() == "2":
            return line2_score(assembler.validate(parse_tutorial_md(submission)))
        level = (row.get("level") or "L2").strip() or "L2"
        if level not in _line1:  # 惰性:纯线2 批次不初始化 LLM scorer
            from services.fde_scorer_runner import _load_secrets, make_soul_score_fn
            _load_secrets(os.environ.get("FDE_API_SECRETS",
                          os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")))
            _line1[level] = make_soul_score_fn(level=level)
        desc = (row.get("acceptance") or "") + "\n" + (row.get("title") or "")
        return _line1[level]({"task_uid": row["task_uid"], "description": desc,
                              "output": submission})

    return qc_fn


def make_verdict_fn(base: str):
    def verdict_fn(body: dict) -> None:
        res = _http("POST", base + "/api/platform/fde/verdict", body=body)
        if not res.get("success"):
            raise RuntimeError(f"verdict ingest failed: {str(res.get('error'))[:120]}")
    return verdict_fn


def make_report_fn(base: str):
    def report_fn(uid: str, agent: str, submission: str) -> None:
        res = _http("POST", base + "/api/platform/fde/report", body={
            "task_uid": uid, "agent_id": agent,
            "output": {"text": submission, "producer": "human"}})
        if not res.get("success"):
            # report 失败不致命(verdict 已留痕)·暴露不吞
            print(f"[fde-qc] report degraded for {uid}: {str(res.get('error'))[:80]}")
    return report_fn


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--app-token", required=True)
    ap.add_argument("--table-id", required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = FeishuSubmissionSource(tenant_token(), args.app_token, args.table_id)
    qc_fn = make_qc_fn()

    if args.dry_run:
        verdict_fn = lambda b: print("[dry] verdict", b["verdict_id"], b["overall_pass"])  # noqa: E731
        report_fn = lambda u, a, s: print("[dry] report", u, a, len(s), "chars")           # noqa: E731
    else:
        verdict_fn = make_verdict_fn(args.base)
        report_fn = make_report_fn(args.base)

    out = sync_submissions(src, qc_fn, verdict_fn, report_fn)

    for r in out["results"]:
        if args.dry_run:
            print("[dry] feedback", r["task_uid"], "passed=", r["passed"],
                  "\n" + r["feedback"])
        else:
            try:
                src.write_feedback(r["task_uid"], r["passed"], r["feedback"])
            except Exception as exc:  # noqa: BLE001 — 写回单点失败不拖批(S1 I3)
                print(f"[fde-qc] write_feedback failed for {r['task_uid']}: {str(exc)[:80]}")
    print("[fde-qc]", json.dumps({"passed": [r["task_uid"] for r in out["results"] if r["passed"]],
                                  "rejected": [r["task_uid"] for r in out["results"] if not r["passed"]],
                                  "skipped": out["skipped"], "failed": out["failed"]},
                                 ensure_ascii=False))


if __name__ == "__main__":
    main()
```

**Step 2: 本地语法校验 + 本地 dry-run(真飞书读·零写)**

Run: `cd phase3/backend && python -c "import ast; ast.parse(open('services/fde_qc_feedback_runner.py', encoding='utf-8').read()); print('syntax ok')"`
Expected: `syntax ok`

(dry-run 留 Task 7 列就位后)

**Step 3: Commit**

```bash
git add phase3/backend/services/fde_qc_feedback_runner.py
git commit -m "feat(s2): fde_qc_feedback_runner 飞书已提交→QC→verdict/report→反馈写回(镜像S1 runner)"
```

---

### Task 6: 飞书派活表加「提交内容」「QC反馈」列 + 状态值(一次性·本地跑)

**Files:**
- Create: `phase3/backend/scripts/add_qc_columns.py`

**Step 1: 写脚本**

```python
"""一次性:派活表(EOVh/tbl69fankpoBhJfw)加 S2 列:提交内容/QC反馈 + 状态值已通过/已打回.

Run(本地·金库凭据): python phase3/backend/scripts/add_qc_columns.py
幂等:已存在的列/选项跳过。
"""
import json
import os
import urllib.request

APP, TABLE = "EOVhbQwA0a1HEOsgmxecgkBVnwh", "tbl69fankpoBhJfw"
FEISHU = "https://open.feishu.cn/open-apis"
NEW_TEXT_FIELDS = ["提交内容", "QC反馈"]
NEW_STATUS_OPTIONS = ["已通过", "已打回"]


def _http(method, url, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _load_secrets():
    p = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")
    with open(p, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                os.environ.setdefault(k, v)


_load_secrets()
tok = _http("POST", f"{FEISHU}/auth/v3/tenant_access_token/internal", body={
    "app_id": os.environ["FEISHU_APP_ID"],
    "app_secret": os.environ["FEISHU_APP_SECRET"]})["tenant_access_token"]

fields = _http("GET", f"{FEISHU}/bitable/v1/apps/{APP}/tables/{TABLE}/fields?page_size=100",
               token=tok)["data"]["items"]
names = {f["field_name"]: f for f in fields}

for name in NEW_TEXT_FIELDS:
    if name in names:
        print("exists:", name)
        continue
    _http("POST", f"{FEISHU}/bitable/v1/apps/{APP}/tables/{TABLE}/fields", token=tok,
          body={"field_name": name, "type": 1})
    print("created:", name)

status = names["状态"]
opts = [o["name"] for o in (status.get("property") or {}).get("options", [])]
missing = [o for o in NEW_STATUS_OPTIONS if o not in opts]
if missing:
    _http("PUT", f"{FEISHU}/bitable/v1/apps/{APP}/tables/{TABLE}/fields/{status['field_id']}",
          token=tok, body={"field_name": "状态", "type": 3, "property": {
              "options": [{"name": o} for o in opts + missing]}})
    print("status options added:", missing)
else:
    print("status options ok:", opts)
```

**Step 2: 本地执行 + 验证**

Run: `python phase3/backend/scripts/add_qc_columns.py`
Expected: `created: 提交内容` / `created: QC反馈` / `status options added: ['已通过', '已打回']`

再跑一次确认幂等:Expected 全 `exists/ok`。

**Step 3: Commit**

```bash
git add phase3/backend/scripts/add_qc_columns.py
git commit -m "feat(s2): 派活表加提交内容/QC反馈列+已通过已打回状态(一次性·幂等)"
```

---

### Task 7: cloud 部署(外科 scp·并进 fde-assignment timer)+ dry-run

**Step 1: scp 文件到 cloud(fork 分支·绝不 pull)**

```bash
scp phase3/backend/services/fde_qc_feedback.py cloud:~/nautilus-mvp/phase3/backend/services/
scp phase3/backend/services/fde_qc_feedback_runner.py cloud:~/nautilus-mvp/phase3/backend/services/
scp "C:\Users\chunx\.claude\skills\knowledge-tutorial-assembler\scripts\assemble_tutorial.py" cloud:/home/ubuntu/fde-toolbox/assemble_tutorial.py
```

**Step 2: cloud dry-run(真飞书读·零写·验证模块加载+路由)**

```bash
ssh cloud 'cd ~/nautilus-mvp/phase3/backend && set -a; source ~/.fde_feishu.env; set +a; \
  FDE_TUTORIAL_ASSEMBLER=/home/ubuntu/fde-toolbox/assemble_tutorial.py \
  python3 -m services.fde_qc_feedback_runner --base http://localhost:8000 \
  --app-token EOVhbQwA0a1HEOsgmxecgkBVnwh --table-id tbl69fankpoBhJfw --dry-run'
```
Expected: `[fde-qc] {"passed": [], "rejected": [], "skipped": [], "failed": []}`(尚无已提交行=正确空集)

**Step 3: 并进现有 timer(每5min·复用 fde-assignment.timer)**

cloud 编辑 `/home/ubuntu/fde-assignment/run.sh` 追加(assignment runner 之后):

```bash
FDE_TUTORIAL_ASSEMBLER=/home/ubuntu/fde-toolbox/assemble_tutorial.py \
python3 -m services.fde_qc_feedback_runner --base http://localhost:8000 \
  --app-token EOVhbQwA0a1HEOsgmxecgkBVnwh --table-id tbl69fankpoBhJfw
```

(线1 LLM 判分要 MiniMax key:run.sh 里 source 与 soul-scorer 同款 secrets 文件——部署时实查 `/home/ubuntu/soul-scorer/run.sh` 的来源照抄;线2 不需要。)

验证:`ssh cloud 'systemctl list-timers | grep fde-assignment'` 在跑;`journalctl` 看下一轮含 `[fde-qc]` 输出。
本地存部署纪录:`phase3/backend/scripts/fde_assignment_run.sh.example` 更新追加段。

**Step 4: Commit**

```bash
git add phase3/backend/scripts/fde_assignment_run.sh.example
git commit -m "deploy(s2): qc runner 并进 fde-assignment timer(部署纪录)"
```

---

### Task 8: 走骨架闭环验收(S2 binding-DONE 判据·亲笔步骤=用户)

**Step 1(用户·专家#1):** 飞书派活表 `expert_t2_rsi_grounded_retrieval_20260612` 行,「提交内容」粘亲笔教案草稿,状态改「已提交」。
**Step 2(系统·≤5min):** timer 拉到 → 线2 QC → 「QC反馈」出现逐项 ✓/✗+reason → 状态=已打回(或直接已通过)。
**Step 3(用户):** 按 ✗ 项修改 → 状态改回「已提交」。
**Step 4(系统):** 再 QC → 状态=已通过。
**Step 5(引擎侧双验):**

```bash
curl -s "https://www.nautilus.social/api/platform/fde/verdict/expert_t2_rsi_grounded_retrieval_20260612"
```
Expected: ≥2 条 verdict(soul|qc|…|<hash1> overall_pass=false → soul|qc|…|<hash2> overall_pass=true·改稿留痕)。
`/tasks` 该行 status=settled + output.producer=human。

**Step 6:** 证据落 memory(binding-DONE)。

---

### Task 9: 废老路径 + 收尾

**Step 1:** `FDE_BUSINESS_CHARTER.md` §1 追加:「S2 闭环(2026-06-12):专家稿件提交+QC反馈唯一通道=派活表「提交内容/QC反馈」列;稿件走微信/文件/CLI 自此废弃」+ commit。
**Step 2:** MEMORY.md 索引一行 + session memory 文件。
**Step 3:** 跨框告知(outbound 投 cloud):soul-scorer 不会碰 human 稿的机制(verdict 先行遮蔽)+ v5 别动 expert_* 行。
**Step 4:** worktree 分支 merge master(`finishing-a-development-branch`):26+10 全 green 再 merge。

---

## 验收总查(S2 Definition of Done)
- [ ] ≥10 个 TDD 测试 green + 既有 FDE 测试(26)无回退
- [ ] 派活表 提交内容/QC反馈 列 + 已通过/已打回 状态在位(幂等脚本)
- [ ] 1 份专家亲笔稿:飞书提交→QC→逐项反馈写回→修改→已通过,全程不碰 CLI
- [ ] 引擎侧:fde_verdicts 留 ≥2 轮 verdict(改稿留痕)·report output producer=human
- [ ] soul-scorer 未双判 human 稿(verdict 先行顺序契约)
- [ ] timer 自驱(并进 fde-assignment·5min)·QC 不代写正文(红线)
- [ ] 老路径废弃声明入宪章 + 跨框已告知
