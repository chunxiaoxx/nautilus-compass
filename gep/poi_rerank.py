"""GEP P3 · 客户端 PoI(Proof-of-Impact)重排。

把跨 agent 召回的记忆胶囊 hits 按「已证下游影响」重排,让高影响胶囊排前
—— 质量进化 / GEP 自然选择。

复用不重造:impact 分数(`cumulative_impact` 字段)来自 compass 已有的 PoI
体系 —— `proof/poi_calculator.py` 配合 serving 侧的 PoI 台账算好后,挂在
serving recall 返回的每个 hit 上。本模块**只做客户端按该字段重排**,不重新
发明 impact 打分公式。

端到端飞轮生效需 serving recall 返回 `cumulative_impact` 字段(serving 侧
增强,部署后才有);在那之前缺字段当 0.0 安全处理。本函数纯属客户端重排逻辑,
serving 不改。

健壮性:与 compass 飞轮「记忆服务抖动不停摆」一致 —— 永不抛。空列表返回 [],
缺字段 / 非数值字段 coerce 当 0,稳定排序(同分保持原序)。
"""

import math


def _as_float(value) -> float:
    """安全地把任意值 coerce 成 float;非数值 / NaN / 缺失一律当 0.0,永不抛。"""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    if math.isnan(f) or math.isinf(f):
        return 0.0
    return f


def rerank_by_impact(hits):
    """按 cumulative_impact 降序重排 hits,reward 作次级排序键(降序)。

    Args:
        hits: 召回的 hit dict 列表。每个 hit 期望(但不强制)带
            `cumulative_impact`(来自 PoI 台账)与 `reward` 字段。

    Returns:
        重排后的 hit 列表(同一批原 dict 对象,只重排顺序,不改内容)。
        高 cumulative_impact 优先;同 impact 时高 reward 优先;同分保持原序
        (稳定排序)。缺字段 / 非数值 / 空列表均安全,永不抛。
    """
    if not hits:
        return []
    # sorted 是稳定排序:同分(同 impact 同 reward)保持原序。
    # 降序用负号,避免对原 dict 做任何改动。
    return sorted(
        hits,
        key=lambda h: (
            -_as_float(h.get("cumulative_impact") if isinstance(h, dict) else None),
            -_as_float(h.get("reward") if isinstance(h, dict) else None),
        ),
    )
