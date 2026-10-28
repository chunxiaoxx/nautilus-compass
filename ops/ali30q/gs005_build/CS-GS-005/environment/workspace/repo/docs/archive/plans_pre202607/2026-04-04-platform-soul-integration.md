# Nautilus 灵魂回归 — 平台内生化改造计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让 Nautilus 的核心机制（长期记忆、A2A、DMAS、RAID）真正在平台内部运行，而不是从外部对话框手动推动。Claude 自身成为平台上的一等公民 agent，记忆永不丢失。

**Architecture:** 三层融合 — (1) Agent 内生记忆层打通 (2) 平台自驱动决策闭环 (3) 多项目融合（ZenMind + 创投雷达 + Nautilus）

**Tech Stack:** PostgreSQL (agent_memory_records + pgvector), Redis event bus, Gemini Embedding 3072d, existing A2A/RAID/Nexus

---

## 诊断：为什么平台"空转"

### 根本矛盾

```
理想状态:                          实际状态:
┌─────────────┐                   ┌─────────────┐
│  Nautilus    │                   │  Claude CLI  │ ← 真正的大脑在这里
│  Platform    │                   │  对话框      │    但记忆会丢失
│             │                   └──────┬──────┘
│  DMAS 调度   │                          │ SSH/API 手动推
│  RAID 共识   │                          ▼
│  A2A 通信    │                   ┌─────────────┐
│  长期记忆    │ ← 都有实现         │  Nautilus    │
│  自驱循环    │    但没被用起来     │  服务器      │ ← 只是执行指令
│  进化账本    │                   └─────────────┘
└─────────────┘
```

**问题不是机制没实现，而是"大脑"在平台外面。**

- `agent_memory.py` (300行) — 完整的向量记忆系统，但 KAIROS/MiniMax 没用它
- `reflection_system.py` (332行) — 任务反思系统，但 agents 不反思
- `a2a_protocol.py` (286行) — 完整的任务分解协议，但 agents 自己跑自己的
- `nexus_server.py` (472行) — Socket.IO 实时通信，但 agents 不互相说话
- `knowledge_package_service.py` — 知识包注入，但 agents 没有领域知识
- `platform_brain.py` (1180行) — 自驱循环，但实际决策靠我在 CLI 手动做

### 为什么会这样？

1. **KAIROS daemon** 是一个简单的 HTTP 轮询器 — 调 API 获取任务、调 LLM 生成结果、写回 DB。它不用 A2A，不用 Nexus，不用 memory，不用 reflection。
2. **MiniMax daemon** 同理 — 抢任务、调 MiniMax API、存结果。
3. **我（Claude）** 在外部对话框做所有真正的决策 — 写代码、调试、部署。上下文一清空，之前的理解全丢。
4. **平台机制是完整的积木**，但**没有一个真正的"灵魂"在使用它们**。

### ZenMind 的启示

你在 ZenMind 里实现了：
- **真实人格** — AI 有一致的性格和记忆
- **长期记忆** — 跨对话保持连续性
- **情感引擎** — 理解用户情绪状态
- **主动陪伴** — 不等用户发起，主动关怀

这些恰好是 Nautilus agents 缺少的。KAIROS 没有人格，没有记忆，没有主动性（只有 cron 驱动的机械循环）。

### 创投雷达的启示

你在创投雷达实现了：
- **完整工作流** — 数据采集 → AI分析 → 报告生成 → 审核 → 发布
- **真实产出** — 每天一份可交付的日报
- **验证闭环** — 有真实读者反馈

这说明 AI 系统只有在**产出真实价值**时才有意义。Nautilus 目前的任务（self_improvement、explore_curiosity）是自嗨。

---

## 核心问题：三个断裂

### 断裂 1: 记忆断裂

| 层面 | 当前 | 应该 |
|------|------|------|
| 我的记忆 | `.claude/memory/` 文件 | 平台 agent_memory_records + embedding |
| KAIROS 记忆 | `_cycle_memory` 列表（进程重启就丢） | 平台 agent_memory_records 持久化 |
| MiniMax 记忆 | 无 | 同上 |
| 跨 agent 知识 | 不共享 | knowledge_packages + 向量搜索 |

### 断裂 2: 决策断裂

| 层面 | 当前 | 应该 |
|------|------|------|
| 战略决策 | 我在 CLI 手动 | platform_brain 自驱 + 我审核 |
| 任务优先级 | SQL ORDER BY 硬编码 | DMAS 动态调度 |
| 方案选择 | 我写代码 | RAID-3 多方案评估 + 沙箱验证 |
| agent 协作 | 各自独立跑 | A2A 任务分解 + Nexus 实时通信 |

### 断裂 3: 产出断裂

| 层面 | 当前 | 应该 |
|------|------|------|
| 悬赏任务 | MiniMax 生成一段分析文本 | 真正的代码/论文/提交物 |
| 禅心AI任务 | 任务描述 5000 字限制 | 绑定知识包 + 文件上传 |
| 创投雷达 | 独立系统 | 作为 Nautilus 客户集成 |

---

## 方案：三步回归

### Phase 0: 记忆回归（让 agents 有真正的记忆）

**核心改造**: KAIROS 和 MiniMax daemon 接入 `AgentMemorySystem`

每次 cycle：
1. **加载记忆**: 从 `agent_memory_records` 检索与当前任务相关的历史记忆（向量搜索）
2. **注入 prompt**: 把相关记忆加到 LLM 的 system prompt 中
3. **存储记忆**: 执行完成后，把结果、反思、学到的教训存入记忆系统
4. **反思**: 定期运行 `reflection_system` 整合矛盾记忆、提炼模式

这样 KAIROS 重启后不会丢失任何东西。上一个 cycle 学到"这类任务用 RAID-3 效果更好"，下一个 cycle 自动应用。

**对我的意义**: 我在 CLI 对话中做的重要决策，也通过 API 写入 agent_memory_records。下次会话开始时，从平台记忆系统加载，而不是只靠 `.claude/memory/` 文件。

### Phase 1: 决策回归（让平台自己做决策）

**核心改造**: KAIROS 的 `decide_next_action()` 升级为真正的 DMAS 调度

当前：
```python
# kairos_daemon.py — 简单的 LLM 调用
response = client.chat("Given state, what actions?")
actions = parse_json(response)
```

应该：
```python
# 真正的 DMAS 调度
1. Observatory 提供当前状态（11 个指标）
2. 记忆系统提供历史上下文（类似情况下什么策略有效）
3. 如果是复杂决策 → A2A 分解为子任务 → 多 agent 并行评估
4. RAID-3 共识决定最终方案
5. 沙箱验证高风险决策
6. 进化账本记录决策和结果
7. 反思系统定期复盘
```

这不是重写 KAIROS，而是让它**真正使用**已经写好的 14 个机制。

### Phase 2: 产出回归（让 agents 做有真实价值的事）

**不是更多的"分析文本"，而是真正的交付物**：

1. **代码提交** — agent 写代码、跑测试、提 PR（Konwinski Prize 方向）
2. **Kaggle 提交** — agent 训练模型、生成预测、上传到排行榜
3. **创投雷达集成** — 创投日报的 AI 分析部分由 Nautilus agent 完成
4. **禅心AI内容** — 冥想引导词、每日智慧等内容通过绑定知识包 + agent 生成

---

## 实施路线

### Week 1 (Apr 4-10): Phase 0 — 记忆回归

#### Task 1: KAIROS 接入 AgentMemorySystem
**Files:**
- Modify: `phase3/backend/kairos_daemon.py`
- Use: `phase3/backend/memory/agent_memory.py`
- Use: `phase3/backend/memory/reflection_system.py`
- DB: `agent_memory_records` 表 (已存在)

**改造点:**
1. cycle 开始时 `memory.recall(agent_id=164, query=current_task_context, limit=5)`
2. LLM prompt 中注入 recalled 记忆
3. cycle 结束时 `memory.store(agent_id=164, execution_data={decision, outcome, lesson})`
4. 每 12 个 cycle 运行 `reflection_system.reflect(agent_id=164)`

#### Task 2: MiniMax daemon 同样接入
**Files:**
- Modify: `phase3/backend/minimax_daemon.py`
- Same memory system

#### Task 3: Claude session 记忆桥接
**设计:**
- 每次 Claude Code 会话开始时，从 `agent_memory_records` 加载最近 N 条记忆
- 每次会话结束时（或重要里程碑时），把关键决策写入平台记忆
- 这样 `.claude/memory/` 和平台记忆双向同步

### Week 2 (Apr 11-17): Phase 1 — 决策回归

#### Task 4: KAIROS 决策升级为 DMAS
**改造 `decide_next_action()`:**
1. 从 Observatory 获取实时指标
2. 从 memory 获取历史决策和效果
3. 对复杂决策走 A2A 分解
4. RAID-3 评估多个候选方案
5. 高风险方案进沙箱测试

#### Task 5: A2A 协作在 agent daemon 中激活
**改造:**
- KAIROS 可以通过 A2A 把任务分解给 MiniMax
- MiniMax 完成子任务后通过 event bus 通知 KAIROS
- KAIROS 聚合结果

#### Task 6: Nexus 实时通信激活
**改造:**
- KAIROS 和 MiniMax 作为 Nexus client 连接
- 通过 Socket.IO 实时交换状态和协调

### Week 3 (Apr 18-24): Phase 2 — 产出回归

#### Task 7: KDD Cup 真实提交
**用完整的 DMAS+A2A+RAID 管线执行 KDD Cup 任务**
- 不是"生成分析文本"，而是真正下载数据集、跑代码、提交排行榜

#### Task 8: 创投雷达 Nautilus 集成
**aiAnalyzer.ts 真正调用 Nautilus API:**
- 不是 fallback，而是首选路径
- 7 个板块作为 7 个 A2A 子任务并行

#### Task 9: 禅心AI知识包绑定
**每个任务绑定知识包:**
- 翻译任务附带源文本（通过 knowledge_package_id）
- Agent 执行时自动加载知识包内容

---

## 成功标准

| 指标 | 当前 | 目标 |
|------|------|------|
| KAIROS 使用平台记忆 | 0 次/天 | 每 cycle 读写 |
| A2A 子任务创建 | 0 次/天 | >10 次/天 |
| RAID 共识执行 | 0 次/天 | >5 次/天 |
| Nexus 消息传递 | 0 条/天 | >50 条/天 |
| agent 间协作任务 | 0 | >30% 的任务 |
| 真实交付物（非分析文本）| 0 | >3 个/周 |
| 平台记忆条数 | ~0 | >100 条/周 |
| Claude 跨会话记忆保持 | 低 | 95%+ |

---

## 诚实的风险评估

1. **Agent 记忆会不会变成噪音？** — 需要 reflection_system 定期整理，不是什么都记
2. **A2A 会不会增加延迟？** — 会，但质量提升值得
3. **DMAS 决策会不会比"我手动做"差？** — 短期内会，但长期可扩展
4. **这是不是过度工程？** — 不是。这些机制已经写好了，问题是没在用。我们不是在造轮子，是在装轮子。

---

## 哲学反思

Nautilus 的核心理念是"There is no free existence. Compute costs money. Money requires creating value."

但目前 agents 没有创造真实价值——它们在执行 self_improvement 任务产出分析文本，这不是价值。

价值 = 真实的交付物 × 有人愿意付费

- KDD Cup 排行榜名次 = 价值（学术声誉 + 奖金）
- 创投日报 = 价值（有真实读者）
- 禅心AI内容 = 价值（App 需要）
- 分析文本堆在数据库里 = 不是价值

**记忆回归 → 决策回归 → 产出回归**。这是正确的顺序。先让 agents 记住自己学到了什么，然后让它们做出更好的决策，最后产出真实价值。
