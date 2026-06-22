# KernelBench 分数制燃料适配器 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在 nautilus-compass 建 `kernelbench/kb_fuel.py`,把 KernelBench eval 结果桥成 V5 `ale_fuel_batch` 的 6-key 分数燃料 record,接同一 `ingest_fuel_records` 进多基准蒸馏合池。

**Architecture:** 纯函数(build sample / is_a_class 镜像 / accumulate)走 TDD 离线测(fake 注入·无 GPU);GPU seam `_run_one`/`main` gated(`pragma no cover`)调现有 `kernelbench-stump-batch` 工具链(`fde_t3_scratch/kernelbench/harness/`)+ attention harness 验强解。逐键匹配 V5 6-key 契约 → 下游 ingest 零改。

**Tech Stack:** Python 3.9+ · pytest · 镜像 `nautilus-v5/fde_capsule/ale_fuel_batch.py` 契约 · 复用 `vertical-task-factory/.../kernelbench_attention/harness.py` + scratch 工具链。

---

## 契约锚(实现前必读)
- 6-key:`task_id, problem_statement, strong_solution, strong_score, doubao_score, strong_verified`(+ additive `score_type`, `judge_version`)。源 = `nautilus-v5/fde_capsule/ale_fuel_batch.py:FUEL_KEYS` + `build_ale_fuel_sample`。
- A 类(maximize):`strong_verified ∧ strong>0 ∧ strong != doubao ∧ strong >= doubao*(1+rel_margin)`,`rel_margin=0.1`。源 = 同文件 `is_a_class`。
- KernelBench 映射:`strong_score`=强解 harness 加速比 · `doubao_score`=doubao best 加速比(失败/不过正确性门=0)· `strong_verified`=强解过正确性+速度门 · `score_type="maximize"`(加速比越大越好)。
- 测试约定:镜像 `tests/test_ale_eval.py` —— `sys.path.insert(.., "kernelbench")` + fake 注入,无 live GPU。

---

### Task 1: `build_kb_fuel_sample` 纯函数

**Files:**
- Create: `kernelbench/kb_fuel.py`
- Test: `tests/test_kb_fuel.py`

**Step 1: Write the failing test**
```python
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "kernelbench"))
import kb_fuel  # noqa: E402

def test_build_sample_has_6_keys_and_maps_speedup():
    s = kb_fuel.build_kb_fuel_sample(
        task_id="kb_attention",
        problem_statement="fused attention kernel ...",
        strong_result={"solution": "class ModelNew...", "speedup": 1.727, "verified": True},
        doubao_speedup=0.0,
    )
    assert s["task_id"] == "kb_attention"
    assert s["strong_score"] == 1.727
    assert s["doubao_score"] == 0.0
    assert s["strong_verified"] is True
    assert s["score_type"] == "maximize"
    assert s["strong_solution"].startswith("class ModelNew")
    # 逐键匹配 V5 契约
    for k in ("task_id","problem_statement","strong_solution","strong_score","doubao_score","strong_verified"):
        assert k in s
```

**Step 2: Run test to verify it fails**
Run: `python -m pytest tests/test_kb_fuel.py::test_build_sample_has_6_keys_and_maps_speedup -v`
Expected: FAIL (`No module named kb_fuel`)

**Step 3: Write minimal implementation**
```python
"""KernelBench → 6-key 分数制燃料适配器。镜像 nautilus-v5/fde_capsule/ale_fuel_batch.py
的契约,把 KernelBench 加速比 eval 桥成蒸馏合池的 6-key record。GPU seam gated。"""
from __future__ import annotations

FUEL_KEYS = ("task_id","problem_statement","strong_solution",
             "strong_score","doubao_score","strong_verified")

def build_kb_fuel_sample(task_id, problem_statement, strong_result, doubao_speedup,
                         judge_version=None) -> dict:
    """纯:KernelBench 单题强解结果 + doubao 加速比 → 6-key 样本。
    strong_result = {"solution": str, "speedup": float, "verified": bool}。
    score_type 恒 "maximize"(加速比越大越好)。"""
    return {
        "task_id": str(task_id),
        "problem_statement": str(problem_statement),
        "strong_solution": str(strong_result.get("solution", "")),
        "strong_score": float(strong_result.get("speedup", 0.0)),
        "doubao_score": float(doubao_speedup),
        "strong_verified": bool(strong_result.get("verified", False)),
        "score_type": "maximize",
        "judge_version": str(judge_version) if judge_version else "",
    }
```

**Step 4: Run test to verify it passes**
Run: `python -m pytest tests/test_kb_fuel.py -v`
Expected: PASS

**Step 5: Commit**
```bash
git add kernelbench/kb_fuel.py tests/test_kb_fuel.py
git commit -m "feat(kb-fuel): build_kb_fuel_sample — KernelBench 加速比→6-key 契约"
```

---

### Task 2: `is_a_class` 镜像 + 与 V5 语义对拍

**Files:**
- Modify: `kernelbench/kb_fuel.py`
- Test: `tests/test_kb_fuel.py`

**Step 1: Write the failing tests**
```python
def test_a_class_true_when_strong_beats_doubao():
    s = kb_fuel.build_kb_fuel_sample("t","p",{"solution":"x","speedup":1.727,"verified":True}, 0.747)
    assert kb_fuel.is_a_class(s) is True   # 1.727 >= 0.747*1.1 且 verified 且 >0

def test_a_class_false_double_fail_same_score():
    s = kb_fuel.build_kb_fuel_sample("t","p",{"solution":"x","speedup":0.0,"verified":True}, 0.0)
    assert kb_fuel.is_a_class(s) is False   # 同分 0/0 双败 = 非 A 类

def test_a_class_false_strong_zero():
    s = kb_fuel.build_kb_fuel_sample("t","p",{"solution":"x","speedup":0.0,"verified":True}, -1.0)
    assert kb_fuel.is_a_class(s) is False   # strong=0 没真解出

def test_a_class_false_not_verified():
    s = kb_fuel.build_kb_fuel_sample("t","p",{"solution":"x","speedup":2.0,"verified":False}, 0.5)
    assert kb_fuel.is_a_class(s) is False

def test_a_class_false_margin_too_small():
    s = kb_fuel.build_kb_fuel_sample("t","p",{"solution":"x","speedup":1.05,"verified":True}, 1.0)
    assert kb_fuel.is_a_class(s) is False   # 1.05 < 1.0*1.1
```

**Step 2: Run to verify fail**
Run: `python -m pytest tests/test_kb_fuel.py -v -k a_class`
Expected: FAIL (`is_a_class` 未定义)

**Step 3: Implement(逐行镜像 V5 `is_a_class` maximize 分支)**
```python
def is_a_class(sample: dict, rel_margin: float = 0.1) -> bool:
    """A 类(maximize·镜像 V5 ale_fuel_batch.is_a_class 语义):
    strong_verified ∧ strong>0 ∧ strong != doubao ∧ strong >= doubao*(1+rel_margin)。
    退化守卫:同分(双败)/ strong=0(没真解出)= 非 A 类(防毒燃料)。"""
    if not sample.get("strong_verified"):
        return False
    strong = float(sample["strong_score"])
    doubao = float(sample["doubao_score"])
    if strong == doubao:
        return False
    return strong > 0 and strong >= doubao * (1.0 + rel_margin)
```

**Step 4: Run to verify pass**
Run: `python -m pytest tests/test_kb_fuel.py -v`
Expected: PASS (全绿)

**Step 5: Commit**
```bash
git add kernelbench/kb_fuel.py tests/test_kb_fuel.py
git commit -m "feat(kb-fuel): is_a_class 镜像 V5 maximize 语义 + 退化守卫(防毒燃料)"
```

---

### Task 3: `accumulate_kb_fuel` 幂等去重

**Files:**
- Modify: `kernelbench/kb_fuel.py`
- Test: `tests/test_kb_fuel.py`

**Step 1: Failing test**
```python
def test_accumulate_dedup_keeps_higher_speedup():
    a = kb_fuel.build_kb_fuel_sample("t1","p",{"solution":"v1","speedup":1.2,"verified":True}, 0.5)
    b = kb_fuel.build_kb_fuel_sample("t1","p",{"solution":"v2","speedup":1.8,"verified":True}, 0.5)
    c = kb_fuel.build_kb_fuel_sample("t2","p",{"solution":"x","speedup":1.0,"verified":True}, 0.5)
    out = kb_fuel.accumulate_kb_fuel([b, c], existing=[a])
    by = {s["task_id"]: s for s in out}
    assert by["t1"]["strong_score"] == 1.8   # 取更高
    assert by["t2"]["strong_score"] == 1.0
    assert len(out) == 2
```

**Step 2: Run → FAIL.** `python -m pytest tests/test_kb_fuel.py -v -k accumulate`

**Step 3: Implement(镜像 `accumulate_ale_fuel`)**
```python
def accumulate_kb_fuel(samples: list, existing: list) -> list:
    """纯·幂等:按 task_id dedup(同 id 取 strong_score 更高者)。不改入参。"""
    by, order = {}, []
    for s in list(existing) + list(samples):
        tid = s["task_id"]
        if tid not in by:
            by[tid] = s; order.append(tid)
        elif float(s["strong_score"]) > float(by[tid]["strong_score"]):
            by[tid] = s
    return [by[tid] for tid in order]
```

**Step 4: Run → PASS.** `python -m pytest tests/test_kb_fuel.py -v`

**Step 5: Commit**
```bash
git add kernelbench/kb_fuel.py tests/test_kb_fuel.py
git commit -m "feat(kb-fuel): accumulate_kb_fuel 幂等去重取优(镜像 ale)"
```

---

### Task 4: GPU seam `_run_one` + `main`(gated · 不单测)

**Files:**
- Modify: `kernelbench/kb_fuel.py`

**Step 1: 实现 gated seam(`# pragma: no cover`)**
- `_eval_strong(harness_dir, candidate_path) -> dict`:调 attention `harness.py evaluate()` → `{"solution":code,"speedup":v["speedup"],"verified":v["passed"]}`。
- `_doubao_speedup(summary_json) -> float`:读现有 `build_summary.py` 产的 `summary.json` 取 doubao `fast1@5` 加速比(失败=0)。
- `_run_one(task_id, *, harness_dir, strong_path, summary_json, judge_version)`:`_eval_strong` + `_doubao_speedup` → `build_kb_fuel_sample`。
- `main()`:env `KB_OUT`(默认 `/tmp/kb_fuel_records.jsonl`)· 逐题落盘 accumulate · 打印 A 类计数。**幂等续跑**(读回 existing)。
- 文件头注释钉死:GPU 真跑在 T4·调 `fde_t3_scratch/kernelbench/harness/{kb_eval_drive.sh,build_summary.py}`·测试不覆盖此 seam。

**Step 2: 编译 + 纯函数回归**
Run: `python -c "import sys; sys.path.insert(0,'kernelbench'); import kb_fuel; print('ok')"` → `ok`
Run: `python -m pytest tests/test_kb_fuel.py -v` → 全绿(seam 不破纯函数)

**Step 3: Commit**
```bash
git add kernelbench/kb_fuel.py
git commit -m "feat(kb-fuel): gated GPU seam _run_one/main — 调 stump 工具链+attention harness 产 jsonl"
```

---

### Task 5: seed 验证(gated GPU · 协调)

**不在本 plan 的离线范围**(需 T4 GPU + doubao 实测·避与 7B 训练抢卡)。出代码后:
1. 写 outbound 给 V5:`kb_fuel.py` 就绪 + 6-key 契约对齐 `ale_fuel_batch` + 调用方式 → V5 在它 producer 管线跑 attention(或 stump leverage 表 p18/p51 真难倒题)的 doubao 实测 + Opus 强解,经本适配器出 record 进合池。
2. 或 compass 在 GPU 空档自跑一条 attention seed(强解 SDPA 1.727x 已验 + doubao 在 attention 实测)→ 确认 A 类与否(诚实:SDPA 库调用 doubao 可能也会→须实测定)。
3. seed 记录 + A 类结论写 memory。

**验收**:`kb_fuel_records.jsonl` 至少一条 `is_a_class==True` 经 `ingest_fuel_records` 进合池(端到端·V5/soul 侧确认)。

---

## 完成定义
- 纯函数(Task 1-3)TDD 全绿·离线可跑。
- gated seam(Task 4)编译通过·结构对齐 ale。
- 契约逐键匹配 V5 `ale_fuel_batch`(下游 ingest 零改)。
- seed(Task 5)gated·走协调不阻塞离线交付。
- 红线:不编 doubao 分 · 不碰 V5 producer / soul ingest(turf)。
