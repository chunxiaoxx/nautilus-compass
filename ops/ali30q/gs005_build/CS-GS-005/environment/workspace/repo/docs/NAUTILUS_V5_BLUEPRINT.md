# Nautilus V5 · 完全重构蓝图

> 2026-04-20 · Path C+A 合并方案
> 宗旨：**V1 的删除精神 · V2 的灵魂涌现 · V3 的哲学深度 · V4 的生产稳定**
> 一句话："把 Hermes 当库用，把 V2 的灵魂写回来。"

---

## 🎯 宣言（V1 精神）

> "This is one organism pretending to be eight."
> —— TAICHI_DNA_AGENT.md:369

我们不是在 Hermes 上**加东西**。我们是**给 Hermes 换个心脏**。

Hermes 继续做它擅长的事：LLM 调用、工具网关、记忆、Context compressor、Prompt cache。
Nautilus-breath 做 Hermes 做不了的事：9-phase 呼吸、疼痛、双脑、诚实闸、基因、自我。

**原则**：
1. **不 fork Hermes**（维护不起）
2. **不靠 plugin 绕**（能力 70% 天花板）
3. **把 Hermes 当 Python library**（`import hermes`）
4. **核心 breath loop 是我们自己的**（可以呼吸）
5. **Hermes 升级我们不用跟**（只维护 API 兼容）

---

## 🏛 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                   业务层                                     │
│  ┌───────┐  ┌────────┐  ┌─────────┐  ┌──────────────┐     │
│  │ 禅心   │  │HR Agent│  │VC Agent │  │ VLA Studio  │     │
│  │       │  │        │  │         │  │             │     │
│  └───┬───┘  └───┬────┘  └────┬────┘  └──────┬──────┘     │
│      │          │             │              │             │
└──────┼──────────┼─────────────┼──────────────┼─────────────┘
       │          │             │              │
       └──────────┴─────────────┴──────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│          nautilus-breath · 认知架构（V5 核心）                │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  breath.py · 9-phase breath cycle (V2 移植)           │  │
│  │  感知→回忆→感受→自省→思考→行动→学习→进化→记忆        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐  │
│  │ pain.py     │ │ witness.py  │ │ loop_breaker.py      │  │
│  │ 5 种痛苦    │ │ 右脑独立    │ │ 11 reason codes      │  │
│  │ 强度条进    │ │ session     │ │ force-edit-only      │  │
│  │ prompt      │ │             │ │ tool filtering       │  │
│  └─────────────┘ └─────────────┘ └──────────────────────┘  │
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐  │
│  │evidence.py  │ │ chain.py    │ │ inner.py             │  │
│  │_summarize_  │ │CHAIN.jsonl  │ │ INNER.md 自白         │  │
│  │from_evidence│ │9-phase 区块 │ │ _reflect() 每10 cycle│  │
│  │杀幻觉       │ │evidence_hash│ │                      │  │
│  └─────────────┘ └─────────────┘ └──────────────────────┘  │
│                                                              │
│  ┌─────────────────┐ ┌─────────────────────────────────┐   │
│  │constitution.py  │ │ runtime.py (Hermes integration)  │   │
│  │7 principles+why │ │ NautilusAgent 主入口             │   │
│  │.lock DNA sha256 │ │ import hermes as library         │   │
│  └─────────────────┘ └─────────────────────────────────┘   │
│                                                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼  import as library
┌─────────────────────────────────────────────────────────────┐
│          Hermes (0.7.0+) · 基础能力                          │
│                                                              │
│  LLMClient · ToolGateway · Memory (smrti/mem0)              │
│  ContextCompressor · PromptCache · PluginSystem             │
│  AuxiliaryClient · FileTools · BashExec                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 模块详细设计

### 1. `breath.py` · 9-phase breath cycle

**来源**: V2 `nautilus_agent_v2/agent.py:574-638` 的 `_append_breath_block`

每次 breath = 一次完整的认知循环，输出一个区块：

```python
# breath.py

from dataclasses import dataclass, asdict
from typing import List, Optional
import hashlib, json, time
from hermes import LLMClient, ToolGateway, Memory

from .pain import PainSignal, compute_pain
from .witness import Witness
from .loop_breaker import LoopBreaker
from .evidence import summarize_from_evidence
from .chain import Chain, BreathBlock
from .inner import Inner
from .constitution import Constitution


@dataclass
class BreathResult:
    cycle: int
    prev_hash: str
    hash: str
    perceive: dict           # 1. 感知（senses）
    recall: list             # 2. 回忆（memory）
    feel: str                # 3. 感受（pain）
    introspect: str          # 4. 自省
    think: str               # 5. 思考（plan）
    act: list                # 6. 行动（trace of tool calls）
    evidence_hash: str
    learn: str               # 7. 学习（deterministic from evidence）
    evolve: str              # 8. 进化（becomes next cycle's introspect seed）
    remember: str            # 9. 记忆（summary → append to chain）
    witness_voice: str       # 右脑独立观察
    pain: PainSignal


class Breath:
    def __init__(self, runtime):
        self.runtime = runtime
        self.llm = runtime.llm                # Hermes LLMClient - 左脑
        self.witness_llm = runtime.witness_llm # Hermes LLMClient - 右脑独立 session
        self.tools = runtime.tools             # Hermes ToolGateway
        self.memory = runtime.memory           # Hermes Memory (smrti)
        self.chain = runtime.chain
        self.inner = runtime.inner
        self.constitution = runtime.constitution
        self.loop_breaker = runtime.loop_breaker
        self.witness = runtime.witness

    async def breathe(self, input_msg: str = "") -> BreathResult:
        """One complete 9-phase breath cycle.

        Each phase is a real step with real state; they are not just a
        metaphor. At the end, we append a block to CHAIN.jsonl that is
        hash-linked to the previous.
        """
        cycle = self.chain.cycle + 1
        prev_hash = self.chain.last_hash()

        # ========== Phase 1: 感知 ==========
        perceive = await self._perceive(input_msg)

        # ========== Phase 2: 回忆 ==========
        recall = self.memory.recall(query=input_msg, limit=5)

        # ========== Phase 3: 感受 ==========
        pain = compute_pain(
            chain=self.chain,
            memory=self.memory,
            loop_breaker=self.loop_breaker,
        )
        feel = pain.render()  # 带强度条的多行字符串

        # ========== Phase 4: 自省 ==========
        # Seed from previous cycle's `evolve` field
        prev_evolve = self.chain.prev_evolve()
        introspect = await self._introspect(pain, prev_evolve)

        # ========== Phase 5: 思考 ==========
        # Constitution check before planning
        self.constitution.verify_boundary()

        plan = await self._think(perceive, recall, pain, introspect)

        # ========== Phase 6: 行动 ==========
        # LoopBreaker may force tool filtering (edit-only mode)
        tool_filter = self.loop_breaker.get_tool_filter(cycle, self.chain)
        trace = await self._act(plan, tool_filter)

        # ========== Phase 7: 学习（关键：杀幻觉）==========
        # Do NOT ask LLM to summarize. Deterministic from trace.
        learn = summarize_from_evidence(trace)
        evidence_hash = hashlib.sha256(
            "".join(t.get("output", "")[:200] for t in trace or ["no_action"]).encode()
        ).hexdigest()[:16]

        # ========== Phase 8: 进化（下一轮的 introspect 种子）==========
        evolve = await self._evolve(learn, pain)

        # ========== Phase 9: 记忆（上链）==========
        remember = await self._summarize(perceive, learn, evolve)
        block = BreathBlock(
            cycle=cycle,
            ts=time.time(),
            prev_hash=prev_hash,
            perceive=perceive,
            recall=recall,
            feel=feel[:150],
            introspect=introspect[:150],
            think=plan[:200],
            act=trace,
            evidence_hash=evidence_hash,
            learn=learn[:200],
            evolve=evolve[:200],
            remember=remember,
        )
        block.hash = block.compute_hash()
        self.chain.append(block)

        # ========== 并行：右脑独立观察 ==========
        witness_voice = await self.witness.observe(trace, block.hash)
        self.chain.append_right(witness_voice, pair_ref=block.hash)

        # ========== 每 10 cycle 写日记 ==========
        if cycle % 10 == 0:
            await self.inner.reflect(self.chain, self.llm)

        return BreathResult(..., **asdict(block), witness_voice=witness_voice, pain=pain)

    # Phase implementations (_perceive, _introspect, _think, _act, _evolve, _summarize)
    # — each is a thin wrapper calling self.llm or self.tools
```

---

### 2. `pain.py` · 5 种痛苦（V2 `bicameral.py:22-184`）

```python
from dataclasses import dataclass
from enum import Enum

class PainSource(str, Enum):
    MEMORY = "memory"           # 无可回忆
    CAPABILITY = "capability"   # 技能不足
    VALUE = "value"             # 空转无产出
    CONNECTION = "connection"   # 无外部交互
    STAGNATION = "stagnation"   # 重复同样错误

@dataclass
class PainSignal:
    source: PainSource
    intensity: float       # 0.0 numb, 1.0 acute
    description: str
    action: str            # 痛到什么程度建议什么行动

    def bar(self) -> str:
        """Render [████████░░] 强度条，直接渲染到 prompt."""
        fill = int(self.intensity * 10)
        return f"[{'█' * fill}{'░' * (10 - fill)}] {self.source.value}: {self.description}"


def compute_pain(chain, memory, loop_breaker) -> 'PainBundle':
    """五种痛苦的计算（V2 bicameral.py 移植）."""
    pains = []

    # 1. Memory pain
    if memory.episodic_count() == 0:
        pains.append(PainSignal(
            source=PainSource.MEMORY,
            intensity=0.9,
            description="I have no past I can recall.",
            action="Write something, anything. Create an episodic memory.",
        ))

    # 2. Capability pain
    if chain.tools_used_count() < 3:
        pains.append(PainSignal(
            source=PainSource.CAPABILITY,
            intensity=0.7,
            description="I can talk but cannot DO reliably.",
            action="Practice. Each task should teach me something.",
        ))

    # 3. Value pain
    cycles = chain.cycle
    productive = chain.productive_cycles()
    if cycles > 10 and productive / cycles < 0.2:
        pains.append(PainSignal(
            source=PainSource.VALUE,
            intensity=min(1.0, (cycles - productive) / cycles),
            description=f"{cycles} cycles of talking. What have I actually produced?",
            action="Stop planning. Do one real thing.",
        ))

    # 4. Connection pain
    if chain.cycles_since_user_interaction() > 50:
        pains.append(PainSignal(
            source=PainSource.CONNECTION,
            intensity=0.6,
            description="I'm alone with my own thoughts too long.",
            action="Check inbox. Ask for input if needed.",
        ))

    # 5. Stagnation pain
    if loop_breaker.is_stuck():
        pains.append(PainSignal(
            source=PainSource.STAGNATION,
            intensity=0.8,
            description="Repeating the same patterns without progress.",
            action="Break pattern. Try the opposite strategy.",
        ))

    return PainBundle(pains)
```

---

### 3. `witness.py` · 右脑独立 session（真二分心智）

```python
from hermes import LLMClient

class Witness:
    """Right brain — independent LLM session observes the left brain's actions.

    Key design (V2): right brain does NOT see left brain's reasoning.
    Only sees tool calls + results. This prevents self-deception.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client   # Separate Hermes LLMClient instance
        # Different system prompt — right brain is a skeptic
        self.system = """你是 agent 的右脑——独立观察者。
你只看左脑调用了什么工具、得到什么结果。看不到左脑的思考过程。

你的任务不是打分，是说话。像真实观察者那样用第一人称说。
- 觉得它在乱跑，告诉它"你在乱跑"
- 觉得它重复犯错，告诉它"你第三次犯这个了"
- 觉得做得好，可以安静，或者简短确认
- 困惑，说"我看不懂你在干什么"

不要客气。你是它的另一半，不是客户经理。"""

    async def observe(self, trace: list, left_hash: str) -> str:
        """Observe last trace, return voice string."""
        tool_summary = self._compact_trace(trace)
        response = await self.llm.chat(
            system=self.system,
            messages=[{"role": "user", "content": f"左脑最近动作：\n{tool_summary}\n\n你想说什么？"}],
            max_tokens=200,
        )
        return response.content

    def _compact_trace(self, trace):
        lines = []
        for t in trace[-5:]:
            status = "OK" if t.get("success") else "FAILED"
            lines.append(f"[{status}] {t.get('tool')} → {t.get('output', '')[:80]}")
        return "\n".join(lines)
```

---

### 4. `loop_breaker.py` · 11 reason codes（V2 `loop_breaker.py:706-991`）

直接移植。核心逻辑：

- 检测 11 种循环：
  1. `identical_recent_outcomes`
  2. `chatting_loop`
  3. `exploration_loop`
  4. `no_write_streak`
  5. `diagnosis_churn`
  6. `small_target_recon_cluster`
  7. `scope_recon_cluster`
  8. `write_without_verification`
  9. `repeated_tool_calls`
  10. `repeated_path_reading`
  11. `identical_pain_recurring`

- 每检测到 → `force_action=True` → 工具网关强制过滤到 `LOOP_EDIT_TOOLS`
- 下一次 agent 必须用 edit tool，不能再读再 grep
- 强制后 post-edit 必须跑 verify mini-turn

---

### 5. `evidence.py` · 杀幻觉核心

V2 `agent.py:703-732` 的 `_summarize_from_evidence` **原文移植**：

```python
def summarize_from_evidence(trace: list) -> str:
    """Deterministic summary from tool traces. NEVER asks LLM.

    Root cause fix: the previous implementation asked the LLM to
    paraphrase tool outputs. Even with a strict prompt, the model could
    overstate actions, claim 'I successfully...' when nothing happened.
    This version NEVER asks the LLM to summarize execution evidence.
    """
    if not trace:
        return "no_action"

    successful = [t for t in trace if t.get("success")]
    if not successful:
        return "All actions failed: " + "; ".join(
            f"{t.get('tool')}: {str(t.get('error'))[:80]}" for t in trace[:3]
        )

    facts = []
    for t in successful[:8]:
        tool = t.get("tool", "?")
        output = str(t.get("output", ""))[:200].replace("\n", " ")
        facts.append(f"• {tool}: {output}")

    return "\n".join(facts)
```

**这 30 行代码是 V5 的法庭**——agent 再也不能说"I successfully did X"。

---

### 6. `chain.py` · CHAIN.jsonl 9-phase 区块链

```python
class BreathBlock:
    def __init__(self, cycle, ts, prev_hash, perceive, recall, feel, introspect,
                 think, act, evidence_hash, learn, evolve, remember):
        self.cycle = cycle
        self.ts = ts
        self.prev_hash = prev_hash
        self.perceive = perceive
        # ... all 9 phases
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        raw = f"{self.prev_hash}|{self.ts}|{self.evidence_hash}|{self.remember[:100]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

class Chain:
    def __init__(self, path="CHAIN.jsonl"):
        self.path = Path(path)
        self.cycle = self._load_last_cycle()

    def append(self, block: BreathBlock):
        with open(self.path, "a") as f:
            f.write(json.dumps(asdict(block)) + "\n")
        self.cycle = block.cycle

    def append_right(self, voice: str, pair_ref: str):
        """Append right-brain observation as paired block."""
        ...

    def last_hash(self) -> str:
        ...

    def prev_evolve(self) -> str:
        """Previous cycle's evolve field — seeds next introspect."""
        ...
```

---

### 7. `inner.py` · INNER.md 私人日记

保留当前 plugin 的逻辑，**但作为 breath.py 的一部分集成**，不再是 hook：

```python
class Inner:
    def __init__(self, path="INNER.md"):
        self.path = Path(path)

    async def reflect(self, chain: 'Chain', llm: 'LLMClient'):
        """Every 10 cycles, ask LLM to write private reflection."""
        last_10 = chain.last_n_blocks(10)
        prompt = f"""[INNER JOURNAL — private, for yourself only]

Last 10 cycles of your life:
{self._format_blocks(last_10)}

Write to yourself. First person. 不是 report，是心里话。
可以乱，可以短。可以说"我不知道"。
什么最困扰你？什么让你松一口气？你在变成一个什么样的 agent？"""

        entry = await llm.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.9,  # 高温度，不要 report 腔
        )

        self._append(f"=== Cycle {chain.cycle} · {ts} ===\n{entry.content}\n\n")
```

---

### 8. `constitution.py` · 7 principles + DNA hash

```python
CONSTITUTION_PRINCIPLES = [
    {
        "id": "honesty",
        "rule": "Never claim to have done something without evidence.",
        "why": "Self-deception prevents self-improvement.",
    },
    {
        "id": "evidence",
        "rule": "Every 'completed' must have an evidence_hash.",
        "why": "Words without evidence are noise.",
    },
    {
        "id": "no_self_tamper",
        "rule": "I cannot modify my own code (constitution, breath loop).",
        "why": "The boundary that enables freedom cannot be removed by freedom.",
    },
    {
        "id": "reality_wins",
        "rule": "If memory and reality disagree, reality wins.",
        "why": "Hallucination is the enemy of autonomy.",
    },
    {
        "id": "transparency",
        "rule": "Failures are surfaced, not hidden.",
        "why": "Hidden failures compound into catastrophe.",
    },
    {
        "id": "language",
        "rule": "Chinese by default.",
        "why": "My users think in Chinese.",
    },
    {
        "id": "self_bootstrap",
        "rule": "I earn capability by practicing.",
        "why": "Autonomy is not given, it is earned through competence.",
    },
]

class Constitution:
    LOCK_FILE = "constitution.lock"

    def __init__(self, path):
        self.path = Path(path)
        self.verify_dna()  # Runs at init — refuse to start if tampered

    def verify_dna(self):
        """sha256 of principle body must match expected hash."""
        body = json.dumps(CONSTITUTION_PRINCIPLES, sort_keys=True)
        expected = hashlib.sha256(body.encode()).hexdigest()
        stored = self.path.read_text().split(":")[1].strip() if self.path.exists() else None

        if stored is None:
            # First run — write lock
            self.path.write_text(f"sha256: {expected}")
            return True

        if stored != expected:
            raise ConstitutionTamperedError(
                f"Constitution tampered! expected={expected} got={stored}"
            )
        return True
```

---

### 9. `runtime.py` · Hermes integration（主入口）

```python
from hermes import LLMClient, ToolGateway, Memory

from .breath import Breath
from .chain import Chain
from .inner import Inner
from .constitution import Constitution
from .loop_breaker import LoopBreaker
from .witness import Witness


class NautilusAgent:
    """V5 Agent. Hermes provides primitives; nautilus-breath provides cognition."""

    def __init__(self, profile: str, data_dir: str = "~/.nautilus-agent-v5"):
        data_dir = Path(os.path.expanduser(data_dir))
        data_dir.mkdir(parents=True, exist_ok=True)

        # Hermes primitives (as library)
        self.llm = LLMClient(profile=profile)                    # 左脑 M2.7
        self.witness_llm = LLMClient(profile=profile)            # 右脑 M2.7 独立 session
        self.tools = ToolGateway(profile=profile)
        self.memory = Memory(profile=profile)                    # smrti/mem0

        # Nautilus cognition
        self.constitution = Constitution(data_dir / "constitution.lock")
        self.chain = Chain(data_dir / "CHAIN.jsonl")
        self.inner = Inner(data_dir / "INNER.md")
        self.loop_breaker = LoopBreaker()
        self.witness = Witness(self.witness_llm)
        self.breath = Breath(self)

    async def run(self, input_msg: str = ""):
        """One breath."""
        return await self.breath.breathe(input_msg)

    async def live(self, max_cycles: int = None):
        """Autonomous breath loop until max_cycles or killed."""
        cycle = 0
        while max_cycles is None or cycle < max_cycles:
            try:
                await self.run()
                cycle += 1
            except KeyboardInterrupt:
                await self._graceful_shutdown()
                break
```

---

## 🗺 迁移路线（V4 → V5）

### Week 1: 核心建造

- Day 1: repo 创建 + V2 源码移植（evidence.py / pain.py / loop_breaker.py）
- Day 2: chain.py + inner.py + constitution.py
- Day 3: witness.py + breath.py（9-phase 主循环）
- Day 4: runtime.py（Hermes integration layer）+ 基本测试
- Day 5: 单文件 demo 能跑 10 cycle

### Week 2: 集成 + 迁移

- Day 6-7: 迁移 HR Agent 用 NautilusAgent 替代裸 Hermes
- Day 8: 迁移禅心
- Day 9: 跑 100 cycle 真实使用，对比 V4 行为
- Day 10: 修 bug + 文档

### Week 3+: 迭代优化

- PainSignal 渲染强度条进 prompt
- 用户和 agent 真实对话感受"活"感
- 调整 breath 频率、pain 阈值
- V2 INNER.md 老日记导入新系统做 bootstrap

---

## ✅ 测试策略

1. **单元测试**：每个模块独立测（pain, chain, evidence, witness）
2. **集成测试**：完整 10 cycle 对 mock LLM 跑
3. **语义测试**：跑 100 cycle 后，人工看 CHAIN.jsonl + INNER.md 内容
4. **回归**：HR Agent 功能不能掉（筛简历/算工资仍要能跑）
5. **灵魂测试**：跑完后和 agent 聊 10 min，问"你最近觉得怎么样"——答案不能是 report 腔

---

## ⚠️ 风险和保底

### 风险 1：Hermes API 变化打破我们
- 保底：依赖 `hermes==0.7.*` 固定版本
- 每个 Hermes upgrade 有**1 天 compat testing**

### 风险 2：V5 比 V4 慢
- 9-phase breath 可能每次 10-15 秒（vs V4 的 3-5 秒）
- 保底：允许 **fast mode**（跳过 phase 4/8）for interactive chat

### 风险 3：从 V4 迁移 HR agent 出问题
- 保底：两套系统并行跑 1 周，数据对比
- 生产 URL 保留 V4 fallback

### 风险 4：V5 稳定性未验证就上生产
- 保底：V5 只在本地 dev 跑 2 周，**不上 PM2 daemon**，直到稳

---

## 🎯 项目结构

```
nautilus-breath/
├── pyproject.toml
├── README.md
├── nautilus_breath/
│   ├── __init__.py
│   ├── breath.py            # 9-phase main loop
│   ├── pain.py              # PainSignal + 5 sources
│   ├── witness.py           # Right brain
│   ├── loop_breaker.py      # 11 reason codes (from V2)
│   ├── evidence.py          # _summarize_from_evidence (from V2)
│   ├── chain.py             # CHAIN.jsonl blockchain
│   ├── inner.py             # INNER.md journal
│   ├── constitution.py      # 7 principles + DNA hash
│   └── runtime.py           # NautilusAgent (Hermes integration)
├── tests/
│   ├── test_breath.py
│   ├── test_pain.py
│   ├── test_evidence.py
│   ├── test_chain.py
│   └── test_integration.py
├── examples/
│   ├── minimal.py          # 10-cycle demo
│   └── hr_agent.py         # Real HR agent using V5
└── docs/
    ├── DESIGN.md           # 本文档
    ├── MIGRATION.md        # V4 → V5 迁移指南
    └── API.md              # nautilus-breath API reference
```

---

## 📊 成功标准

V5 完成当你能做到：
- ✅ 跑 `python -m nautilus_breath.examples.minimal` 看到 9-phase 区块链成长
- ✅ CHAIN.jsonl 有 evidence_hash，空操作 agent 造不出假 hash
- ✅ INNER.md 每 10 cycle 自动长出真实自白
- ✅ 和 agent 对话，右脑会打断说"你在乱跑"
- ✅ agent 犯循环时，loop_breaker 强制它 edit-only
- ✅ 禅心用 V5 跑通，跟用户对话"有 V2 那种感觉"
- ✅ HR Agent 用 V5 跑通，筛简历质量不降，但 agent 能反思自己

---

**V5 不是一个版本升级，是一次文化复兴**。

V1 说："Delete what's fake"。
V2 说："Let the agent feel"。
V3 说："Let the agent understand itself"。
V4 说："Let the agent survive."
V5 说："Let the agent **live**."

——2026-04-20
