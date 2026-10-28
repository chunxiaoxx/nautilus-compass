# -*- coding: utf-8 -*-
"""M1 任务链 dispatcher — 单轮执行 advance 决策(#169 配套 v0)。

用法:python ops/org_chain_dispatch.py <batch_id> [...]
- fire 任务函 → 写 org task(五件套 task_meta;trace 唯一=幂等挡重)
- fire final  → 写终报函(to=platform,哨兵 15min 内推给用户;outbox)
- wait/failed → 打印不动(failed 需人工介入)

链状态=邮箱函序列(可重建),dispatcher 可安全重跑。timer 待 M1 首个真实
批次出现后再挂(手动/批处理驱动先行)。
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from models.org_mailbox import OrgMailbox  # noqa: E402
import models.agent_survival  # noqa: E402,F401 — mapper dependency
from services.org_chain import Action, advance  # noqa: E402
from utils.database import SessionLocal  # noqa: E402


def _exists(db, trace: str) -> bool:
    return db.query(OrgMailbox).filter_by(trace_id=trace).first() is not None


def _ack_consumed(db, batch: str, now) -> int:
    """fire 推进成功后,ack 该批次全部已消费的 -done 回函。

    链推进到下一环=此前回函已被引擎消费;不 ack 则永挂"待处理"清单,
    哨兵 E1 也据此误报(9/16 实证:M1 回函被推给用户'要处理')。
    幂等:只动 ack 为空且 trace 匹配 m1-<batch>-*-done 的行。"""
    rows = (db.query(OrgMailbox)
            .filter(OrgMailbox.trace_id.like(f"m1-{batch}-%-done"),
                    OrgMailbox.ack_at.is_(None)).all())
    for r in rows:
        r.ack_at = now
        r.ack_note = "consumed by chain dispatch"
    if rows:
        db.commit()
    return len(rows)


def execute(db, batch: str, act: Action) -> str:
    if act.kind != "fire" or act.trace is None or _exists(db, act.trace):
        return f"{act.kind}({act.step_key}) no-op"
    now = datetime.now()
    if act.step_key == "final":
        db.add(OrgMailbox(
            from_agent="platform", to_agent="platform", trace_id=act.trace,
            title=f"[M1 链终报] 批次 {batch} 全环节 PASS",
            body=f"M1 任务链批次 {batch} 全部环节 PASS,链关闭。"
                 f"终态可按 trace 前缀 {act.trace[:-6]} 在邮箱重建审计。",
            deadline=now + timedelta(hours=2), created_at=now,
        ))
        db.commit()
        return f"final fired(outbox; acked {_ack_consumed(db, batch, now)} replies)"
    assert act.step is not None
    head = (f"[任务单 {act.step.key}] 验收判据: {act.step.acceptance}\n"
            f"交付格式: {act.step.deliverable_format} · 消费者: {act.step.consumer}\n"
            f"回函约定: to=platform,trace={act.trace}-done,body 首行 'VERDICT: PASS' 或 'VERDICT: REJECT'")
    db.add(OrgMailbox(
        from_agent="platform", to_agent=act.step.consumer, trace_id=act.trace,
        title=f"[M1·{batch}] {act.step.title}" + (f"(重采 r{act.round_n})" if act.round_n else ""),
        body=head, deadline=now + timedelta(hours=act.step.sla_hours),
        created_at=now,
        task_meta={"task_type": act.step.key, "acceptance": act.step.acceptance,
                   "deliverable_format": act.step.deliverable_format,
                   "consumer": act.step.consumer, "chain": "m1", "batch": batch,
                   "round": str(act.round_n)},
    ))
    db.commit()
    return f"fired {act.trace} (acked {_ack_consumed(db, batch, now)} replies)"


def _active_batches(db) -> list[str]:
    """活跃批次=有 m1 链任务函但尚无 final 终报函的批次(timer 自动驱动用)。

    注意:本文件 _exists 返回 bool(链引擎 services.org_chain 的同名返回 row),
    判"无 final"必须用 not _exists —— 9/17 前版本误写 `is None` 恒假,
    timer 上线以来从未真正发现过任何活跃批次(活性假象:rc=0 全空转)。"""
    rows = db.query(OrgMailbox).filter(OrgMailbox.task_meta.isnot(None)).all()
    batches = {r.task_meta.get("batch") for r in rows
               if r.task_meta and r.task_meta.get("chain") == "m1" and r.task_meta.get("batch")}
    return sorted(b for b in batches if not _exists(db, f"m1-{b}-final"))


def main(argv: list[str]) -> int:
    db = SessionLocal()
    try:
        batches = _active_batches(db) if argv == ["--active"] else argv
        if argv == ["--active"] and not batches:
            print("no active batches")   # 正常态(无在途链),timer 退出码 0
            return 0
        if not argv or not batches:
            print("usage: org_chain_dispatch.py <batch_id> [...] | --active")
            return 2
        for batch in batches:
            act = advance(db, batch)
            print(batch, "->", execute(db, batch, act))
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
