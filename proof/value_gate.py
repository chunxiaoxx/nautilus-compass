"""B1 · 价值证明门 · 反"堆死机制"纪律的代码化.

近一月最硬教训(canonical §2.1): compass 一直堆记忆机制(OKF/GEP/胶囊/…)而没证
任一让某 agent 在真任务变强 —— 堆机制本身是病。本门 = 每个记忆功能上线前必须答得出
"它让谁(helps_whom)在什么任务(on_task)上、用什么可测信号(measured_by)证明变好"。
答不出 = defer。纯校验·无副作用·复用现有 PoI/win_rate/recall 度量语义(不重造)。
"""
from dataclasses import dataclass


# 已有的真实可测信号(功能价值必须落到其一)· 加新度量就在这登记。
RECOGNIZED_SIGNALS = (
    "poi", "cumulative_impact",      # proof/poi_calculator 体系
    "win_rate", "uplift",            # 飞轮 verdict
    "recall-hit", "recall hit",      # 召回命中
    "tier mutation", "tier_mutation",  # 生命周期晋升
    "valid_rate", "reinforce",
)


@dataclass
class ValueClaim:
    name: str
    helps_whom: str        # 谁受益(哪个 agent / consumer)
    on_task: str           # 在什么真任务上
    measured_by: str       # 用什么可测信号证明


def admit_feature(claim: ValueClaim) -> list:
    """返回错误列表(空=准入)。四字段非空 + measured_by 引用一个真实可测信号。"""
    errs = []
    if not (claim.name or "").strip():
        errs.append("name: 必填")
    if not (claim.helps_whom or "").strip():
        errs.append("helps_whom: 必须指明谁受益(不能空泛'用户')")
    if not (claim.on_task or "").strip():
        errs.append("on_task: 必须指明在什么真任务上")
    measured = (claim.measured_by or "").strip().lower()
    if not measured:
        errs.append("measured_by: 必填 — 没有可测信号=不准入(反堆死机制)")
    elif not any(sig in measured for sig in RECOGNIZED_SIGNALS):
        errs.append(
            f"measured_by: '{claim.measured_by}' 不是已知可测信号 — "
            f"必须落到 {list(RECOGNIZED_SIGNALS[:6])}… 之一(含糊词如'感觉更好'不算)"
        )
    return errs
