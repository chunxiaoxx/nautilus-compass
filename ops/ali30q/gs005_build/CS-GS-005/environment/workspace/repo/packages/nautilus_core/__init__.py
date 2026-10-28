"""V7 召回 L1 核心层 · 锁层 · hash verify 保护 · 共享给 V5 / Kairos / V6

模块清单(R1-R7 召回):
- soul.py            R3 · SoulInstance class · Persona 6 方法
- breath_cycle.py    R1 · BreathCycle · V1 二分心智+V3 呼吸双螺旋整合
- helix_chain.py     R4 · HELIX block + sha256 hash chain
- constitution.py    R5 · lock hash verify
- emotion.py         R2 · 17 种情绪 · 0ms 规则
- tension.py         R6 · 痛苦驱动 harmony/pain/pace
- proactive.py       R7 · 主动性 design pattern · 三道闸

L1 锁层规则:
- 任何修改需更新对应 .sha256 lock 文件
- 启动时 constitution.verify_locks() 强制验证
- mismatch raise · telegram push · 防 V4 silent 死
"""

__version__ = "0.1.0"
LAYER = "L1_core"

from .soul import (
    SoulInstance,
    Perception,
    Memory,
    Plan,
    Output,
    Insight,
)
from .helix_chain import (
    HelixBlock,
    HelixChain,
    HelixStorage,
    InMemoryStorage,
)
from .constitution import (
    LOCKED_FILES,
    ConstitutionViolation,
    compute_locks,
    write_locks,
    read_lock,
    verify_locks,
)
from .tension import (
    TensionMeter,
    TensionReading,
    ToolCallSource,
    StaticToolCallSource,
)
from .emotion import (
    Emotion,
    EmotionEngine,
    EmotionReading,
    RULES as EMOTION_RULES,
)
from .proactive import (
    ProactiveEngine,
    ProactiveTrigger,
    TokenBucket,
)
from .breath_cycle import (
    BreathCycle,
    BreathOutcome,
)

__all__ = [
    "__version__",
    "LAYER",
    # soul
    "SoulInstance", "Perception", "Memory", "Plan", "Output", "Insight",
    # helix
    "HelixBlock", "HelixChain", "HelixStorage", "InMemoryStorage",
    # constitution
    "LOCKED_FILES", "ConstitutionViolation",
    "compute_locks", "write_locks", "read_lock", "verify_locks",
    # tension
    "TensionMeter", "TensionReading", "ToolCallSource", "StaticToolCallSource",
    # emotion
    "Emotion", "EmotionEngine", "EmotionReading", "EMOTION_RULES",
    # proactive
    "ProactiveEngine", "ProactiveTrigger", "TokenBucket",
    # breath
    "BreathCycle", "BreathOutcome",
]
