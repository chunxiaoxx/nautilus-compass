"""R4 · HELIX 永久链 + hash chain · 不可篡改自我历史(V3 helix/chain.py 移植)

每个 cycle = 1 个 HelixBlock · sha256 hash chain · 不可篡改。

Block 真包(整合 R1-R7 真容器):
- prev_hash + content + ts → hash(完整链)
- ts_start / ts_end / duration_ms(R1 时戳)
- drift_score / drift_anchors(compass 漂移)
- tension(R6 harmony/pain/pace)
- emotion(R2 情绪 17 种)
- action / result / reflect(R1 双螺旋左右链)
- hydrogen_links(R1 氢键关联)

存储双写:
- PG (nautilus_helix_blocks) - 主
- JSONL (/var/lib/nautilus/helix.jsonl) - 防 PG 崩 · append-only
"""
from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Protocol


@dataclass
class HelixBlock:
    """HELIX 链单元 · 1 cycle = 1 block"""
    prev_hash: str                  # 前一 block 的 hash · genesis 时为 "0"*64
    cycle_num: int                  # 单调递增 · agent 生命内
    ts_start: int                   # cycle 起戳(epoch ms)
    ts_end: int                     # cycle 末戳(epoch ms)

    # R6 tension
    harmony: float = 0.5
    pain: float = 0.5
    pace: str = "normal"

    # R2 emotion
    emotion: str = "neutral"
    emotion_confidence: float = 0.0

    # compass 时空
    drift_score: float | None = None
    drift_anchors: list[str] = field(default_factory=list)
    recall_top_k: list[dict] = field(default_factory=list)

    # R1 双螺旋
    action: dict = field(default_factory=dict)         # 左链 · 行动
    result: dict = field(default_factory=dict)         # 左链 · 结果
    reflect: dict = field(default_factory=dict)        # 右链 · 见证
    hydrogen_links: list[str] = field(default_factory=list)  # 氢键 · 关联其他 block hash

    # meta
    persona_signature: str = ""
    agent_id: str = ""
    hash: str = ""                  # 计算后填(content + ts + prev_hash)

    @property
    def duration_ms(self) -> int:
        return self.ts_end - self.ts_start

    def content_for_hash(self) -> str:
        """除 hash 字段外全部字段 · stable JSON · 避免 dict 顺序差异"""
        d = asdict(self)
        d.pop("hash", None)
        return json.dumps(d, sort_keys=True, ensure_ascii=False)

    def compute_hash(self) -> str:
        return hashlib.sha256(self.content_for_hash().encode("utf-8")).hexdigest()

    def seal(self) -> "HelixBlock":
        """计算 hash 并返回 frozen 副本(实际 dataclass 非 frozen 为简化)"""
        self.hash = self.compute_hash()
        return self

    def to_jsonl(self) -> str:
        return json.dumps(asdict(self), sort_keys=True, ensure_ascii=False) + "\n"

    def prompt_hint(self) -> str:
        """≤ 60 token 紧凑形式 · 进 next cycle prompt 注入"""
        drift_str = f"{self.drift_score:.2f}" if self.drift_score is not None else "na"
        return (
            f"helix #{self.cycle_num} · {self.duration_ms}ms · drift {drift_str} · "
            f"pain {self.pain:.2f} · pace {self.pace} · feel {self.emotion}"
        )


class HelixStorage(Protocol):
    """抽象存储 · PG / JSONL / in-memory 都可"""
    def append(self, block: HelixBlock) -> None: ...
    def tail(self) -> HelixBlock | None: ...
    def get(self, cycle_num: int) -> HelixBlock | None: ...
    def all_blocks(self) -> list[HelixBlock]: ...


class InMemoryStorage:
    """测试用 · 内存存储"""
    def __init__(self):
        self._blocks: list[HelixBlock] = []

    def append(self, block: HelixBlock) -> None:
        self._blocks.append(block)

    def tail(self) -> HelixBlock | None:
        return self._blocks[-1] if self._blocks else None

    def get(self, cycle_num: int) -> HelixBlock | None:
        for b in self._blocks:
            if b.cycle_num == cycle_num:
                return b
        return None

    def all_blocks(self) -> list[HelixBlock]:
        return list(self._blocks)


class HelixChain:
    """L1 · 不可篡改自我历史 · sha256 链"""
    GENESIS_PREV = "0" * 64

    def __init__(self, agent_id: str, storage: HelixStorage):
        self.agent_id = agent_id
        self.storage = storage

    def next_cycle_num(self) -> int:
        tail = self.storage.tail()
        return (tail.cycle_num + 1) if tail else 0

    def open_block(self, **fields) -> HelixBlock:
        """开始新 cycle · ts_start = now · prev_hash 自动从 tail 取"""
        tail = self.storage.tail()
        prev_hash = tail.hash if tail else self.GENESIS_PREV
        return HelixBlock(
            prev_hash=prev_hash,
            cycle_num=self.next_cycle_num(),
            ts_start=int(time.time() * 1000),
            ts_end=0,
            agent_id=self.agent_id,
            **fields,
        )

    def close_block(self, block: HelixBlock) -> HelixBlock:
        """关闭 cycle · ts_end + seal hash + 写 storage"""
        if block.ts_end == 0:
            block.ts_end = int(time.time() * 1000)
        block.seal()
        self.storage.append(block)
        return block

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """从 genesis 走到 tail · 验 hash chain · 返 (ok, violations)"""
        violations = []
        prev = self.GENESIS_PREV
        for i, b in enumerate(self.storage.all_blocks()):
            if b.prev_hash != prev:
                violations.append(f"block {b.cycle_num}: prev_hash {b.prev_hash[:12]}... != expected {prev[:12]}...")
            actual_hash = b.compute_hash()
            if actual_hash != b.hash:
                violations.append(f"block {b.cycle_num}: hash {b.hash[:12]}... != recomputed {actual_hash[:12]}...")
            prev = b.hash
        return (len(violations) == 0, violations)
