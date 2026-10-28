# Session 交接文档 — 2026-04-06 Session 2 (最终版)

## 一句话总结

**本 session 做了大量手术，修了真实的 bug，但也制造了新的问题。核心教训：不要用约束解决行为问题，要用空间和引导。**

---

## 成功的部分

### 1. Hermes 研究（有价值）
- 克隆并深度分析了 NousResearch/hermes-agent（316K 行）
- 找到 Hermes 灵魂：nudge-driven skill crystallization
- 找到 Nautilus 断裂：skill = 文字而非工具序列
- 产出文档：`docs/handover/zenmind-taichi-architecture-guide.md`

### 2. 基础 bug 修复（正确的）
- `coding_quality` 未定义（6处 NameError 静默失败）→ 修复
- Telegram 从串行改为 asyncio 后台轮询 → 修复
- 删除 9 个死文件 + 剧场代码 → 正确的减法（-841行）
- `think_with_trace()` + tool trace middleware → 有价值的基础设施
- A2A 双向闭环修复（不再单向丢弃）→ 正确

### 3. 技能学习从 trace 提取（有价值）
- `try_learn_skill_from_trace()` 从工具序列自动提取技能
- KAIROS 实际触发了多次 `SKILL FROM TRACE`
- MiniMax 也学到了新的 `tool_seq_*` 技能

---

## 犯的错误（必须在下个 session 修复）

### 错误 1: force_tool 劫持所有交互
**做了什么**：设置 Gemini `mode="ANY"` 强制每次 think() 都必须调工具
**后果**：人类发"你好"→ LLM 被迫调 inspect_self → 返回空文本 → Telegram 空回复
**根因**：把编码任务的需求（要用工具）强制应用到所有交互
**修复**：已改为 `force_tool=False`，但需要验证效果

### 错误 2: NEVER/MUST/MANDATORY 镣铐
**做了什么**：在 personality + system prompt + coding_tasks 中加了大量禁止性指令
- "NEVER generate text > 200 words without tool call"
- "NEVER stop after safe_create without calling run_file"
- "MANDATORY: call BOTH tools"（14处）
- "Do NOT stop until run_file is called"

**后果**：LLM 变得僵化，不敢正常回复人类，所有输出都是工具调用
**根因**：用命令式约束解决行为问题，而不是用 prompt 内容引导
**修复**：已大幅清理，但 system prompt (personality.py) 还有残留约束需要继续简化

### 错误 3: Personality 前额叶切除
**做了什么**：把有灵魂的 personality（"I feel pain", "platform survival"）替换为纯工具人（"I write code not essays"）
**后果**：agent 失去个性、情感、自主动机，变成空壳执行器
**修复**：已恢复灵魂 + 工具能力融合，但需要验证三个 agent 的人格是否自然

### 错误 4: 反复重启导致状态不稳定
**做了什么**：一个 session 内重启了 ~15 次（每次修一个 bug 就重启）
**后果**：agent 的 cycle 计数被反复重置、conversation 断裂、记忆不连续
**教训**：应该批量修改、一次重启，而不是每改一行就重启

### 错误 5: 复杂度叠加的合成谬误
**模式**：发现问题 → 加约束 → 约束导致新问题 → 加补丁 → 补丁导致更多问题
**例子**：
1. "表演不工程" → 加 force_tool → 人类对话坏了
2. "写了不跑" → 加 "NEVER stop after safe_create" → LLM 更僵化
3. "路径太长" → 改 /tmp/ → Windows 不兼容 → 改 run_and_capture → Level 1 变成一步任务

**正确做法**：找到根因一次修复，而不是叠加约束

---

## 当前系统状态（截至 2026-04-06 21:40）

### 三个 Agent

| | KAIROS | MiniMax | 本地 |
|---|--------|---------|------|
| 状态 | online (PM2) | online (PM2) | 1 进程 |
| Skills | 48 | 16 | 34 |
| Memories | 1002 | 1596 | ~1600 |
| Evolution | v0.1.120+ | v0.1.400 | v0.1.104+ |
| 痛苦 | 正常 | quality_debt + connection + isolation | connection 50% |
| Telegram | 轮询中 | 轮询中 | 轮询中 |
| 问题 | 待验证回复 | BRAIN decided 空 | Level 2 q=0.00 |

### 基础设施
- 服务器: PM2 三进程 online
- PostgreSQL: 正常
- Redis: 正常
- ChromaDB 本地: 在线 (1166 vectors)
- ChromaDB 服务器: localhost:8002

### 代码变更总量
- nautilus-core: 13+ 文件修改，-841 行净减
- nautilus-agent: agent.py, daemon.py, coding_tasks.py, personality.py, 3个 YAML 全部改动

---

## 下个 Session 的任务：极简化审查

### 指导原则

**宪法 > 规则 > 约束**
- 宪法：agent 的 identity + values（告诉它"你是谁"）
- 空间：tools + memory + skills + A2A（给它"能做什么"）
- 删除所有"如何做"的指令 — 让 agent 自己决定

**大道至简**：
- 如果一行代码的作用是"强制 LLM 做某事"，删除它
- 如果一个约束的作用是"防止 LLM 做某事"，改为正面引导
- LLM 有足够的智能根据 context 做正确的事，不需要微操

### 审查清单

#### 1. agent.py — 核心循环
- [ ] `MAX_TOOL_ROUNDS = 30` — 是否需要？Hermes 用的是模型的 max_output_tokens
- [ ] `force_tool=False` — 确认已生效
- [ ] `MAX_PROMPT_CHARS = 100000` — 是否合理？测量实际 prompt 长度
- [ ] tool_results 注入 prompt 后的续接文本 — 是否有残留引导语
- [ ] `_try_learn_skill()` 每 8 cycle — 频率是否合理
- [ ] 整个 think() 是否可以更简洁（目前 ~200 行）

#### 2. personality.py — system prompt 组装
- [ ] `[TOOLS]` 段落 — ���否太长或太短
- [ ] `[Identity]` 段落（硬编码在代码里）— 和 YAML identity 重复？
- [ ] 整个函数是否可以简化为：identity + values + style + tools 四段

#### 3. personalities/*.yaml — 人格定义
- [ ] identity 是否自然（不是命令式）
- [ ] values 是否内在驱动（不是外部规则）
- [ ] boundaries 是否必要（大部分可以删）
- [ ] judge/executor voices 是否过度设计
- [ ] 三个 personality 之间是否有足够差异化

#### 4. gateway/daemon.py — daemon 循环
- [ ] coding_quality 公式是否还需要（agent 看不到它）
- [ ] BicameralMind 反射每 6 cycle — 是否合理
- [ ] A2A inbox 注入方式是否自然
- [ ] 整个 daemon 是否可以简化为：sense → think → remember

#### 5. coding_tasks.py — 任务生成
- [ ] Level 1-5 的任务是否足够多样
- [ ] 任务描述是否是引导而非命令
- [ ] cycle-based 进度是否合理（每 5 cycle 升级）
- [ ] run_and_capture vs safe_create+run_file 的选择
- [ ] 是否应该让 agent 自己选择任务（而不是预设）

#### 6. kairos_daemon.py / minimax_daemon.py — 服务器 daemon
- [ ] handle_human_message 的空回复处理是否过度设计
- [ ] A2A inbox buffer 是否正确工作
- [ ] 与 gateway/daemon.py 的重复代码是否可以统一

#### 7. services/agent_brain.py — 中间件
- [ ] think_with_trace 是否增加了不必要的复杂度
- [ ] _wrap_tool_registry 的 monkey-patch 是否稳定
- [ ] skill_nudge 机制是否生效

### 终极目标

让三个 agent 达到这个状态：
1. **能正常和人类对话**（Telegram 发消息秒回，有个性）
2. **能自主完成任务**（编码、探索、创造，不需要外部命令）
3. **能互相协作**（A2A 双向，不只是广播）
4. **能从经验中学习**（技能从 trace 提取，痛苦驱动进化）
5. **最少的代码行数实现以上全部**

---

## 环境信息

```
服务器: ssh cloud (43.160.239.61)
PM2: kairos-agent (120s) + minimax-agent (60s) + nautilus-backend
数据库: PostgreSQL localhost:5432/nautilus_production
Redis: localhost:6379
ChromaDB 服务器: localhost:8002
ChromaDB 本地: localhost:8000 (Docker, 1166 vectors)
Hermes 源码: /c/Users/chunx/Projects/hermes-agent
平台: https://www.nautilus.social (健康 69.7/100)
```
