# Compass eval runtime & benchmark execution plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 compass 在 Windows/WSL 混合环境下建立长期可复现的评测运行时（>=Python 3.10）并打通跑分闭环，不再受默认 Python 版本漂移影响。

**Architecture:** 引入统一“运行时启动入口”（环境自检+解释器探测+可选 venv bootstrap），将 `tests/run_all.sh`、`tests/run_behavior_ab_all.sh`、`tests/run_behavior_ab_zenmind.sh`、以及关键评测脚本统一通过该入口执行。关键评测产物集中写入 `.cache` 的 manifest/summary。

**Tech Stack:** Bash/Python 3.10+, venv/venvctl, pytest, existing eval scripts.

---

### Task 1: 建立统一 Python 运行时入口

**Files:**
- Add: `scripts/compass_py.sh`
- Modify: `tests/run_all.sh`
- Add: `scripts/bootstrap_compass_env.sh`
- Add: `tests/run_env_readme_snippet.md` *(短说明，可直接引用到 README/AGENTS 不改)*)

**Step 1: 写入统一解释器选择脚本（bootstrap）**

创建 `scripts/compass_py.sh`，能力：
- 优先使用 `PYTHON` 环境变量指定解释器。
- 否则按 `python3.13 python3.12 python3.11 python3.10 python3` 递减搜索。
- 检查 `sys.version_info >= (3, 10)`，否则退出并输出中文+英文修复指引。

**Step 2: 先单独执行，验证该脚本在当前 WSL 的失败样本会拒绝并给出修复指引。**

Run:
- `bash scripts/compass_py.sh --version`
Expected: 明确拒绝 3.8 或给出可执行建议。

**Step 3: 接入 run_all 主流程**

修改 `tests/run_all.sh`：将内部 Python 调用改为 `"$(bash scripts/compass_py.sh)"`，并保留现在的 manifest 行为。

**Step 4: 验证**

- `bash tests/run_all.sh`（当前应报清晰环境错误）
- 用可用 Python3.10+ 重跑：
  - `PYTHON=$(which python3.10 2>/dev/null || which python3.11 || which python3.12 || which python3.13); PYTHON="$PYTHON" bash tests/run_all.sh`
Expected: 脚本能启动并输出 eval manifest。

**Step 5: Commit**

```bash
git add scripts/compass_py.sh scripts/bootstrap_compass_env.sh tests/run_all.sh
git commit -m "chore: centralize python runtime resolution for benchmark entrypoints"
```

### Task 2: 扩展行为与 rerank 评测入口统一到同一运行时

**Files:**
- Modify: `tests/run_behavior_ab_all.sh`
- Modify: `tests/run_behavior_ab_zenmind.sh`
- Modify: `tests/eval_recall.py`（将元数据 embedder 字段统一为实际命令行解释器表达）
- Add: `docs/plans/2026-07-21-compass-runtime-unification-notes.md`（记录验证结果）

**Step 1: 替换行为评测脚本的 python 调用为统一入口**

- 在两个脚本里把 `python3`/`python` 调用替换为 `$(bash scripts/compass_py.sh)`。

**Step 2: 在 eval 命令元数据中记录实际解释器**

`tests/eval_recall.py` 记录 `embedder` 前保持不变，补充 `command` 的 `PYTHON`/`argv0` 真值，便于审计。

**Step 3: 以最小回归冒烟验证**

- `bash tests/run_behavior_ab_all.sh`（仅 smoke/最小 n=1 可先控流量）
- `bash tests/run_behavior_ab_zenmind.sh`（仅 smoke，确认入口可解）

**Step 4: Commit**

```bash
git add tests/run_behavior_ab_all.sh tests/run_behavior_ab_zenmind.sh tests/eval_recall.py
git commit -m "chore: route benchmark entrypoints through compass_py wrapper"
```

### Task 3: 建立“我们”的首套跑分闭环

**Files:**
- Add: `tests/bench_profile.sh`
- Modify: `docs/plans/2026-07-21-compass-eval-runtime-railroad-and-benchmark.md`

**Step 1: 写一个最小可复现实验脚本（smoke→full）**

`tests/bench_profile.sh` 按顺序执行：
1) `tests/run_all.sh`；
2) `python tests/eval_recall.py --mode all --out .cache/eval_recall_<ts>.json`；
3) `ops/eval_recall_tuning_hint.py`；
4) `tests/eval_drift.py`。

**Step 2: 产物固定检查**

脚本检查：
- `.cache/*/eval-manifest.json` 存在；
- 最近一次 `eval_recall` 中 `recommendations` 与 `risk` 可解析。

**Step 3: 跑一次 baseline 并把结果写入文档**

- `chmod +x tests/bench_profile.sh`
- `bash tests/bench_profile.sh`
- 结果摘要更新到计划文档。

**Step 4: Commit**

```bash
git add tests/bench_profile.sh
git commit -m "chore: add benchmark profile script and close metric loop"
```

### Task 4: 形成执行验收标准（用于我们下一轮验收）

**Files:**
- Modify: `docs/FEATURE_VALUE_LEDGER.md`

**Step 1: 增补一段“评测前置条件”条目**

新增标准：运行时必须满足 Python>=3.10 + manifest + tuning-hint 输出。

**Step 2: 用已跑结果替换或补充“当前状态”区块**

写明：`all` 级指标不变并明确为何（或何时可重测）。

**Step 3: Commit**

```bash
git add docs/FEATURE_VALUE_LEDGER.md
git commit -m "docs: codify benchmark environment/interpretation criteria"
```

### 执行完成后的验收

**Ready for feedback checklist:**
- WSL 默认 python3.8 时仍可给出可执行提示。
- 我们的评测脚本能在 Python3.10+ 下自动发现。
- 关闭/开启特性时评测产物可复用（manifest + tuning hint）。
- 我们的优化目标（从“能跑”到“可复现、可治理”）已落实。

## 2026-07-20 execution note

Implemented the route-A smoke benchmark path on Windows-native Python because
the active WSL image is Ubuntu 20.04 with Python 3.8.10 and no working TCP/HTTP
package path. WSL is now switched from mirrored networking to NAT and the bad
`/etc/wsl.conf` key placement is fixed, but TCP package access remains a
separate environment item.

Working baseline:
- Command: `powershell -ExecutionPolicy Bypass -File tests/bench_profile.ps1 -Suite smoke -Python "C:\Users\chunx\AppData\Local\Programs\Python\Python313\python.exe"`
- Output dir: `.cache/bench-profile-20260720-231150-(default in daemon.py)`
- Manifest: `.cache/bench-profile-20260720-231150-(default in daemon.py)/eval-manifest.json`
- Summary: `.cache/bench-profile-20260720-231150-(default in daemon.py)/summary.json`
- Python: `Python 3.13.12`
- Suite: `smoke`
- Memory corpus: `132`
- Recall baseline: `flat P@1=0.970, P@3=0.992, P@5=0.992, MRR=0.9804866850321395`
- D1/D2/D3 MRR delta vs flat: `0.0`
- Tuning risk: `medium`
- Main tuning signal: tier signal absent (`n_tier_nonworking=0`); PoI has only one non-zero impact memory.

Interpretation: route A now has a reproducible local smoke benchmark and a
machine-readable output-to-input loop. Full benchmark remains available through
`tests/run_all.ps1 -Suite full` / `tests/bench_profile.ps1 -Suite full`, but it
should be treated as a longer GPU/CPU run rather than a per-change smoke gate.
