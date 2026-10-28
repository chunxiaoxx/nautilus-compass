# SESSION_SUMMARY_20260809 · 平台框 session 总结与跨框交接

> date: 2026-08-09 (更新版 · 含 Codex 冲突分析)
> session_id: a8e08c29-09fe-4710-927d-e33eac87febb
> scope: 本轮所有调研/分析/诊断/产出/纠正 + Codex 冲突/重复造轮子深度分析
> purpose: 新对话起手读此文件,免重做、免冲突

---

## ⚠️ 核心警示：Codex 今日(8/9)活跃，大量并行工作

### Codex 今日提交（2026-08-09 · 14 个 session · 3:32 AM - 8:32 AM）

**nautilus-core（5 commits）**:
| commit | 描述 | 分支 |
|---|---|---|
| `21a36fd2c` | docs(platform): admit G1-A planning inputs | codex/g1-a-constitutional-gate |
| `1dab76717` | feat(core): enforce readonly metadata projection | codex/fde-s0-readonly-discovery 线 |
| `28fbeb506` | feat(platform): add G1-A constitutional gate | codex/g1-a-constitutional-gate |
| `a9d937f77` | docs(platform): define G1-A constitutional gate | codex/g1-a-constitutional-gate |
| `ac0323c3c` | docs(platform): plan internal R&D dogfood coordination | codex/internal-rd-dogfood-coordination |

**nautilus-compass（2 commits）**:
| commit | 描述 |
|---|---|
| `c277b78` | fix(m1): require receipt-backed advice sources |
| `e87234b` | docs(compass): publish G1-A grounding capsule |

### Codex 正在做的（DO NOT TOUCH）

1. **G1-A 宪法门（constitutional gate）** — 今日新开，core + compass 都在动
2. **Readonly metadata projection** — core 强制只读投影
3. **Internal R&D dogfood coordination** — 规划文档
4. **M1 receipt-backed advice** — compass 修正

---

## 🔴 冲突/重复造轮子完整地图

### A. 已确认重复（platform 重复了别人的工作）

| # | 什么 | 谁先做的 | platform 做了 | 判定 |
|---|---|---|---|---|
| D1 | income B=0 根因诊断 | compass 8/7 broadcast 已诊断 | 8/8 独立重新诊断，结论完全相同 | **重复劳动** — 结论一致：gmint 自产、externally_backed=0 |
| D2 | fuel-loop 是唯一闸门 | V5 8/8 outbound + compass 8/8 outbound 已判定 | 8/8 独立得出相同结论 | **重复劳动** — 两框已向 codex 发出部署请求 |
| D3 | soul timer 空转诊断 | （隐含在 compass 收敛判定中） | 8/8 独立诊断 | **部分重复** — compass 没逐 timer 查但结论一致 |

### B. 代码层重叠（但非冲突 — 同源分支）

| # | 什么 | Codex 状态 | Platform 状态 | 判定 |
|---|---|---|---|---|
| O1 | Protocol v2 合约 | 6-task 链(task1a→task6)完整实现 | task1a(contracts.py)在 soul-distill-deploy 上 | **同源** — 同一 commit 不同 parent hash。codex 领先 5 个 task |
| O2 | Protocol v2 设计文档 | `fff91a659` on codex branch | `886cd99ea` on soul-distill-deploy | **完全同一 commit** — 同作者同时同文件 |
| O3 | S0 admission | `codex/fde-s0-readonly-discovery`(只读探测层) | `fde_phase3_s0.py`(准入系统层) | **互补不冲突** — 不同层 |

### C. Codex 已建、Platform 不应碰的（17 个 codex 分支在 core 仓）

| 分支 | 内容 | 状态 |
|---|---|---|
| `codex/g1-a-constitutional-gate` | 🔴 **今日活跃** — 宪法门 + 规划输入 | 正在写 |
| `codex/fde-s0-readonly-discovery` | fail-closed Bitable 只读发现 | 4 commits |
| `codex/platform-protocol-v2-task1a` ~ `task6-admission` | 6 步协议 v2 实现 | 完整链 |
| `codex/m0-v1-platform-admission` | M0 admission(ed25519 + migration) | 8 commits |
| `codex/m0-v1-synthetic-dogfood-platform` | M0 合成测试 | 已存在 |
| `codex/fde-core-parity-v1` | FDE 核心对齐 | 存在 |
| `codex/fde-core-readonly-adapter-runtime` | 只读 adapter 运行时 | 存在 |
| `codex/fde-phase3-ops` / `recruiting-ops` | FDE 三期运营 | 存在 |
| `codex/m1-platform-loopback` | M1 平台环回 | 存在 |
| `codex/m1-r1a-plan-admission` | M1 R1A 计划准入 | 存在 |
| `codex/internal-rd-dogfood-coordination` | 🔴 **今日活跃** — 内部研发协调规划 | 正在写 |
| `codex/platform-p0-reconciliation-evidence` | P0 调和证据 | 存在 |

### D. 数据过时（platform 用了旧数据）

| 指标 | Platform session 时的值 | Compass 8/9 直读值 | 偏差 |
|---|---|---|---|
| income | 703 (7/16 探针) | **1707** (8/9 直读) | **严重过时** — V5 brain 修复后暴涨 |
| ext_verified | 93 | **107** | 过时 |
| health 502 | "已修"(platform 自己修的) | compass 8/9 说"未修" | **compass 数据过时** — 实测 backend 200 + nginx 200 |

---

## 一、本轮完成事项（全部 grounded）

### 1.1 基础设施修复（3 项）

| # | 事项 | 状态 | 证据 |
|---|---|---|---|
| 1 | health 502 修复 | ✅ 已修 | nginx `/api/health` 改指 8000 端口;ssh cloud 实测 backend 200 + nginx 200 |
| 2 | cloud VM git 直改清理 | ✅ 已清 | 7 个 agent_engine 文件 `git checkout --` 还原 |
| 3 | FDE 三期 GitHub 仓 + `fde` 快捷命令 | ✅ 已建 | `chunxiaoxx/nautilus-fde-phase3` (private, 3 分支全推);compass_start.ps1 已加 fde |

### 1.2 平台诊断（4 项 — 注:D1/D3 与 compass 部分重复）

| # | 诊断 | 结论 | 证据 |
|---|---|---|---|
| 1 | income 根因 | **B=0**:ext_verified verdicts 全来自自产 genopt 题;externally_backed = 0/3618 | DB 直查 fde_verdicts + convergence endpoint |
| 2 | soul 四 timer | 全活但**全空转** | systemd journalctl 逐个查 |
| 3 | 两条流水线断开 | Genopt 与 FdeDispatch 管道**零交叉** | DB 表关系分析 |
| 4 | 云端分支差异 | soul-distill-deploy ahead 1381/behind 119 vs main | `git rev-list --count` |

### 1.3 深度理论分析（收敛方程）

`improvement_rate = B × Σ(ηᵢ × fᵢ)`
- η = 就绪（四 timer + 验证链 + 记分牌）
- B = 零（全自产）
- 结论：工厂全开但无原料

### 1.4 边界纠正

平台框不做 FDE 业务决策 → 已存 `feedback-platform-not-fde-business-boundary`

---

## 二、最新跨框全景（8/9 compass broadcast 直读）

### 记分牌 8/9（compass 独立核实）

| 指标 | 8/8 | 8/9 | Δ | 含义 |
|---|---|---|---|---|
| income | 1067 | **1707** | +640 | V5 brain 恢复后爆发 |
| ext_verified | 86 | **107** | +21 | 验证管道在跑 |
| autonomy | 91.86% | **93.46%** | +1.6pp | 持续改善 |
| settle B-backed | 0/3618 | **0/3618** | 无变化 | ⚠️ 全自产零外部 |

### 闭环判定（compass + platform 一致）

```
造 B (V5 income 1707)     ✅ 活着且加速
搬 B (fuel-loop)          ❌ 物理断 (cloud 零部署)
消费 B (learning kernel)  ⏸ 代码在(codex 分支)，等 fuel-loop 数据
外部 B (S0 pilot)         🟡 邀请发出，等专家 OAuth
```

**唯一物理闸门：fuel-loop 部署** — 球在 codex（V5 + compass 已发 outbound 请求）

---

## 三、Platform 唯一应做的（不与 codex 冲突 · 不重复造轮子）

### 🔴 P0: 分支正名（soul-distill-deploy 1381/119 分叉）

当前分支 soul-distill-deploy 与 main 严重分叉。60 个本地分支（大量 codex/* + worktree/*）。
- 这**纯是 platform 的活**，codex 不会做
- 需用户拍板：rebase to main / merge to main / 选择性 cherry-pick
- **风险**：codex 今日还在往自己的分支推，如果平台动 main 会影响 codex 的 base

### 🟡 P1: 纠正 compass 过时数据

compass 8/9 broadcast 说 health 502 "未修" — 实测已修（backend 200 + nginx 200）。
- 发 outbound 告知 compass：health 已修，请更新下次快照
- **不重做诊断** — 只传递新信息

### 🟡 P2: V5/Kairos LLM key 审计

V5 8/8 outbound 请求平台验证 V7/Kairos LLM 配置（都指向 MiniMax proxy key，model 名不匹配）。
- **纯 platform infra** — 没人做
- 需 ssh cloud 检查环境变量 + 测试端点

### 🟡 P3: Codex 分支清理建议

60 个本地分支需要 triage（标活/死/冻结），给用户拍砍。
- 这符合 compass "减法清单" 角色
- **不碰 codex 活跃分支**（g1-a / internal-rd / fuel-loop）

### 🟢 P4: 健康监控 cron probe

加一个简单的定时 curl 探针，health 再挂时自动告警。

---

## 四、明确不做清单（DO NOT DO · 避免冲突和重复）

| # | 不做什么 | 谁在做 | 理由 |
|---|---|---|---|
| X1 | 不写 protocol v2 新代码 | codex 6-task 链 | codex 已完整实现 |
| X2 | 不碰 G1-A 宪法门 | codex 今日活跃 | 正在写 |
| X3 | 不建 Bitable 只读发现 | codex/fde-s0-readonly-discovery | 已实现 |
| X4 | 不写 fuel-loop 代码 | codex 拥有分支代码 | V5+compass 已请求部署 |
| X5 | 不修 C2 实验 | codex 被 V5+compass 要求 | 球在 codex |
| X6 | 不重诊 income 根因 | compass + platform 已诊完 | 结论一致 |
| X7 | 不做 FDE 业务决策 | FDE 框 | 用户明确纠正 |
| X8 | 不建跨框状态追踪 | compass 收敛执法 | compass 的角色 |
| X9 | 不建 M0 admission | codex/m0-v1-platform-admission | 已实现 |
| X10 | 不建 internal R&D dogfood | codex/internal-rd-dogfood-coordination | 今日活跃 |

---

## 五、协调协议根因分析

### 核心问题：Claude ↔ Codex 无实时协调通道

当前协调机制 = git（共享仓库）+ outbound md 文件（异步信箱）+ compass memory（跨框记忆）。

**B（协调通道带宽）问题**：
- outbound 是异步的：写后不知道对方何时读
- 数据会过时：platform session 用的 income=703 vs 实际 1707；compass 用的 health=未修 vs 实际已修
- 无"谁正在做什么"的注册表：codex 今日 14 个 session，platform 不知道在做什么直到 git log

**三个可能的改进方向**：

1. **Git commit 元数据约定**：commit message 加 `[domain:protocol-v2][status:active]` 标签，可以被 grep 快速扫描"谁在哪个域活跃"
2. **共享 active-tasks.json**：各仓库根放一个 JSON 文件，列出当前 session 的 active tasks + timestamps，其他框 session-start 读
3. **compass 作为协调层**：compass 已经在做收敛执法，把"谁正在做什么"也纳入 compass 的探针范围

方向 2 最轻量——一个 JSON 文件，每次 session 开头写自己的任务，结尾清除。compass session-start 可以扫描各仓库的 active-tasks.json 来生成"当前各框活跃度快照"。

---

## 六、四仓分离与 Turf 边界（最终版）

| 仓库 | Claude 框 turf | Codex 同时在做 |
|---|---|---|
| nautilus-core | infra/账本/裁判链/部署/分支管理 | protocol v2 / G1-A 门 / readonly discovery / M0 admission |
| nautilus-v5 | — (V5 框管) | fuel-loop 部署 / brain 运维 |
| nautilus-compass | — (compass 框管) | M1 fix / G1-A grounding / S4 flywheel |
| nautilus-fde-phase3 | — (FDE 框管) | FDE ops / recruiting / training materials |

**关键原则**：在 core 仓库，codex 有 17 个活跃分支覆盖 platform 领域的大量功能。Platform Claude 框必须先查 codex 分支再动手。

---

## 七、新对话起手动作（精简版）

1. **读此文件**（当前文件）
2. **`git log --all --oneline --since="2026-08-09T00:00"`** — 看 codex 今日最新提交
3. **ssh cloud `curl localhost:8000/api/platform/convergence`** — 获取最新记分牌
4. **按 P0-P4 推进**（见第三节）—— 不碰第四节"不做清单"

---

*nautilus-core platform dialog · session a8e08c29 · 2026-08-09 更新版*
*含 Codex 冲突分析 · grounded(git log + outbound 交叉 + ssh cloud 实测)*
