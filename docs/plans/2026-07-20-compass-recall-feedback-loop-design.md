# compass 评测输出闭环设计（2026-07-20）

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 `tests/eval_recall.py` 的执行结果变成可被下游调优直接读取的工件，形成 "输出→输入" 的本地闭环，并在同一套流程里给出下一步架构/代码建议。

**Architecture:** 在回放层面不改 recall 核心算法，只对 benchmark/harness 增加结构化输出、失败诊断字段和 `next_actions`。产物交给下一轮执行脚本消费，从而实现 "评测结果自动驱动优化假设"。

**Tech Stack:** Python, 当前 `tests/eval_recall.py`/`tests/eval_drift.py`、bash

---

## Task 1: 增强 `tests/eval_recall.py` 的评测输出为“可执行输入”

**Files:**
- Modify `tests/eval_recall.py`

**Step 1: Write the failing test**
- Add单元测试 `tests/test_eval_recall_artifact.py`：验证 `build_summary_payload()` 在多 mode 下返回可序列化字典，包含 `meta`, `modes`, `recommendations`。

**Step 2: Run it to make sure it fails**
- `python -m pytest tests/test_eval_recall_artifact.py -q`

**Step 3: Implement minimal code**
- 在 `tests/eval_recall.py` 中新增 `build_summary_payload(...)`（纯函数）。
- 新增 CLI 参数 `--out <path>`，默认写入 `.cache/eval_recall_<timestamp>.json`。
- 对每个 mode 输出：
  - `P@1/P@3/P@5/MRR`
  - `failed` 前 20 个记录（含 rank、query）
  - `delta_vs_baseline`（相对 flat）
- 在 `meta` 中增加:
  - `impact_nonzero_count`, `tier_nonworking_count`
  - `payload_version`, `command`, `mode`, `mem_count`, `has_embeddings`
- 新增 `recommendations`：
  - 无 `cumulative_impact`：建议触发 PoI/outcome 回路补面，先跑 `ops/` 中 outcome-reconciliation 相关脚本；
  - 无 tier 信号：建议核对 `tier` 冷启动和 promote 通路；
  - `ΔMRR` 不显著：建议冻结该策略分支，优先提升高回报维度（比如 RRF/BGE reranker 的实验组）。

**Step 4: Run it to make sure it passes**
- `python -m pytest tests/test_eval_recall_artifact.py -q`

**Step 5: Commit**
- `git add tests/eval_recall.py tests/test_eval_recall_artifact.py`
- `git commit -m "test: add eval_recall artifact mode and structured output"`

---

## Task 2: 让 `tests/run_all.sh` 输出一份统一度量清单（run manifest）

**Files:**
- Modify `tests/run_all.sh`

**Step 1: Write the failing test**
- Add/extend `tests/test_eval_recall_modes.py`（不改生产逻辑）：
  - `python tests/run_all.sh` 成功时应产出 `eval-manifest.json`（通过 grep 检查字符串）。

**Step 2: Run it to make sure it fails**
- `bash tests/run_all.sh | Out-Null; if (-not (Test-Path .cache/*/eval-manifest.json)) { exit 1 }`（本地按 shell 环境执行）

**Step 3: Implement minimal code**
- 在 `run_all.sh`:
  - 让 `eval_recall` 使用 `--out` 输出 JSON。
  - 追加 `manifest.json`，记录每个子脚本的日志路径、metric JSON 路径（有则记录）。
  - 运行后 echo `manifest: <path>`，用于 pipeline 下游读入。

**Step 4: Run it to make sure it passes**
- `python -m pytest tests/test_eval_recall_modes.py -q`
- `bash tests/run_all.sh`（只在本地完成路径检查，不需要长时间再次重复 full eval）

**Step 5: Commit**
- `git add tests/run_all.sh tests/test_eval_recall_modes.py`
- `git commit -m "chore: add eval run manifest with eval_recall artifact path"`

---

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

**Step 5: Commit**
- `git add ops/eval_recall_tuning_hint.py tests/test_eval_recall_tuning_hint.py`
- `git commit -m "feat: add eval_recall tuning-hint generator"`

---

Plan complete and saved to `docs/plans/2026-07-20-compass-recall-feedback-loop-design.md`.

Two execution options:

1. Subagent-Driven (this session) — fast, checkpoints, and manual review
2. Parallel Session — use executing-plans on separate clean session

I recommend option 1 for this round.
