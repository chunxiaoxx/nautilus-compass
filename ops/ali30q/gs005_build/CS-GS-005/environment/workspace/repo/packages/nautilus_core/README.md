# nautilus_core · V7 召回 L1 共享层

V1 二分心智 + V3 呼吸双螺旋整合体 · 锁层 sha256 hash verify · 共享给 V5 / Kairos / V6

## 7 模块

| 模块 | 内容 | 行数 |
|---|---|---|
| `soul.py` | SoulInstance 基类 · 6 方法(perceive/recall/think/compose/express/reflect)| 97 |
| `helix_chain.py` | HelixBlock + HelixChain · sha256 prev_hash 链 · verify_integrity | 162 |
| `constitution.py` | LOCKED_FILES 锁层 · CLI `--update / --check` 模式 | 117 |
| `tension.py` | TensionMeter · 真工具失败率 → harmony/pain/pace | 95 |
| `emotion.py` | EmotionEngine · 17 种(4 维度×3 强度+5+neutral)· 0ms 规则路径 | 108 |
| `proactive.py` | ProactiveEngine · priority + rate(token bucket)+ cooldown 三闸 | 105 |
| `breath_cycle.py` | BreathCycle · 整合 R2-R7 · breath() = 1 cycle = 1 HelixBlock | 142 |

## 用法 · L2 agent 接入

```python
from nautilus_core import (
    SoulInstance, Perception, Memory, Plan, Output, Insight,
    HelixBlock, HelixChain, InMemoryStorage,
    TensionMeter, StaticToolCallSource,
    EmotionEngine,
    ProactiveEngine, ProactiveTrigger,
    BreathCycle, BreathOutcome,
)

class MyAgentSoul(SoulInstance):
    def perceive(self, raw_input, context=None):
        return Perception(raw_input=raw_input, ...)
    def recall(self, query, top_k=5):
        return [...]   # 接 zenmind-mem / compass
    def think(self, perception, memories):
        return Plan(intent="...", tool_name="...", reasoning="...")
    # compose / express / reflect 同样 override

soul = MyAgentSoul(agent_id="ag-1")
helix = HelixChain(agent_id="ag-1", storage=InMemoryStorage())
cycle = BreathCycle(soul=soul, helix_chain=helix,
                    emotion=EmotionEngine(),
                    proactive=ProactiveEngine())

block = cycle.breath("用户输入")
print(block.prompt_hint())
```

## 锁层

任何 `LOCKED_FILES` 改动 · 启动时 `verify_locks(strict=True)` 拒启:
```bash
python -m nautilus_core.constitution --check    # 验证
python -m nautilus_core.constitution --update   # 改动后更新 sha256
```

## tests

48/48 PASS:
```bash
python -m pytest nautilus_core/tests/ -v
```

## V5/Kairos/V6 接入计划

- ✅ Step 1 · V7 worktree → `nautilus_core` package(本 commit)
- ⏳ Step 2 · V5 主 daemon 重构 · 替换 `mind/emotion/chain` 为 `from nautilus_core import ...`
- ⏳ Step 3 · Kairos / V6 接入 · 删自有 emotion / 散落 pain · `import nautilus_core`

## V4 教训

- LOCKED_FILES + sha256 → 任何 silent 改动启动失败(防 V4 silent regression)
- BreathOutcome 由外部 callback 注入 → 不让 SoulInstance 自评 success
- ProactiveEngine 三闸 → 主动性不退化为噪音
