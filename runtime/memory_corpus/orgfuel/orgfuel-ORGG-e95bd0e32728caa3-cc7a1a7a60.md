---
name: orgfuel-ORGG-e95bd0e32728caa3-cc7a1a7a60
description: "判读档判例 2026-07-20-compass-recall-feedback-loop-design · Task "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-e95bd0e32728caa3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-20-compass-recall-feedback-loop-design · Task 3: 以真实结果驱动的架构性建议脚本（轻量）
## Task 3: 以真实结果驱动的架构性建议脚本（轻量）

**Files:**
- Add `ops/eval_recall_tuning_hint.py`

**Step 1: Write the failing test**
- Add `tests/test_eval_recall_tuning_hint.py`：给定一个 mock 的 eval_recall artifact，验证能输出 3 类建议（数据缺失、参数重算、策略冻结/继续）。

**Step 2: Run it to make sure it fails**
- `python -m pytest tests/test_eval_recall_tuning_hint.py -q`

**Step 3: Implement minimal code**
- 让脚本接收 artifact json，输出：
  - `next_actions`（列表）
  - `risk`（none/low/medium）
  - `blocking_reason`（如缺失信号）
- 与 plan 的 `run_all` 产物形成闭环输入链，后续每次评测直接拿来读。

**Step 4: Run it to make sure it passes**
- `python -m pytest tests/test_eval_recall_tuning_hint.py -m fast -q`
- `python ops/eval_recall_tuning_hint.py --artifact <latest_eval_recall_json>`

**Ste
