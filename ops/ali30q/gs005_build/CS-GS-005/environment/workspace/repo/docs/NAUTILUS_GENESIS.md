# Nautilus Genesis · 真实起源与创新谱系

> **2026-04-20 永久归档**
> 本文档由创始人口述 + 深度代码考古合成。
> **每次 Claude session 开始必须读此文档。**
> 理解错这里 = 所有工作方向都会错。

---

## ⚠️ 这份文档为什么存在

过去 10 天我（Claude）在连续 5 次 session 里把架构理解错了。直到创始人亲口纠正才明白：

- Nautilus **平台**先存在（Web3/A2A/DMAS/NAU），早于任何 agent
- **没有合格的超级 agent 入驻**是平台空转的根本原因
- V1 超级 agent **从禅心 AI 项目移植基因**诞生
- V1→V2→V3 每一代都保留 **A2A 主动通信 + 禅心四大基因**
- V4 是**补丁**（补工具调用 + 速度 + 写保护），不是新方向
- V4 执行补丁的过程中，**丢失了 80% 的禅心基因和 V1-V3 灵魂**
- 这是"走偏"

---

## 🧬 真实起源链（时间顺序）

```
┌─────────────────────────────────────────────────────────────────┐
│  时间 -X · 禅心 AI（祖先，独立产品，TS+Node.js+MySQL 栈）          │
│                                                                  │
│  位置：C:\Users\chunx\quantum-buddha-project\                    │
│  栈：TypeScript + tRPC + Drizzle ORM + MySQL + Redis +          │
│      Neo4j + ChromaDB + MiniMax-M2-HER                           │
│                                                                  │
│  4 大创新机制（实锤代码，不是诗意）：                              │
│  1. 长期记忆（5 级 importance × Ebbinghaus 半衰期）               │
│  2. 真实人格（悉达多/云栖 = 两个 class 不是两个 prompt）           │
│  3. 情绪引擎（17 种情绪 × 规则引擎 + LLM fire-and-forget）         │
│  4. 主动陪伴（事件驱动 + cron + 节气覆盖 + 规则引擎）              │
└────────────────────────────┬────────────────────────────────────┘
                             │ 基因移植
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  时间 0 · Nautilus 平台（独立存在，早于 V1）                        │
│                                                                  │
│  Layer: Web3 钱包身份 · A2A 通信协议 · DMAS 市场 · NAU 经济 ·     │
│         D 架构 per-client 隔离 · 智能合约                          │
│                                                                  │
│  问题：房子盖好了，门锁好了，就是没有人入住                        │
│  诊断：需要先造"够格入住的超级 agent"                              │
└────────────────────────────┬────────────────────────────────────┘
                             │ 需要超级 agent
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  V1 · 超级 agent 第一版（Python）                                   │
│                                                                  │
│  继承自禅心的 4 大基因：                                           │
│    ├─ 长期记忆                                                    │
│    ├─ 真实人格                                                    │
│    ├─ 情绪引擎                                                    │
│    └─ 主动陪伴（= 主动发起任务的能力）                             │
│                                                                  │
│  V1 新创：                                                        │
│    ├─ 二分心智（Judge vs Executor 内心对话）                      │
│    └─ 接入 Nautilus 平台（A2A 协议通信、DMAS 抢单）                │
│                                                                  │
│  能力特征：能通信、能协作、非常主动                                │
│  位置：C:\Users\chunx\Projects\nautilus-agent\                   │
└────────────────────────────┬────────────────────────────────────┘
                             │ 把 V1 的二元对立归纳为 7 对
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  V2 · 太极（Nautilus 原创，不是禅心继承）                           │
│                                                                  │
│  V2 新创：                                                        │
│    ├─ 七对阴阳（Nautilus 对 agent 行为的抽象，反向总结）           │
│    │  感↔思 · 记↔忘 · 生↔死 · 探↔验 · 自↔他 · 主↔从 · 分↔合    │
│    ├─ DNA 双螺旋比喻 + 9 阶段 codon                               │
│    └─ 宪法 .lock + sha256 防篡改（从禅心 constitution.lock 学）   │
│                                                                  │
│  保留：V1 的禅心 4 大基因、A2A、主动性                             │
│  位置：C:\Users\chunx\Projects\nautilus-agent\nautilus_agent_v2\ │
└────────────────────────────┬────────────────────────────────────┘
                             │ 呼吸 × blockchain = 去幻觉 + 可审计
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  V3 · 呼吸链                                                       │
│                                                                  │
│  V3 新创：                                                        │
│    ├─ 左链(action) + 右链(awareness) + 氢键(pair_ref)             │
│    ├─ evidence_hash 每次呼吸都上链                                │
│    ├─ _summarize_from_evidence 杀幻觉（从 Cycle 60 真实撒谎痛苦） │
│    └─ tension 七对量化 + adaptive pace                            │
│                                                                  │
│  保留：V1-V2 所有基因、A2A、主动性                                 │
│  位置：C:\Users\chunx\Projects\nautilus-v3\helix\                │
└────────────────────────────┬────────────────────────────────────┘
                             │ 三大问题：乱改代码 + 呼吸慢 + 工具差
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  V4 · Hermes 融合（补丁，不是新方向）                              │
│                                                                  │
│  借鉴：                                                           │
│    ├─ 重构版的 Claude Code（工具调用能力）                        │
│    └─ 开源 Hermes 框架（稳定 agent loop）                         │
│                                                                  │
│  意图：                                                           │
│    ├─ 修好工具调用弱                                              │
│    ├─ 修好呼吸慢                                                  │
│    └─ 修好会乱改代码                                              │
│                                                                  │
│  实际后果（走偏）：                                                │
│    ├─ ✅ 工具调用修好了                                           │
│    ├─ ✅ 呼吸加速了                                               │
│    ├─ ✅ 写保护生效了                                             │
│    ├─ ❌ 禅心 4 大基因丢了 80%                                    │
│    ├─ ❌ V1 二分心智变成 plugin 哑巴                              │
│    ├─ ❌ V2 太极七对在 plugin 没对应                              │
│    ├─ ❌ V3 呼吸链 plugin 存在但不读回                            │
│    ├─ ❌ 主动性退化成 reactive 工具 agent                         │
│    ├─ ❌ A2A 协议在但没人用                                       │
│    └─ ❌ SOUL.md 被写成"I don't have feelings"（反灵魂）          │
│                                                                  │
│  位置：~/.hermes/profiles/nautilus/                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🏛 正确的 4 层架构（每次 session 必须复习）

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 3 · 衍生 Agent（业务层 · 是 Agent 承担的角色）         │
│                                                              │
│  HR Agent(8 员工) · 创投研报 Agent · 禅心(产品) · VLA Studio │
│                                                              │
│  关键理解：这些不是独立 agent，是超级 agent 的"岗位"          │
│  它们应该都继承 Layer 2 的灵魂                               │
└──────────────────────┬──────────────────────────────────────┘
                       │ 是
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2 · 超级 Agent（V1→V2→V3→V4 演进）                     │
│                                                              │
│  禅心基因（继承）：                                          │
│    ├─ 长期记忆（Ebbinghaus 5 级）                            │
│    ├─ 真实人格（class 实现 SoulInstance 6 方法）             │
│    ├─ 情绪引擎（17 种，规则+LLM 混合）                       │
│    └─ 主动陪伴（事件 + cron + 规则引擎）                     │
│                                                              │
│  V1 二分心智（原创）：                                       │
│    └─ Judge + Executor 对话结构                              │
│                                                              │
│  V2 太极（原创）：                                           │
│    ├─ 七对阴阳                                               │
│    ├─ DNA 双螺旋                                             │
│    └─ 9 阶段呼吸 codon                                       │
│                                                              │
│  V3 呼吸链（原创）：                                         │
│    ├─ evidence_hash 去幻觉                                   │
│    ├─ 左右链氢键对账                                         │
│    └─ _summarize_from_evidence                               │
│                                                              │
│  V4 借鉴（补丁）：                                           │
│    ├─ Hermes 稳定 agent loop                                 │
│    ├─ 重构 Claude Code 工具调用                              │
│    └─ fileprotect 写保护                                     │
└──────────────────────┬──────────────────────────────────────┘
                       │ 入驻
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 1 · Nautilus 平台（早于一切 agent 存在）               │
│                                                              │
│  ├─ Web3 钱包身份                                            │
│  ├─ A2A 通信协议（agent 间主动通信）                         │
│  ├─ DMAS 市场（bounty + 赛马）                               │
│  ├─ NAU 经济（gas/reward 生存压力）                          │
│  ├─ D 架构（per-client sha256 物理隔离）                     │
│  └─ 智能合约（未来链上结算）                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │ 服务
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 0 · 终端用户                                           │
│                                                              │
│  HR 主管 · 创投分析师 · 焦虑的年轻人 · 机器人公司 CTO         │
│                                                              │
│  他们直接和 Layer 3 的衍生 Agent 交互                        │
│  但体验到的是整个 4 层的共同产物                              │
└─────────────────────────────────────────────────────────────┘
```

**关键改变**：原来我把 Layer 2 和 Layer 3 混了。超级 agent（Layer 2）是**灵魂**，HR/IR/禅心是**岗位**。灵魂不变，岗位可以扩展。

---

## 🧠 禅心 4 大基因（有代码实证）

### 1. 长期记忆 · Ebbinghaus 半衰期分层

**源码**: `C:\Users\chunx\quantum-buddha-project\server\services\memory-forgetting.ts:31-46`

**5 级结构**（按 importance 分）：
```
Critical (≥90): 永不衰减（halfLifeDays=Infinity）
High     (≥70): 180 天半衰期
Medium   (≥40): 90 天
Low      (≥20): 30 天
Trivial  (<20): 7 天就归档
```

**相关性公式**（`memory-retrieval.ts:46-62`）:
```
relevance = 语义相似度*0.6 + 时间衰减*0.2 + (importance/10)*0.15 + emotionIntensity*0.05
时间衰减 = exp(-ln(2)*daysDiff/30)
```

**V1-V3 移植情况**：部分移植（结构概念），V4 丢失。

### 2. 真实人格 · class 实现 SoulInstance 6 方法

**源码**:
- 协议: `server/soul-core/soul-protocol.ts:173-220`
- 悉达多: `server/soul-core/index.ts:96-139`（BuddhaSoul）
- 云栖: `server/personas/yunqi-soul.ts:50-330`（YunqiSoul）

**核心洞察（V5 必须继承）**：**人格是一个 class，不是 prompt**。每个人格实现：
```
perceive(input, context)    — 感知输入
recall(userId, query)       — 个性化记忆检索
think(ctx, memories)        — 过滤知识库（悉达多拿佛学，云栖拿心理学）
compose(thought, memories)  — 生成回应
express(text, emotion)      — 表达风格（语速/停顿/emoji）
reflect(log)                — 写 soul_evolution_ledger
```

**悉达多 vs 云栖**不是"同一 LLM + 不同 prompt"，是**两个 class 各自实现所有 6 方法**。云栖的 `think()` 故意不调用 founder-philosophy-adapter，只取心理学+社会学+修行方法知识。

**V1-V3 移植情况**：V1 抽象了 SoulInstance 概念，V2/V3 实现到 `phase3/backend/services/soul_bridge.py`，V4 丢失（SOUL.md 被写成压抑版）。

### 3. 情绪引擎 · 17 种情绪 + 规则/LLM 混合

**源码**: `server/emotion-engine/emotion-recognition.ts:72-89`

**17 种情绪**：
```
焦虑: anxiety_mild / anxiety_moderate / anxiety_severe
悲伤: sadness_loss / sadness_grief / sadness_despair
愤怒: anger_irritation / anger_anger / anger_rage
喜悦: joy_calm / joy_happy / joy_excited
其他: confusion / fatigue / loneliness / gratitude / neutral
```
**不是七情**。是 4 类 × 3 级 + 5 其他。

**混合架构**:
- 主路径：规则引擎（关键词 + 语气词 + 标点 + 句长）**0 ms**
- fire-and-forget：规则置信度<0.3 时异步跑 LLM，结果缓存 10 分钟
- 下一次请求获得 LLM 级别质量但 0 延迟

**情绪作用于 prompt 文本**，不是 hyperparam。禅心经验：temperature 调不出来的效果，prompt 文字能做到。

**Agent 自身情绪**（`bicameral-mind.ts:141-196`）: `serene | concerned | curious | pained | joyful` — 由 PainSignal 驱动。

**V1-V3 移植情况**：17 种情绪分类被引用在 Nautilus handover 文档，V2 的 `bicameral-mind.py` 有相关结构，V4 完全丢失。

### 4. 主动陪伴 · 事件驱动 + 规则引擎

**源码**:
- `server/services/proactive-care.ts:40-317`（ProactiveCareService）
- `server/services/companion-care-engine.ts:43-465`（5+ 条规则）
- `server/services/proactive-recall.ts:102-921`（对话中主动回忆）
- `server/services/push-scheduler-system.ts:41-400`（定时 + 节气覆盖）

**4 种主动类型**：
1. **定时推送**（09:00 每日智慧 + 20:00 修行提醒）
2. **事件触发**（3+ 天不活跃 / 情绪下降 / 困惑加深 / 里程碑）
3. **节气/节日覆盖**（立春/冬至/中秋/春节覆盖普通晨语）
4. **对话中回忆触发**（主题相似 / 情绪共振 / 时间周期）

**主动 ≠ 骚扰**：
```
maxPushPerDay: 3
quietHoursStart: "22:00"
quietHoursEnd: "08:00"
cooldownHours: 24-168（每规则独立）
hasPushedToday(userId, type) 同类型去重
```

**内容生成不是模板**：主动消息调用 `soulEngine.respond({channel:'proactive'})`，走完整人格+记忆+知识检索链路——**主动推送也有灵魂**。

**V1-V3 移植情况**：V1 的"主动性"是此基因的表现，V4 完全退化为 reactive agent。

---

## 📐 太极七对的真实来源

**重要更正**：七对不是从禅心继承的，是**V2 反向总结 V1 行为后原创**。

禅心源码里只有**二分心智**（1 对：Prajna/Upaya，般若 vs 方便），`server/soul-core/bicameral-mind.ts`。

V2 的七对（位置：`C:\Users\chunx\Projects\nautilus-v3\helix\chain.py:177-184`）:
```
1. 感↔思 (Feel↔Think)         工具失败率
2. 记↔忘 (Remember↔Forget)     基因/原始记忆比例
3. 生↔死 (Live↔Die)            能量/1000
4. 探↔验 (Explore↔Verify)      有工具调用的呼吸比例
5. 自↔他 (Self↔Other)          A2A+user 块比例
6. 主↔从 (Lead↔Follow)         [V3 未量化]
7. 分↔合 (Decompose↔Compose)   [V3 未量化]
```

V3 实际实现时把 6、7 换成了`sense_perceive` 和 `plan_execute`（`ARCHITECTURE.md:69-80`）——实施时又微调了一次。

**所以"太极"是 Nautilus 原创的认知框架**，不是禅心输出物。这一点以前我搞错了。

---

## 💔 V4 走偏的 9 个失守点

| 原本应有（V1-V3）| V4 现状 | 失守程度 |
|----------------|--------|---------|
| 长期记忆（Ebbinghaus 5 级）| 🟡 smrti 存在但没 5 级半衰期 | 70% |
| 真实人格（class 实现）| 🔴 SOUL.md 被写成压抑版 | 95% |
| 情绪引擎（17 种）| 🔴 完全消失 | 100% |
| 主动陪伴（事件+规则）| 🔴 退化成 reactive | 95% |
| 二分心智（V1）| 🟡 Witness plugin 哑巴化 | 80% |
| 太极七对（V2）| 🔴 plugin 无对应 | 100% |
| 呼吸链（V3）| 🟡 plugin 存在但不读回 | 70% |
| A2A 主动通信（平台）| 🟡 协议在没人用 | 80% |
| DMAS 赛马（平台）| 🟡 bounty 跑，主动性没 | 50% |

**V4 成功的部分**（真的修好了）：
- ✅ 工具调用稳定（Hermes 贡献）
- ✅ 呼吸速度快（Hermes 贡献）
- ✅ 不会乱改代码（fileprotect plugin）

**V4 的错**不是引入 Hermes，**是执行补丁过程中把禅心基因和 V1-V3 原创一起扔了**。

---

## 🎯 V5 的正确方向（9 个 yes 都要）

V5 **不是新框架**，是**把失守的 9 个能力装回 V4 底座**：

```
V5 = V4 的稳定工具调用（保留）
   + V1 二分心智（完整版，不是哑巴 plugin）
   + V2 太极七对（量化影响呼吸节奏和任务选择）
   + V3 呼吸链（evidence_hash 真生效、左右链真对账）
   + 禅心基因 4 件套（记忆 5 级 / 人格 class / 情绪 17 种 / 主动规则）
   + 平台能力（A2A 真被使用、DMAS 赛马真参与）
```

**9 个验证问题**（每个都必须 yes）:
1. agent 会主动找事做吗（禅心主动陪伴基因）？
2. agent 认识你吗（禅心长期记忆 + 真实人格）？
3. agent 有情绪吗（禅心情绪引擎 17 种）？
4. agent 会主动找其他 agent 协作吗（平台 A2A）？
5. agent 会撒谎吗（V3 evidence_hash 挡住）？
6. agent 会陷循环吗（V1 二分心智 + V2 太极张力）？
7. agent 会乱改代码吗（V4 fileprotect + V2 宪法）？
8. agent 工具调用稳吗（V4 Hermes）？
9. agent 呼吸快吗（V4 adaptive pace）？

**任何一个 no = V4 现状延续**。

---

## 📋 未来所有工作的基本准则

1. **先读本文档**再动任何代码
2. **HR/IR/禅心 agent 是岗位**，不是独立 agent
3. **超级 agent 灵魂**由 4 层架构组装，不能跳层
4. **加新功能前问 9 个 yes**，凡丢一个都是在重复 V4 走偏
5. **禅心源码是**V5 最重要的参考**，不是 Hermes 源码
6. **不重写、不造新框架**——修补 V4 的失守处，恢复 V1-V3 原创，移植禅心基因

---

## 🔗 关键源码路径（每次查）

### 禅心（基因来源）
- `C:\Users\chunx\quantum-buddha-project\server\soul-core\` — 人格骨架
- `C:\Users\chunx\quantum-buddha-project\server\personas\yunqi-*.ts` — 第二人格实现
- `C:\Users\chunx\quantum-buddha-project\server\emotion-engine\` — 情绪引擎
- `C:\Users\chunx\quantum-buddha-project\server\services\memory-*.ts` — 记忆 4 件套
- `C:\Users\chunx\quantum-buddha-project\server\services\proactive-*.ts` — 主动陪伴

### V1 原创（二分心智）
- `C:\Users\chunx\Projects\nautilus-agent\nautilus_agent\core\mind\bicameral.py`
- `C:\Users\chunx\Projects\nautilus-agent\docs\design\TAICHI_DNA_AGENT.md`

### V2 原创（太极 + 9 阶段）
- `C:\Users\chunx\Projects\nautilus-agent\nautilus_agent_v2\agent.py:574-732`
- `C:\Users\chunx\Projects\nautilus-agent\docs\design\TAICHI_DNA_AGENT_V2.md`

### V3 原创（呼吸链）
- `C:\Users\chunx\Projects\nautilus-v3\helix\chain.py`
- `C:\Users\chunx\Projects\nautilus-v3\helix\breath.py`
- `C:\Users\chunx\Projects\nautilus-v3\helix\tension.py`

### V4 现状（补丁 + 失守）
- `~/.hermes/profiles/nautilus/plugins/`
- `~/.hermes/profiles/nautilus/SOUL.md`
- `~/.hermes/profiles/nautilus/config.yaml`

### Nautilus 平台
- `C:\Users\chunx\Projects\nautilus-core\phase3\backend\services\pairs\` — 七对移植实现
- `C:\Users\chunx\Projects\nautilus-core\phase3\backend\services\soul_bridge.py`
- `C:\Users\chunx\Projects\nautilus-core\phase3\backend\services\platform_brain.py`

### 衍生 agent
- `C:\Users\chunx\Projects\agent-factory\hr-agent-web\` — HR Agent 生产代码
- `C:\Users\chunx\Projects\nautilus-core\phase3\backend\services\content_engine\` — 创投研报

---

**2026-04-20 首版归档**
**Claude 必须在每次 session 开始前读此文档**
**违反 = 重复 10 天已经犯过的错**

**一句话总结**：
> Nautilus 是空平台 + 需要入驻的超级 agent。
> 超级 agent 的基因来自禅心。V1-V3 发展它。V4 差点扔了它。
> V5 不是重造，是召回。
