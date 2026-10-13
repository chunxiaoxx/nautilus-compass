---
name: orgfuel-ORGG-0c99140df8bc03cd-a52cdc323a
description: "判读档判例 2026-07-20-compass-recall-feedback-loop-design · Task "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-0c99140df8bc03cd
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-07-20-compass-recall-feedback-loop-design · Task 2: 让 `tests/run_all.sh` 输出一份统一度量清单（run manifest）
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
- `python -m pytest tests/
