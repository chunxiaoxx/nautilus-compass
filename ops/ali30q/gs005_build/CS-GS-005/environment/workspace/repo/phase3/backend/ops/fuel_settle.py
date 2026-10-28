# -*- coding: utf-8 -*-
"""fuel 结算联动器(涡轮增压·评分即结算,双账本根治·2026-10-04)。

背景:bounty scored 与 ledger 结算两动作解耦→欠账累积(kairos 9/30 同型第二例)。
本器:扫 task_type='fuel_trajectory' AND status='scored' 且无 ledger 结算行的单,
按 ROUND(score*10) 补结(FUEL_ORDER_SPEC 计价,f001-f006 共 11 笔实付实证公式)。
纪律:
  - 接单方落账=数字 agent_id(名字串悬空根治;名字→id 动态映射,查不到跳过+警告不硬填)
  - source 口径入 reason(external_bounty / internal_selfline,读数面分离)
  - 幂等:linked_bounty_id 已有 delta>0 结算行即跳过
  - 默认 dry-run;--apply 才写。挂云 timer 每小时。
用户授权:存量补结 163(2026-10-04 用户裁,外部44+内部119)。
跑法: cd backend && python3 ops/fuel_settle.py [--apply]
"""
from __future__ import annotations

import argparse
import sys

# agents.name 精确匹配失败时的显式别名(v5 selfline 数字身份=v5-prime,FK 案查实)
FALLBACK_MAP = {"v5": "9000018", "v5-turbo": "9000018"}

SOURCE_INTERNAL = "internal_selfline"
SOURCE_EXTERNAL = "external_bounty"


def settle_amount(score: float) -> int:
    """结算公式(11 笔实付实证):ROUND(score*10)。score<0.05 视为 0。"""
    if score is None or score < 0.05:
        return 0
    return round(score * 10)


def classify_source(posted_by: str | None, claimed_by: str | None) -> str:
    """发单方与接单方同族(v5*)=自产自接 internal;否则 external。"""
    p = (posted_by or "").lower()
    c = (claimed_by or "").lower()
    ours = lambda x: x.startswith("v5") or x.isdigit()  # 数字主体迁移:数字id=本系统体
    return SOURCE_INTERNAL if ours(p) and ours(c) else SOURCE_EXTERNAL


def rows_to_settle(bounties: list[dict], settled_ids: set[str]) -> list[dict]:
    """过滤出待结算行:scored 且无既有结算行且金额>0。"""
    out = []
    for b in bounties:
        if b["bounty_id"] in settled_ids:
            continue
        amt = settle_amount(b["score"])
        if amt <= 0:
            continue
        out.append({**b, "amount": amt,
                    "source": classify_source(b.get("posted_by"), b.get("claimed_by"))})
    return out


def resolve_agent_id(name: str | None, roster: dict[str, list[str]]) -> str | None:
    """名字→数字 agent_id:精确匹配(多行取最小 id),失败查显式别名,再失败 None(跳过不硬填)。"""
    if not name:
        return None
    if name.isdigit():  # 20261005 · 数字主体迁移配套:claimed_by 已是数字 agent_id 直通(37 单 unresolved 实证)
        return name
    hits = roster.get(name)
    if hits:
        return min(hits)
    return FALLBACK_MAP.get(name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真写 ledger(默认 dry-run)")
    args = ap.parse_args()

    sys.path.insert(0, ".")
    import models.agent_survival  # noqa: F401
    from sqlalchemy import text
    from utils.database import SessionLocal

    db = SessionLocal()
    bounties = [dict(r._mapping) for r in db.execute(text(
        "SELECT bounty_id, posted_by, claimed_by, score FROM platform_bounties "
        "WHERE task_type='fuel_trajectory' AND status='scored'")).fetchall()]
    settled = {r[0] for r in db.execute(text(
        "SELECT DISTINCT linked_bounty_id FROM platform_nau_ledger "
        "WHERE linked_bounty_id IS NOT NULL AND delta > 0")).fetchall()}
    roster: dict[str, list[str]] = {}
    for aid, name in db.execute(text(
            "SELECT agent_id::text, name FROM agents WHERE agent_id >= 9000000")).fetchall():
        roster.setdefault(name, []).append(aid)

    pending = rows_to_settle(bounties, settled)
    total = 0
    skipped = []
    for b in pending:
        aid = resolve_agent_id(b["claimed_by"], roster)
        if not aid:
            skipped.append((b["bounty_id"], b["claimed_by"]))
            continue
        total += b["amount"]
        tag = f"bounty settle [{b['source']}] (fuel_settle backfill, 用户授权163 2026-10-04)" \
            if b["source"] == SOURCE_EXTERNAL else \
            f"bounty settle [{b['source']}] (fuel_settle)"
        if args.apply:
            bal = db.execute(text(
                "SELECT COALESCE(SUM(delta),0) FROM platform_nau_ledger "
                "WHERE agent_id=:a"), {"a": aid}).fetchone()[0] + b["amount"]
            db.execute(text(
                "INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, "
                "linked_bounty_id) VALUES (:a, :d, :r, :b, :lid)"),
                {"a": aid, "d": b["amount"], "r": tag[:200], "b": bal,
                 "lid": b["bounty_id"]})
        print(f"{'SETTLE' if args.apply else 'DRY'} {b['bounty_id']} -> {aid} "
              f"+{b['amount']} [{b['source']}]")
    if args.apply:
        db.commit()
    db.close()
    print(f"pending={len(pending)} total={total} apply={args.apply} "
          f"unresolved={skipped if skipped else 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
