# 分支治理 triage 报告 (2026-08-09)

> core 仓 161 分支全量盘点 · grounded (git log 逐分支)

## 统计

| 类别 | 数量 | 操作 |
|---|---|---|
| 已合入 main | 2 | 可安全删除 |
| Codex 活跃 (≤7d) | 10 | 不碰 |
| Codex 过期 (>7d, 未合) | 30 | 需 codex 确认 |
| 正常 feature 分支 (旧) | 25 | 需评估 |
| **垃圾分支 (文件名误建)** | **~70** | 可批量删 |
| worktree 分支 | 6 | 可清 |
| 无提交日期 (空分支) | 18 | 可删 |

## 分批操作方案

### 批次 1: 安全删除 (零风险)

**已合入 main 的 2 个**:
- codex/embodied-data-pitch-v2
- codex/fde-t1-training-materials

**垃圾分支 (文件名/路径误建为分支名, ~70 个)**:
这些都是 `git checkout -b <文件名>` 的事故产物,不是功能分支:
- `_OUTBOUND_*`, `_INBOUND_*` (12+ 个 outbound 文件被建成分支)
- `CLAUDE.md`, `README.md`, `LICENSE`, `ARCHITECTURE.md` (项目文件)
- `pyproject.toml`, `docker-compose.yml`, `deploy.sh` (配置文件)
- `=`, `HTTP`, `tmp_*` (明显误操作)
- 单文件名: `demo.py`, `research`, `output`, `uploads`, `tools`, `scripts`, `docs`, `vtf`, `ops`, `packages`, `nautilus`, `nautilus_sdk.py` 等

### 批次 2: Codex 评估 (需 codex 确认)

**活跃 (>8/3, 不碰)**:
- codex/internal-rd-dogfood-coordination
- codex/g1-a-constitutional-gate
- codex/fde-core-readonly-adapter-runtime
- codex/m1-r1a-plan-admission
- codex/fde-core-parity-v1
- codex/m1-r1-runtime
- codex/m1-o1-process-isolation
- codex/m1-two-stage-runtime/plan-pin/platform-loopback/o1-hardening/agent-session-goal-contract
- codex/m0-v1-synthetic-dogfood-platform
- codex/coding-rsi-foundation-r0
- codex/platform-protocol-v2-task1a~task6-admission (6 个)
- codex/org-capability-charter
- codex/m0-v1-platform-admission
- codex/platform-protocol-v2-design
- codex/platform-p0-reconciliation-evidence
- codex/fde-s0-readonly-discovery

**过期但可能有价值 (7/20-8/2, ~10 个)**:
- codex/fde-phase3-ops, codex/fde-phase3-recruiting-ops
- codex/reborn-compass-j1
- codex/fde-gold-standard-workflow
- codex/phase3-* (8 个 phase3 系列)
- codex/fuel-liziqiu-20260720
- codex/deploy-lf-contract, codex/canonical-deploy
- codex/embodied-pitch-visual-v21

### 批次 3: 非 codex feature 分支 (需用户拍)

| 分支 | 最后 commit | 建议 |
|---|---|---|
| soul-distill-deploy | 8/7 | 当前工作分支,保留 |
| inc2/slice1~4.5 | 5/28 | 旧 sprint,评估是否已合 |
| inc3-* (4 个) | 5/29 | 旧 sprint |
| inc1.5/* (2 个) | 5/28 | 旧 sprint |
| fde-production-line | 6/6 | 可能已过时 |
| fde-dispatch-substrate | 6/6 | 可能已过时 |
| fde-durable-writeback | 6/9 | 可能已过时 |
| platform-rsi-fde-dashboard | 6/6 | 可能已过时 |
| merge-cloud-production | 3/15 | 很旧 |
| phase3-development | 2/18 | 很旧 |

### 批次 4: worktree 分支 (可清)

- worktree-agent-a2152bb850d8d40bc
- worktree-agent-a72327837a6616139
- worktree-agent-a76f6b8cd07a581ef
- worktree-agent-ab1ca44becee7358a
- worktree-dashboard-heartbeat-fix
- worktree-inc3-slice-b

## 建议执行顺序

1. 先删批次 1 (垃圾 + 已合, ~72 个) → 立刻减到 ~89 分支
2. 清批次 4 (worktree, 6 个) → ~83
3. 批次 2 codex 过期的发 outbound 问 codex → codex 回复后处理
4. 批次 3 等用户拍

## 不碰

- main, master (基础分支)
- soul-distill-deploy (当前工作分支)
- codex 活跃分支 (16 个)
