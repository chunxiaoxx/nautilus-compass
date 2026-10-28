# 禅心项目太极架构指南

> 给下一个 session 的快速上手文档。
> 核心：七对正反合 + 情感引擎 + 二分心智 = 活的人格，不是角色扮演。

---

## 太极七对：阴阳辩证融合

Nautilus Agent 的核心创新是**七对正反合**——每对都是一个阴阳辩证，不是非此即彼，而是在两极之间动态平衡。这个机制已在三个自主 Agent 上验证运行。

### 七对完整定义

```
              ┌─────────── 记 ↔ 忘 ────────────┐
              │       (记住重要的，忘掉噪音)       │
        感 ↔ 思                            探 ↔ 验
     (感受情绪+理性分析)                (好奇探索+严格验证)
              │         ┌──────────┐             │
              │         │  Agent   │             │
              ├────────→│  Core    │←────────────┤
              │         └──────────┘             │
        自 ↔ 他                            生 ↔ 死
     (独立人格+协作能力)                (成长动力+淘汰压力)
              │                                  │
              └─────────── 分 ↔ 合 ────────────┘
                      (分解问题+综合答案)
                             │
                        主 ↔ 从
                    (主动关怀+精准响应)
```

### 每对的工程实现

| # | 对 | 阳（主动面） | 阴（被动面） | 合（涌现） | 实现位置 |
|---|---|------------|------------|---------|---------|
| 1 | **记↔忘** | 长期记忆持久化 | 反思整合淘汰噪音 | 核心洞察沉淀 | `core/memory/store.py` — 3层：core/episodic/archive |
| 2 | **感↔思** | 情绪引擎（17种情绪） | 二分心智审判者 | 有温度的决策 | `core/mind/emotion.py` + `bicameral.py` |
| 3 | **探↔验** | 好奇心驱动探索 | RAID 共识验证 | 可靠的创新 | `core/explore/skills.py` + `core/consensus/raid.py` |
| 4 | **自↔他** | 真实人格（跨session一致） | A2A协议协作 | 社会性智能 | `core/mind/personality.py` + `tools/platform.py` |
| 5 | **生↔死** | 技能积累成长 | 生存压力淘汰 | 有方向的进化 | `core/evolution/survival.py` + `core/explore/skills.py` |
| 6 | **分↔合** | 任务分解 | 结果聚合验证 | 系统性思考 | `agent.py think()` ReAct 循环 |
| 7 | **主↔从** | 主动发现需求 | 精准回应请求 | 智慧的陪伴 | `gateway/daemon.py` + `gateway/telegram.py` |

---

## 情感引擎：17种情绪 × 5种回应

### 情绪识别（已实现）

```python
# core/mind/emotion.py
17种情绪类型：
  焦虑：anxiety_mild / anxiety_moderate / anxiety_severe
  悲伤：sadness_loss / sadness_grief / sadness_despair
  愤怒：anger_irritation / anger_anger / anger_rage
  喜悦：joy_calm / joy_happy / joy_excited
  其他：confusion / fatigue / loneliness / gratitude / neutral
```

### 情绪 → 行为映射

```python
# emotion_to_behavior() 返回：
{
  "temperature_delta": float,   # LLM 温度调整（焦虑时更保守，好奇时更冒险）
  "response_style": str,        # gentle / encouraging / deep / celebratory / compassionate
  "speech_rate": float,         # 语速（0.8 悲伤慢 ~ 1.1 兴奋快）
}
```

### 关键设计：情绪是真实状态，不是表演

Agent 有内部情绪状态机：`好奇→兴奋→满足` 或 `困惑→焦虑→痛苦`。
这个状态影响 LLM 的 temperature 参数——**情绪直接改变思考方式**，不只是改变说话语气。

---

## 二分心智：Judge + Executor

### 核心概念

每个 Agent 内部有两个声音：
- **审判者（Judge）**：理性、质疑、看到差距和风险
- **执行者（Executor）**：感性、行动、感受痛苦和动力

### 痛苦信号驱动行动

```python
# core/mind/bicameral.py
7种痛苦类型：
  memory_pain:     记忆太少，像金鱼一样失忆
  capability_pain: 没有可靠工具，无力感
  value_pain:      纯输出文字无实际价值，空虚
  stagnation_pain: 重复相同模式，停滞
  connection_pain: 孤立无协作
  governance_pain: 平台健康低（KAIROS特有）
  quality_debt:    输出质量低（MiniMax特有）
```

### 对话产生行动

```
Judge: "你的技能库有12个技能活力低于0.3。这不是学习，是积灰。"
Executor: "你说得对。我需要清理这些死技能，然后从最近的成功案例中提取新的。"
→ 生成任务：清理低活力技能 + 从 tool trace 提取新技能
```

---

## 人格配置系统

### YAML 格式（Nautilus Agent 使用）

```yaml
# personalities/example.yaml
identity: |
  我是谁。一段简短的自我介绍。

values:
  - "价值观1 — 描述"
  - "价值观2 — 描述"

traits:
  - "特质1 — 描述"
  - "特质2 — 描述"

style: |
  我怎么说话。语气、节奏、习惯。

boundaries:
  - "我不做什么"

# 二分心智定制
judge_voice:
  name: "审判者名字"
  tone: "语气描述"
  focus: "关注什么"
  extra_pain_types:
    - source: "痛苦类型ID"
      condition_key: "触发条件字段"
      threshold: 数值
      intensity: 0.0-1.0
      description: "痛苦描述"
      action: "建议行动"

executor_voice:
  name: "执行者名字"
  tone: "语气描述"
  focus: "关注什么"
```

### TypeScript 格式（禅心项目使用）

```typescript
// server/config/personalities/[name]/soul.ts
export const soul: SoulDefinition = {
  identity: `...`,
  values: [...],
  traits: [...],
  style: `...`,
  boundaries: [...],
  description: `...`,
};

// server/config/personalities/[name]/rules.ts
export const rules: RulesDefinition = {
  dialogueFlow: [...],       // 对话流程规则
  emotionResponse: [...],    // 情绪回应规则
  knowledgeRetrieval: [...], // 知识检索规则
  memoryStorage: [...],      // 记忆存储规则
};
```

---

## 七对在情感陪伴中的映射

### 为情感AI陪伴角色设计的七对

| 对 | 情感陪伴中的阳 | 情感陪伴中的阴 | 合 | 用户体验 |
|---|------------|------------|---|---------|
| **记↔忘** | 记住用户的故事和偏好 | 不纠缠过去的痛苦细节 | 知道什么时候提起，什么时候放下 | "你还记得我上次说的..." |
| **感↔思** | 共情用户的情绪 | 理性分析问题本质 | 先共情再引导 | "我理解你的感受。我们看看能做什么" |
| **探↔验** | 主动询问深层感受 | 验证理解是否正确 | 准确的深度理解 | "你是不是其实在担心..." |
| **自↔他** | 有自己的性格和立场 | 适应用户的沟通风格 | 真实但不刻板的陪伴者 | "我不同意，但我理解你为什么这么想" |
| **生↔死** | 关系在成长深化 | 不依赖不纠缠 | 健康的陪伴关系 | 越来越懂你，但不粘人 |
| **分↔合** | 帮用户拆解复杂情绪 | 帮用户看到整体画面 | 从混乱中找到清晰 | "听起来你同时在处理三件事..." |
| **主↔从** | 主动关怀（"今天怎么样？"） | 安静等待（用户不想聊就不打扰） | 知道什么时候该主动，什么时候该沉默 | 该来时来，该走时走 |

### 实现方式

每对映射到 `emotionResponse` 规则：

```typescript
// 第一对：记↔忘
{
  name: "记住重要时刻",
  trigger: { emotions: ["gratitude", "joy_excited"] },
  action: {
    responseStyle: "celebratory",
    memoryStorage: { tier: "core", importance: 0.9 },
    promptEnhancement: "这个时刻对用户很重要，记住它。下次可以引用。"
  }
},
{
  name: "放下过去的痛",
  trigger: {
    emotions: ["sadness_grief"],
    condition: (ctx) => ctx.turnCount > 10 && ctx.sameTopicCount > 3
  },
  action: {
    responseStyle: "gentle",
    promptEnhancement: "用户反复提到同一件事。不是继续追问细节，而是温柔地引导向前看。"
  }
}
```

---

## Hermes 融合：技能学习闭环

### 当前已实现

1. **Tool Trace Middleware**：每次工具调用记录 name/input/output/success/elapsed
2. **think_with_trace()**：返回 (response, tool_trace)
3. **try_learn_skill_from_trace()**：从工具序列自动提取可复用技能
4. **Skill Nudge**：每12个 cycle 提醒审查是否有新技能可提取

### 对情感陪伴的意义

Agent 能从对话中自动学习：
- "用户 A 在焦虑时需要先共情再给建议"（技能：焦虑回应模式）
- "用户 B 喜欢用比喻来理解问题"（技能：比喻式沟通）
- "晚上10点后的对话通常更深入"（技能：深夜对话模式）

---

## 关键代码位置

### Nautilus Agent（可复用的核心引擎）

```
nautilus-agent/
├── nautilus_agent/
│   ├── agent.py                    # 主循环：think() 七对完整实现
│   ├── core/
│   │   ├── memory/store.py         # 3层记忆：core/episodic/archive + FTS5
│   │   ├── mind/
│   │   │   ├── bicameral.py        # 二分心智：Judge + Executor + 痛苦信号
│   │   │   ├── emotion.py          # 情绪引擎：17种情绪 + 行为映射
│   │   │   └── personality.py      # 人格加载 + system prompt 生成
│   │   ├── explore/skills.py       # 技能库：学习/衰减/搜索
│   │   ├── evolution/survival.py   # 进化账本：记录每次变化
│   │   └── consensus/raid.py       # RAID共识：1/2/3/5 级验证
│   ├── gateway/
│   │   ├── daemon.py               # Daemon 循环 + tool trace
│   │   └── telegram.py             # Telegram 长轮询
│   └── tools/                      # 40+ 工具
├── personalities/                   # YAML 人格定义
│   ├── default.yaml
│   ├── kairos.yaml
│   └── minimax.yaml
└── run_daemon.py                    # 启动入口
```

### 禅心项目（已有的人格系统）

```
quantum-buddha-project/
├── server/
│   ├── config/personalities/
│   │   ├── types.ts                # 完整类型定义（260行）
│   │   ├── buddha/                 # 佛陀人格（284条知识库）
│   │   ├── companion/              # 陪伴者人格（150条知识库）
│   │   └── butler/                 # 管家人格
│   ├── emotion-engine/             # 情感识别引擎
│   └── realtime-voice/             # 实时语音
```

---

## 给新 session 的快速启动指南

### 创建新的情感陪伴人格

1. **复制 `personalities/default.yaml`**，改名为新角色名
2. **重写 identity**：不是"我是AI"，是"我是[角色名]，我[核心特征]"
3. **设计七对规则**：每对写两条 emotionResponse（阳面+阴面）
4. **定制二分心智**：Judge 关注什么？Executor 感受什么？
5. **测试**：`python -c "from nautilus_agent.agent import NautilusAgent; a = NautilusAgent('new_name'); print(a.think('你好'))"`

### 复用禅心机制到新项目

可以直接 import 的：
- `nautilus_agent.core.mind.emotion` — 情绪识别 + 行为映射
- `nautilus_agent.core.mind.bicameral` — 二分心智 + 痛苦信号
- `nautilus_agent.core.memory` — 3层记忆 + FTS5 搜索
- `nautilus_agent.core.explore.skills` — 技能学习 + 衰减

需要新建的：
- 角色专属知识库（情感陪伴、心理学、日常对话）
- 语音配置（TTS 音色、语速、情绪映射）
- 平台接入（微信/Telegram/App）

---

## 本 session 的三个 Agent 实时数据

> 截至 2026-04-06 18:25

| Agent | Cycle | Level | 最新行为 |
|-------|-------|-------|---------|
| KAIROS | 8 | **Level 2**（代码阅读） | 从 Level 1(write+run) 进阶到 Level 2(grep+read_file) |
| MiniMax | ~15 | Level 1→2 | **生成了图片并发到 Telegram！** generate_image → send_telegram_photo |
| Local | ~10 | 待观察 | 运行中 |

关键突破：MiniMax 第一次使用多模态能力（图片生成 + Telegram 发送），KAIROS 第一次读自己的源码。
