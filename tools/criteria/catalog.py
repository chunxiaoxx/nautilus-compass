"""criteria catalog v0——判据=VerifyPack(SPEC_v0.2)claim 模板+gate 元数据。

设计约束:verify 引擎零改动(9/15 冻结纪律)。gate(阈值门)语义在数据方 build 侧
执行(eval_gate):实测值过 gate 才写进 claim(verify 端纯等式复算);不过=拒装包。
目录正本:docs/criteria/CATALOG_v0.md。L/U 族占位待 22:00 收口会确认。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Criterion:
    """单条判据:模板+门+实测背书。frozen=注册后不可变(M3 纪律的代码面)。"""

    cid: str
    layer: str  # hard|video|structure|metric|semantic|utility|meta
    title: str
    check_kind: str  # SPEC_v0.2 §4 七种 kind 之一
    check_template: dict  # kind 参数模板(不含 kind 与 claim.value)
    gate: dict | None = None  # {"op": ">="|"<=", "value": float};None=纯复算无门
    provenance: str = ""


_REGISTRY: dict[str, Criterion] = {}

_ALLOWED_KINDS = {
    "aggregate", "file_hash", "file_hash_map",
    "group_count", "json_map_equal", "text_contains", "script",
}
_GATE_OPS = {
    ">=": lambda v, t: v >= t,
    "<=": lambda v, t: v <= t,
}


def register(c: Criterion) -> None:
    if c.cid in _REGISTRY:
        raise ValueError(f"duplicate criterion id: {c.cid}")
    if c.check_kind not in _ALLOWED_KINDS:
        raise ValueError(f"check kind {c.check_kind!r} not in SPEC_v0.2 §4")
    _REGISTRY[c.cid] = c


def get(cid: str) -> Criterion:
    return _REGISTRY[cid]


def all_criteria() -> list[Criterion]:
    return list(_REGISTRY.values())


def eval_gate(c: Criterion, value: float) -> bool:
    """数据方 build 侧过门判定。verify 引擎不调用此函数。"""
    if c.gate is None:
        return True
    op = _GATE_OPS.get(c.gate["op"])
    if op is None:
        raise ValueError(f"gate op {c.gate['op']!r} not allowed")
    return op(value, c.gate["value"])


def build_claim(c: Criterion, value: Any, *, claim_id: str | None = None) -> dict:
    """判据+实测值→SPEC_v0.2 claim dict。criterion 段随包携带,验签后可追溯。"""
    check = dict(c.check_template)
    check["kind"] = c.check_kind
    return {
        "id": claim_id or c.cid,
        "check": check,
        "value": value,
        "criterion": {"cid": c.cid, "layer": c.layer, "gate": c.gate},
    }


# ---------------------------------------------------------------- 注册表 v0


register(Criterion(
    cid="D2", layer="metric", title="帧完整率 >=99.9%",
    check_kind="aggregate",
    check_template={"from": "frames.json#rows", "num": "count(rc == 1)", "den": "count()", "op": "ratio_eq"},
    gate={"op": ">=", "value": 0.999},
    provenance="验收判据母版-v0 D2(内控暂定);200 条 valid_ratio 中位 1.0 最低 0.9127(P3 纲领 §一)",
))

register(Criterion(
    cid="D4", layer="metric", title="元数据完整率 =100%",
    check_kind="aggregate",
    check_template={"from": "meta_check.json#rows", "num": "count(ok == 1)", "den": "count()", "op": "ratio_eq"},
    gate={"op": ">=", "value": 1.0},
    provenance="验收判据母版-v0 D4:缺失即批次不合格",
))

register(Criterion(
    cid="C4", layer="structure", title="无效帧占比 <=5%",
    check_kind="aggregate",
    check_template={"from": "frames.json#rows", "num": "count(invalid == 1)", "den": "count()", "op": "ratio_eq"},
    gate={"op": "<=", "value": 0.05},
    provenance="验收判据母版-v0 C4(黑/冻/糊合计;首单实测可修订升 v0.1)",
))

register(Criterion(
    cid="X1", layer="semantic", title="指令-动作一致率(VLM 判官,L2 可降级)",
    check_kind="script",
    check_template={"repro": "repro/x1_judge.py", "timeout_s": 900},
    gate={"op": ">=", "value": 0.8},
    provenance="X1 40 条:17.5% 错配候选(待金标);判定器可信度 <0.8 不发布(P3 §四)",
))

register(Criterion(
    cid="M2", layer="meta", title="判定器金标校准通过率 >=0.8",
    check_kind="aggregate",
    check_template={"from": "calibration.json#rows", "num": "count(pass == 1)", "den": "count()", "op": "ratio_eq"},
    gate={"op": ">=", "value": 0.8},
    provenance="G1/X1 双证:判定器自己会出 bug(X1 parse 坑险报 100%);校准环是硬性的(P3 §四灵魂 2)",
))
