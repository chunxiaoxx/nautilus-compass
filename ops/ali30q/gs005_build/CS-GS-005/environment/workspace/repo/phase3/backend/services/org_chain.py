"""M1 任务链引擎 — #169 平台侧配套(2026-09-14 用户批准,flywheel 认领验证段)。

零新表设计(方案红线:全部用既有件):
- 任务函走 org task 语义(OrgMailbox.task_meta,五件套),trace=`m1-<batch>-<step>[-r<k>]`
- 完成回函 = 执行框投回 to=platform,trace 加 `-done`,body 首行 `VERDICT: PASS|REJECT`
- 链状态 = 邮箱里已存在的函序列(邮箱即账本,可重建、可审计)
- advance() 纯决策:从头模拟状态机 → fire/wait/failed/finished;幂等可重入
- outbox = final 终报函(to=platform,哨兵 15min 内推给用户)
- 环节定义 = 飞轮试单流水线八环节的 M1 子集(环节 1-5,翻译表 2026-09-04 方案)

REJECT 语义:有 on_reject 的环节(如 QC 拒收回重采)回退到目标环节下一轮;
无 on_reject 的环节 REJECT = 链失败(failed,人工介入)。
自回退特例(on_reject=自身):验证型环节(convert_lerobot)REJECT = 等判据
裁决;判据修订入正本后自动 fire 下一轮重验,acceptance 随函携带新判据。
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.org_mailbox import OrgMailbox

CHAIN = "m1"
_DONE_VERDICTS = ("PASS", "REJECT")


@dataclass(frozen=True)
class Step:
    key: str
    title: str
    acceptance: str
    deliverable_format: str
    consumer: str
    sla_hours: int = 2
    on_reject: str | None = None  # REJECT 回退目标环节 key


M1_STEPS: list[Step] = [
    Step(key="equip_acceptance", title="设备到货验收",
         acceptance="/collect 清单逐项对账:到货件数/型号/序列号与下单单一致,缺损如实亮牌",
         deliverable_format="验收清单(逐项对账)", consumer="flywheel", sla_hours=48),
    Step(key="day0_smoke", title="Day0 实测",
         acceptance="照单跑出实采样例:采样例文件存在+Hz/通道元数据达标",
         deliverable_format="采样例文件+元数据读数", consumer="flywheel", sla_hours=48),
    Step(key="collect_episode", title="采集执行",
         acceptance="原始素材达标:时长/场景/动作清单命中询价单口径",
         deliverable_format="episode 原始数据包+自检清单", consumer="flywheel", sla_hours=72),
    Step(key="qc_pass", title="QC 四检",
         acceptance="黑帧/冻帧/模糊/人脸四检机械检测报告:全过=PASS;超阈=REJECT 回重采",
         deliverable_format="QC 检测报告", consumer="flywheel", sla_hours=24,
         on_reject="collect_episode"),
    Step(key="convert_lerobot", title="LeRobot 转换",
         acceptance="v0.3 读回验证:帧数 written==decoded==源视频帧数(状态日志±1 注记为上游特性);"
                    "双 mp4 齐;逐集 valid_ratio>=0.9 硬门槛,批 min/分布上墙,坏帧集清单披露",
         deliverable_format="LeRobot 数据集+读回验证读数(v0.3)", consumer="flywheel", sla_hours=24,
         on_reject="convert_lerobot"),  # 验证型环节:REJECT=判据裁决后自回退重验(下一轮)
]


@dataclass(frozen=True)
class Action:
    kind: str                       # fire | wait | finished | failed
    step_key: str | None = None
    trace: str | None = None
    step: Step | None = None
    round_n: int = 0
    meta: dict = field(default_factory=dict)


def _trace(batch: str, key: str, round_n: int) -> str:
    return f"{CHAIN}-{batch}-{key}" + (f"-r{round_n}" if round_n else "")


def _exists(db: Session, trace: str) -> OrgMailbox | None:
    return db.query(OrgMailbox).filter_by(trace_id=trace).first()


def _verdict_of(db: Session, batch: str, key: str, round_n: int) -> str | None:
    """该轮任务函的完成回函 verdict;无回函=None,无法解析=None。"""
    row = _exists(db, _trace(batch, key, round_n) + "-done")
    if row is None:
        return None
    first = (row.body or "").strip().splitlines()[0].strip() if row.body else ""
    for v in _DONE_VERDICTS:
        if first.upper().endswith(v):
            return v
    return None


def advance(db: Session, batch: str, steps: list[Step] = M1_STEPS) -> Action:
    """从头模拟链状态机 → 下一个动作。纯读,可重复执行(幂等决策)。"""
    key_index = {s.key: i for i, s in enumerate(steps)}
    rounds: dict[str, int] = defaultdict(int)
    pos = 0
    while pos < len(steps):
        step = steps[pos]
        r = rounds[step.key]
        task_row = _exists(db, _trace(batch, step.key, r))
        if task_row is None:
            return Action(kind="fire", step_key=step.key, step=step, round_n=r,
                          trace=_trace(batch, step.key, r))
        verdict = _verdict_of(db, batch, step.key, r)
        if verdict is None:
            return Action(kind="wait", step_key=step.key, round_n=r,
                          trace=_trace(batch, step.key, r))
        if verdict == "PASS":
            pos += 1
        elif step.on_reject and step.on_reject in key_index:
            rounds[step.on_reject] += 1
            pos = key_index[step.on_reject]
        else:
            return Action(kind="failed", step_key=step.key, round_n=r,
                          trace=_trace(batch, step.key, r),
                          meta={"reason": f"{step.key} REJECT 且无回退目标"})
    return Action(kind="fire", step_key="final",
                  trace=f"{CHAIN}-{batch}-final",
                  meta={"note": "全链 PASS,投终报(outbox)"})
