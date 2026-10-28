# Nautilus V5 · 认知架构调研（Fast Response + Deep Cognition）

> 2026-04-20 深度调研存档
> 调研覆盖：2023-2026 开源项目 / 学术论文 / 商业产品
> 核心问题：如何实现"快车道秒级响应 + 慢车道分钟级反思 + 主动车道自驱"

---

## Part 1：产品 / 项目 / 论文清单

### 1.1 Letta sleep-time（最贴近 V5 需求）
- [docs.letta.com/guides/agents/architectures/sleeptime](https://docs.letta.com/guides/agents/architectures/sleeptime)
- **核心**：双 agent 共享 memory block。primary 面向用户、sleep-time 每 N 步（默认 5）异步重写 memory。primary 可随时读 memory，不必等 sleep-time 完成。
- **启发**：V5 的"快慢分离"蓝本——同一记忆空间，两个写入权限不同的 agent。

### 1.2 Sleep-time Compute 论文（arXiv 2504.13171）
- Lin, Snell, Packer 等（2025-04）
- **核心**：把推理拆成 `S(c) → c'`（离线处理 context）和 `T_b(q, c') → a`（在线回答 query）。GSM-Symbolic 上把 test-time 计算削减 5×。
- **启发**：V5 可在用户没问之前"预推理"可能的问题，用户来问时直接套答案。

### 1.3 Letta V1 agent loop
- [letta.com/blog/letta-v1-agent](https://www.letta.com/blog/letta-v1-agent)
- **核心**：弃用 heartbeat + send_message 工具，改为 native reasoning。继承 ReAct 思维链 + MemGPT stateful memory + Claude Code 多步 tool call。
- **启发**：V1 架构本身是 fast path（一个主循环做完 ReAct），sleep-time agent 是 slow path。"单循环 + 后台伙伴"分层值得复制。

### 1.4 Claude Code Auto Dream（2026-03 内测）
- [claudefa.st/blog/guide/mechanics/auto-dream](https://claudefa.st/blog/guide/mechanics/auto-dream)
- **核心**：**双门触发**——距上次 dream 满 24h 且满 5 个 session 才启动。四阶段（orientation → gather signal → consolidation → prune index）；锁文件防并发；只改 memory 文件，源码/配置一律只读。观测到一次消化 913 session 用时 8-9 分钟。
- **启发**：主动周期性 maintenance 的**触发门 + 安全边界 + 四阶段管线**是 V5 内省的蓝本。

### 1.5 Claude Code Chyros（泄露代号）
- [mindstudio.ai/blog/what-is-claude-code-chyros-background-daemon](https://www.mindstudio.ai/blog/what-is-claude-code-chyros-background-daemon)
- **核心**：Anthropic 未发布的"永远在线"后台 daemon，响应 CI 失败、PR 打开、定时器等事件。
- **启发**：即使 Anthropic 都在往"进程级 agent daemon"走，V5 应直接把 agent 设计成 daemon。

### 1.6 Generative Agents / Smallville（Stanford Park 2023）
- [arXiv 2304.03442](https://arxiv.org/abs/2304.03442)
- **核心**：memory stream（时间戳 + 自然语言）+ 检索打分 `score = α_recency × recency + α_importance × importance + α_relevance × relevance`（三者通常等权 1:1:1，归一化 [0,1]）+ **importance sum ≥ 150 触发 reflection**（一天约 2-3 次）+ 每日 plan（粗到细递归）。
- **启发**：V5 需要 importance score 累计器决定何时"反思"。

### 1.7 MemGPT（arXiv 2310.08560）
- **核心**：分层 context（main = RAM；external = disk），LLM 自己调 tool 管理自己的内存，token 接近阈值触发自我 summarize。
- **启发**：V5 的"tension / witness / learning" 也应该做成 LLM 可自主调用的 memory-ops 工具。

### 1.8 Reflexion / Society of Minds / Chain-of-Verification
- **Reflexion** arXiv 2303.11366：三模块 Actor / Evaluator / Self-Reflection；每 episode 用 verbal feedback 存 episodic memory。HotpotQA 30% → 60%。
- **Society of Minds multi-agent debate** arXiv 2305.14325：多个 LLM 实例辩论若干轮再汇总。
- **MAR** arXiv 2512.20845：单 reflector 升级成 persona-critic 群。

### 1.9 A-Mem（arXiv 2502.12110）
- **核心**：Zettelkasten 风格的 agentic memory——每次新 memory 自动生成 context description / keywords / tags，并智能建立跨节点连接。
- **启发**：V5 的 `wiki/` 知识库应该做成 Zettelkasten 链接图。

### 1.10 Dual-Process LLM Agent 突破（2025-2026）
- **DPT-Agent** arXiv 2502.11882（2025-02）：**System 1 = FSM + code-as-policy**（每 0.25s 出动作）；**System 2 = ToM + async reflection**（后台线程）。S2 更新 S1 的策略代码，S1 一直响应用户。**最清晰的 fast/slow 解耦实现**。
- **DPA (Dual-Process Agent)** MDPI 2026-03：System 1 检索响应；System 2 反思写回 memory + conservative curator gate 防污染。
- **DUPLEX** arXiv 2603.23909：Qwen3-8B 做 Fast System 提实体关系 → PDDL symbolic planner；GPT-4o 做 Slow System。
- **DualSpec** arXiv 2603.07416：deep research agent action speculation，Fast path 投机 action，Slow path 校验。
- **CogRouter** arXiv 2602.12662：ACT-R 四层 cognitive depth，step-level 路由。

### 1.11 Proactive agent 研究
- **ProactiveAgent (THUNLP)** arXiv 2410.12361：Activity Watcher 监听 VSCode/browser/window focus → 6,790 event 数据集 → 训练 reward model（F1 **0.918**）作 accept/reject 分类器 → finetuned LLM + reward filter。
- **ContextAgent** NeurIPS 2025 arXiv 2505.14668：多模态 sensory → 抽 context + persona → 预测是否主动 → 调工具。比 rule-based 好 8.5%/6%。
- **ProAgent PKU**（AAAI 24 Oral）：多人游戏主动 cooperative agent。
- **LangChain Ambient Agents**：event stream 触发 + Agent Inbox UI + 三模式（notify / question / review）。

### 1.12 Cursor 2.0 background agents
- [docs.cursor.com/en/background-agent](https://docs.cursor.com/en/background-agent)
- **核心**：cloud 环境 clone repo，后台并行跑最多 8 个 agent，自动选最优，git worktree 隔离。

### 1.13 Anthropic multi-agent research system
- [anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system)
- **核心**：lead agent (Opus) 起 3-5 个 subagent (Sonnet) 并行。对 open-ended research 比单 agent 高 **90.2%**。token 用量 15×。
- **启发**：慢车道可用多 subagent 并行反思，对应宪法第 3 条"对立面真诚"。

### 1.14 延迟 vs 深度
- **Claude 3.7 extended thinking**：thinking display = omitted 减小首字符延迟；5k thinking token 加 5-15s 延迟。
- **OpenAI o3-mini**：三档 reasoning effort；比 o1-mini 首 token 快 2.5s。
- **Microsoft Agent Framework background responses**：continuation token + 可恢复 stream。
- **Google ADK streaming tools**：async generator，长任务边跑边 yield 中间结果。

---

## Part 2：Dual-Process 架构深度拆解

### 2.1 Letta sleep-time（最贴近 V5）

**怎么分**：进程/异步线程级分离。两个 agent，共享 **memory block**（context window 里的带标签字段，有字符上限）。primary agent 拥有 `conversation_search` / `archival_memory_search` 工具；sleep-time agent 拥有修改 primary memory block 的工具。

**何时触发慢路径**：Step-based，primary 每跑 N 步（默认 5）系统把最近消息 push 给 sleep-time。可配 `sleeptime_agent_frequency`。

**慢路径做什么，怎么反哺**：读 primary 最近消息 → 反思 → **直接覆写** primary 的 memory block。primary 下一次打 context 时自然读到最新 learned context。**不走消息队列，走共享状态**。

**用户体感延迟**：官方声明 primary 不等 sleep-time。快路径延迟 = 普通 ReAct。慢路径完全异步。

**失败模式**：token 爆炸（每次触发跑一整轮 LLM）；block 写冲突（多 sleep agent 对同 block，无锁）；语义漂移（sleep-time 可能把正确 memory 改错）。

### 2.2 DPT-Agent（最严格的 dual-process）

**怎么分**：**线程 + 角色分离**。
- **System 1** = FSM + code-as-policy。每 0.25s tick 必须输出一个 macro action。FSM 里跑的是 LLM 生成过的 Python 代码，不再调 LLM。
- **System 2** = LLM 后台线程。跑 Theory of Mind（推断人的意图）+ asynchronous reflection（更新指导原则）。

**何时触发慢路径**：基于 history buffer 长度。每间隔 λ 步，把 buffer 交给 S2。λ 可配，与 action frequency 完全解耦。

**慢路径怎么反哺**：S2 输出两个东西：
  1. **Human belief** `b^n = LLM(τ₀:tₙ, b^(n-1))`——对人的推断，累积更新。
  2. **Guidelines** `g^m = LLM(τ₀:tₘ, b^n, g^(m-1))`——给 S1 code generator 的自然语言指导。

S1 的 code generator 下一次被调用时，把最新 guidelines 喂进去，生成新的策略代码。**不是即时覆盖，而是"下一次 code 生成"时生效**。

**用户体感延迟**：S1 延迟 = FSM 转一次 + 代码执行，毫秒级。论文声明每 tick 0.25s 不 miss。S2 延迟完全不影响用户。

**失败模式**：S2 跑太慢 S1 一直用旧策略；Code-as-policy 生成出错 FSM 崩，保留 fallback；ToM 推断错误放大到 guidelines → 放大到 code → agent 行为偏。

### 2.3 Generative Agents 的 reflection（最成熟的触发机制）

**怎么分**：时间轴分离。memory stream，观察类 memory 每次都写；reflection 类 memory 周期性生成。

**何时触发**：最近 memory 的 importance score 累计 ≥ 150。一天约 2-3 次。
1. LLM 基于最近 100 条 memory 生成 3 个 "salient high-level questions"。
2. 每个 question 做检索（recency × importance × relevance 等权）。
3. LLM 对检索结果生成 5 条 insight，每条带证据指针。
4. Insight 写回 memory stream，自身也有 importance score，可被下一轮反思当输入——形成 reflection tree。

**慢路径反哺**：反思结果就是新的 memory 条目，下次检索时和原始观察平等竞争。

**失败模式**：阈值 150 是超参，不同 domain 需重调；一天奇葩事件（火灾）瞬间爆表连续触发 reflection 浪费 token；reflection tree 深了检索权重偏向高层抽象，丢失原始细节。

### 2.4 Claude Code Auto Dream（生产级"慢路径"工程范本）

**怎么分**：完全进程级。会话期间不触发，进程空闲/新启动时检查。

**何时触发**：**双门 AND**——距上次 dream ≥ 24h **且** 期间 ≥ 5 个 session。

**做什么（4 阶段，8-9 分钟跑 913 session）**：
1. **Orientation**：扫 memory 目录 + MEMORY.md。
2. **Gather signal**：grep 风格**targeted 搜索**（不全读 transcript）找 correction / 显式 save / 重复 pattern / 架构决策。
3. **Consolidation**：相对日期 → 绝对日期、删矛盾、去陈旧、合重复。
4. **Prune + index**：MEMORY.md 保持 ≤ 200 行，重排相关性。

**反哺**：只写 memory 文件，**源码/配置/测试文件一律只读**。锁文件保证单并发。下次会话启动读到的 MEMORY.md 是 dream 后版本。

### 2.5 四个方案对比

| 维度 | Letta sleep-time | DPT-Agent | Generative Agents | Claude Auto Dream |
|---|---|---|---|---|
| 解耦粒度 | 进程 + 共享 memory | 线程 + code 生成 | 时间轴 | 进程 + 文件 |
| 触发 | 每 N 步 | 每 λ 时间 | importance ≥ 150 | 24h + 5 session |
| 慢→快通道 | 覆写 block | 更新 guidelines → 下次 code gen | 写入 memory stream | 写入 MEMORY.md |
| 用户延迟 | 0（异步） | 0（线程） | N/A | 0（会话外） |
| 主要失败 | token 爆炸 + 写冲突 | S2 慢/错传播 | 阈值调参 | 误删 |

**结论**：Letta + Auto Dream 的**共享状态 + 多触发门 + 只写隔离区**组合最贴近 V5。DPT-Agent 的**策略 vs 执行分离**在延迟敏感下最严格。Generative Agents 的**importance 累计触发**是最天然的认知心理学对齐。

---

## Part 3：Proactive 的 3 种实现模式

### 3.1 规则触发（时间 / 事件）· 占 40%

**机制**：外部 event stream（Slack / 邮件 / CI / cron）进入，agent 在 subscribe 的事件上醒来。

**代表**：
- **LangChain Ambient Agents + Agent Inbox**：email agent 参考实现，Slack Bolt webhook → LangGraph run → 三模式选择。
- **Claude Code Chyros**（未发布）：响应 CI fail / PR open / cron。

**代码核心**：webhook + LangGraph persistence。state 保存后 agent 可"暂停 waiting"。

**优点**：确定性强，成本可控。
**缺点**：事件集合要预定义。

### 3.2 记忆触发（"N 天没联系 → 关心"）· 占 30%

**机制**：agent 周期性扫 memory，对符合某 pattern 的记忆打分，超阈值触发主动。

**代表**：
- **Replika proactive**："Replika shows up when something's on your mind"——具体算法未公开。
- **Generative Agents plan loop**：每天早上 agent 生成粗 plan，执行时 memory retrieval 影响 next action。
- **ProactiveAgent** 训练了 0.918 F1 分类器判断"该不该主动"。

**代码核心**：`for memory in recent_memories: if trigger_condition(memory) and time_decay(memory) > τ: schedule_proactive_action()`。

**优点**：贴近"人类主动想起朋友"。
**缺点**：需要记忆基础结构足够好；容易变 spam。

### 3.3 自我驱动（agent 觉得该做点什么）· 占 30%

**机制**：agent 在 idle 时做 reflection/evaluation，发现差距触发 action。**内源驱动**。

**代表**：
- **Generative Agents reflection**：importance 累积触发。
- **Sleep-time Compute**：agent 在用户没问时自己"预推理 likely queries"。
- **AgentEvolver / EvolveR / ACE**（2025-2026 自我进化系列）：agent 自己发现 skill gap，自己 propose task。

**代码核心**：
```python
while True:
    sleep(interval)
    tension = measure_internal_state()
    if tension > threshold or time_since_last_action > T:
        proactive_plan = slow_reflect(memory, goals)
        if proactive_plan.confidence > τ:
            execute_or_notify(proactive_plan)
```

**优点**：真正"有灵魂"。
**缺点**：tension / confidence 怎么定义是核心难题。

---

## Part 4：V5 架构建议

### 4.1 快车道（fast path）

**建议**：**Letta V1 agent loop + native reasoning + streaming**。
- 主循环单一 ReAct，不嵌 sleep-time 调用。
- Claude 4.7/GPT-5 native reasoning token，设 `thinking display = omitted` 减小首字符延迟。
- Context 构造：`[宪法 + 当前 learned_context + 最近 10 条对话 + 召回 5 条 memory + 当前 tension 状态 + user query]`。
- Tool call 走 streaming tool（Google ADK 范式）。
- **首字符目标 < 2s**，完整响应 < 10s。

### 4.2 慢车道（slow path / breath）

**建议**：**Letta sleep-time + Auto Dream 双门 + DPT-Agent 策略反哺**融合。

**三层架构**：

1. **Tier 1 · 响应后微反思（每次对话后 fire-and-forget）**
   - 约 2-3s，复用当前 LLM，更新 `tension` / 写 witness / 更新 learned_context 一个字段。
   - 不阻塞用户。

2. **Tier 2 · 周期呼吸（daemon，每 5-15 分钟）**
   - Generative Agents **importance 累积 ≥ 阈值**决定是否 reflection。阈值按 V5 12 对 tension 加权。
   - 产出：刷新 tension；生成 salient question + insight；写入 memory + wiki。

3. **Tier 3 · 深度 dream（每日定时）**
   - 模仿 Auto Dream 双门：满 24h 且满 N 次会话。
   - 四阶段：orientation → gather signal → consolidate → prune。
   - **安全边界**：dream 只写 `memory/` 和 `wiki/`，代码/配置只读；锁文件防并发。
   - 可跑 multi-agent debate（Society of Minds）做深度对立面审查。

**慢→快反哺**：**共享 memory block**（Letta 风格），快车道读"最后成功写入版本"，不等 in-flight 写。**版本号保护**，**单 slow 实例 + 锁文件**。

### 4.3 主动车道（proactive）

**建议**：**三触发并存**——规则 + 记忆 + 自我（40% / 30% / 30%）。

1. **规则触发**：LangGraph ambient 范式，Agent Inbox 三模式（notify / question / review）。
2. **记忆触发**：daemon 每 15 分钟扫 memory，`time_since_last × importance × emotional_weight` 打分。draft 过"是否打扰"分类器（ProactiveAgent 的 0.918 F1 思路）。
3. **自我驱动**：tension 超阈值触发 witness + action proposal；sleep-time compute **查询预测**。

**怎么决定发什么**：draft → "是否该发" 分类器 → "语气风格" refiner → 发。记录反馈训练 reward model。

**平衡不打扰**：
- 硬规则：每用户每天 ≤ 3 条主动；每 topic 两次主动间隔 ≥ 12h。
- 软规则：reward model "打扰度" × "价值" 做阈值。
- 用户"别烦"永久降权（permanent flag）。

### 4.4 三车道的数据共享

**共享什么**：
- **memory stream**（Generative Agents 风格，append-only）
- **learned_context block**（Letta 风格，10-15 个命名 block）
- **wiki 链接图**（A-Mem Zettelkasten 风格）
- **tool trace**（Hermes 启发）

**冲突处理**：
- **写权限分层**：
  - 快车道可写 memory stream、tool trace。**不能写 learned_context**。
  - 慢车道可写 memory stream（含 reflection）、learned_context block。**不能写 constitution**。
  - 深度 dream 可写 wiki（除 constitution）、learned_context、prune memory。
  - 主动车道只写 proactive queue 和反馈表。
- **锁**：learned_context 用 file lock；dream 全局一把锁。
- **读取**：快车道读"最近一次成功写入的快照"，不等 in-flight 写。

**一致性**：最终一致（1-10s）。不追求跨车道事务。

### 4.5 参考架构图

**V5 = Letta V1 骨架 + Auto Dream 四阶段（dream 层）+ DPT-Agent 策略反哺（breath 层）+ LangGraph Ambient Inbox（proactive 层）**

```
                    ┌──────────────────────────────────┐
                    │         Shared State             │
                    │  Memory stream · Learned context │
                    │  Wiki Zettel · Tool trace        │
                    └──────┬────────┬────────┬─────────┘
                      read │   read │   read │write
        ┌────────────────┐ │        │        │  ┌─────────────────┐
        │  FAST LANE     │ │        │        │  │  PROACTIVE LANE │
        │  Letta V1      │─┘        │        │  │  LangGraph      │
        │  ReAct + stream│          │        │  │  Ambient        │
        │  TTFT < 2s     │  append  │        │  │  3 triggers     │
        │  Total < 10s   │──────────┤        │  │  Inbox UI       │
        └────────────────┘          │        │  └─────────┬───────┘
                                    │        │            │
                    ┌───────────────┴────────┴─────┐      │
                    │  SLOW LANE (3 tiers)        │◄─────┘
                    │  Tier 1: micro reflect 2-3s  │
                    │  Tier 2: breath daemon 15min │
                    │  Tier 3: deep dream 24h+5ss  │
                    └──────────────────────────────┘
```

---

## Part 5：5 个必避陷阱

1. **阻塞等待慢车道（V1-V3 老毛病）**
   用户发消息→agent 先跑完反思→再回。**永远不要**。Letta 明确 primary 不等 sleep-time；DPT-Agent S1 不等 S2。快车道读"上次成功写入"的 learned_context。

2. **慢车道无门，LLM 账单爆炸**
   Letta 警告：sleep-time 频率设 1 会"diminishing returns"。Auto Dream 双门（24h + 5 session）对抗。V5 每 slow tier 配触发门，每天最多 dream 1 次。

3. **主动 = 打扰**
   Replika proactive 被评测吐槽"像 spam"。ProactiveAgent 训 0.918 F1 reward model 过滤。**2 道门**：是否该发 + 语气合适。用户"别烦"永久降权。

4. **多 slow 实例并发写同 memory block**
   Letta sleep-time "experimental unstable" 主要来自写冲突。**V5 慢车道 daemon 全局单例 + 文件锁**。

5. **反思不落地只是字符串**
   Reflexion / A-Mem / Generative Agents 共同陷阱：反思产出的 text 没回 action loop。**V5 必须让反思以结构化字段（tension 值、learned_context 命名 block、proactive queue entry）直接被快车道读取**。

---

## Sources

- [Letta Sleep-Time Agents Guide](https://docs.letta.com/guides/agents/architectures/sleeptime)
- [Sleep-time Compute paper arXiv 2504.13171](https://arxiv.org/abs/2504.13171)
- [Rearchitecting Letta V1 agent loop](https://www.letta.com/blog/letta-v1-agent)
- [Generative Agents paper arXiv 2304.03442](https://arxiv.org/abs/2304.03442)
- [MemGPT arXiv 2310.08560](https://arxiv.org/abs/2310.08560)
- [Reflexion arXiv 2303.11366](https://arxiv.org/abs/2303.11366)
- [Society of Minds multi-agent debate arXiv 2305.14325](https://arxiv.org/abs/2305.14325)
- [A-Mem arXiv 2502.12110](https://arxiv.org/abs/2502.12110)
- [DPT-Agent arXiv 2502.11882](https://arxiv.org/abs/2502.11882)
- [Self-Evolving-Agents DPA MDPI 2026](https://www.mdpi.com/2079-9292/15/6/1232)
- [DUPLEX arXiv 2603.23909](https://arxiv.org/html/2603.23909v1)
- [Proactive Agent arXiv 2410.12361](https://arxiv.org/abs/2410.12361)
- [ContextAgent arXiv 2505.14668](https://arxiv.org/abs/2505.14668)
- [Voyager arXiv 2305.16291](https://arxiv.org/abs/2305.16291)
- [Claude Auto Dream guide](https://claudefa.st/blog/guide/mechanics/auto-dream)
- [Claude Code Chyros source leak](https://www.mindstudio.ai/blog/what-is-claude-code-chyros-background-daemon)
- [LangChain Introducing Ambient Agents](https://blog.langchain.com/introducing-ambient-agents/)
- [Anthropic multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)
- [Cursor background agents docs](https://docs.cursor.com/en/background-agent)
