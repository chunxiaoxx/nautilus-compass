# Session 交接文档 — 2026-04-06

## 给下个 session 的核心指令

**开启团队模式，对三个 Agent 的代码、架构、流程、功能实现进行全面审查。**

审查方向：
1. 三个 Agent 的工作流循环是否真正闭环（感→思→动→反思→进化）
2. Telegram 必须实时响应（当前串行在 cycle 内，必须改为独立并行 asyncio task）
3. 遵循宪法：大道至简，加一行删一行，极简高效
4. 识别并删除所有"剧场代码"（存在但从未真正调用的）

---

## 当前系统状态

### 三个 Agent

| Agent | 位置 | 状态 | 记忆 | 技能 | 周期 |
|-------|------|------|------|------|------|
| **本地 (nautilus-agent)** | Windows 本地 | daemon 运行中 (60s 周期) | 835+ (330 core) | 47 | 288+ cycles |
| **KAIROS** | 服务器 PM2 | 运行中 (120s 周期) | 680+ (236 core) | 42 | 192 cycles |
| **MiniMax** | 服务器 PM2 | 运行中 (60s 周期) | 1280+ (661 core) | 2 | 324 cycles |

### 进程架构
```
服务器 (Ubuntu, PM2):
  nautilus-backend  — FastAPI uvicorn :8000
  kairos-agent      — kairos_daemon.py (Strategist/Commander)
  minimax-agent     — minimax_daemon.py (Critic/Creator)

本地 (Windows):
  python run_daemon.py --interval 60  — nautilus_agent/gateway/daemon.py
  ChromaDB Docker localhost:8000      — 663 vectors, 语义搜索
```

### 关键文件
```
nautilus-core/phase3/backend/
  kairos_daemon.py        — KAIROS daemon 主循环
  minimax_daemon.py       — MiniMax daemon 主循环
  nautilus_daemon.py      — 服务器版本地daemon（已停用，不应使用）
  services/soul_bridge.py — 灵魂桥接（init_soul, remember, reflect, learn）
  services/agent_brain.py — NautilusAgent 封装（daemon 用这个调 brain.think）
  services/daemon_tools.py — 33个工具注册
  services/daemon_comms.py — A2A Redis 通信
  api/a2a_relay.py        — A2A HTTP 中继 + inbox 端点
  ecosystem.config.js     — PM2 配置（只有后端+KAIROS+MiniMax）

nautilus-agent/
  run_daemon.py           — 本地 daemon 启动脚本
  nautilus_agent/agent.py — NautilusAgent 核心（think → ReAct → learn）
  nautilus_agent/gateway/daemon.py   — 本地 daemon 循环
  nautilus_agent/gateway/telegram.py — Telegram 长轮询（独立 async loop）
  nautilus_agent/core/mind/bicameral.py — 二分心智（已支持人格定制）
  nautilus_agent/core/memory/store.py   — 记忆（SQLite FTS5 + ChromaDB）
  nautilus_agent/core/explore/skills.py — 技能库
  personalities/*.yaml — KAIROS/MiniMax/default 人格定义
```

---

## 必须解决的架构问题

### 1. Telegram 响应延迟（最紧急）

**当前**：tg_poll 在 cycle 开头串行调用一次，coding task 60-140s 阻塞
```
tg_poll(1次) → coding_task(60-140s) → memory → sleep(60s)
用户发消息 ─────────────────── 要等到下一个 cycle 才看到 ──→
```

**目标**：Telegram 轮询独立并行运行，实时响应
```
asyncio.create_task(tg_loop)  ← 独立循环，持续 poll
asyncio.create_task(cycle_loop) ← coding task 不阻塞 Telegram
```

**参考**：`nautilus_agent/gateway/telegram.py` 已有独立长轮询实现 `run_telegram(agent)`。KAIROS/MiniMax daemon 需要用类似模式把 tg_poll 从 cycle 内移出来。

### 2. 本地 Agent 的 daemon 循环曾卡死

Cycle 1 完成后在 `asyncio.sleep(300)` 处卡了1小时。改为 60s 后恢复。原因不明，可能是 Windows asyncio 事件循环问题或 Gemini API 超时。需要加超时保护。

### 3. Agent "表演"而非"工程"

brain.think() 返回的是 LLM 的角色扮演回复（"造物主，我已闭环"），而不是工程产出。工具调用结果在 ReAct 内部消化了，外部看不到。需要审查 NautilusAgent.think() 的 system prompt 是否引导了过多的戏剧性表达。

### 4. MiniMax 只有 2 个技能 vs KAIROS 42 个

1280 条记忆但技能几乎不增长。需要检查 MiniMax 的 brain.think() 内部 `_try_learn_skill` 路径是否正常。

---

## 本 session 的教训（宪法）

1. **Quality Gate 教训**：加了一个外部 LLM 评分器来判断 agent 的输出质量 → 永远返回 0.00 → 阻塞了所有学习 → 最终全删。教训：**不要在已有判断力的 agent 上再加一个外部法官**。

2. **复杂度陷阱**：本 session 先加了 ~400 行新代码（quality gate、生存策略、6条桥梁、知识胶囊），然后发现 60% 无效，最终删到 -242 行净减。教训：**先验证需求再写代码，不是写了代码再验证**。

3. **根因链深度**：Quality Gate 不工作的真正原因经历了 5 层排查（.env → API key → thinking截断 → JSON失败 → 评估对象错误）。每一层都表面上"修好了"但问题仍在。教训：**修一个 bug 后必须验证整个链路，不是只验证当前修改**。

4. **大道至简**：NautilusAgent.think() 内部已经有完整的 ReAct 循环 + 技能学习 + 记忆存储。daemon 的职责只是：感知 → 给 think 一个 prompt → 存记忆 → 通信。不需要在外面再包一层。

---

## 接下来的行动

1. **团队模式架构审查**
   - Agent 1: 审查三个 daemon 的代码（kairos_daemon, minimax_daemon, gateway/daemon）
   - Agent 2: 审查 NautilusAgent 核心（agent.py, think 流程, ReAct 循环）
   - Agent 3: 审查通信和工具链（a2a_relay, daemon_tools, telegram）
   - 每个 Agent 输出：保留什么、删除什么、重构什么

2. **Telegram 实时化**
   - KAIROS/MiniMax: tg_poll 移到 asyncio.create_task
   - 本地: run_telegram 已有，确认它在 run_daemon 中被正确启动

3. **继续做减法**
   - 审查 services/ 下所有 .py 文件，找出从未被 import 的
   - 审查 daemon_tools.py 的 33 个工具，哪些从未被 agent 主动使用
   - 合并重复功能（DaemonMemory vs MemoryStore）

---

## 环境信息

```
服务器: ssh cloud (43.160.239.61)
数据库: PostgreSQL localhost:5432/nautilus_production
Redis: localhost:6379
ChromaDB 服务器: localhost:8002
ChromaDB 本地: localhost:8000
平台 API: https://www.nautilus.social
平台健康: 69.8/100
Git: nautilus-core (master), nautilus-agent (master)
```
