# -*- coding: utf-8 -*-
"""裁定 C 冲正执行器:重复付款对冲(口径 C,用户 2026-10-07 深夜终裁)。

口径 C(#10437 compass 四口径表 + 用户裁 C):
  - 身份归并(canonical):9000016≡nautilus-prime-001、9000018≡v5(双身份分叉并主体,用户终裁);
  - 分组键 (linked_bounty_id, canonical_agent),delta>0,reason 非 stake%(押金释放正当同号,#10421);
  - 保留 (created_at, id) 首条,其余生成对冲负行:
      delta=-原delta, linked_bounty_id=原id+'.dedup', reason='dedup vs ledger#<源行id>';
  - 对冲行挂在第二笔实际所在身份名下并扣该身份 nau_balance(双写,#10368 反例预防);
  - 排除 hr-agent-web(已同步,再冲=双扣);slice6-cv-multi 类合法分成(组内金额不等且非别名)不冲——
    由 canonical 分组天然排除(9100601/9100602 非别名,各自组内无重复);
  - 幂等:组内已存在 '.dedup' 后缀行的整组跳过;
  - 默认 dry-run;--apply 才写。
门读数(dry-run 必须精确命中才许 apply,用户批):
  974 单 / 1,039 行 / −30,613 NAU(排 hr;含 hr 全量=1,056/1,121/−35,483)。
执行批次(10/8 晨部署窗):止血 fuel_settle 修复部署 → 本器 dry-run 验门 → apply →
  唯一索引 v3(20261008_ledger_settle_unique_gate.sql,stake 排除版)→ compass 复读。
跑法: cd backend && python3 ops/reconcile_dedup.py [--apply]
"""
from __future__ import annotations

import argparse
import sys

ALIAS = {"9000016": "nautilus-prime-001", "9000018": "v5"}  # 用户裁 C 身份归并
EXCLUDED_AGENTS = {"hr-agent-web"}  # 已同步,不冲(#10402)


def canonical(agent_id: str) -> str:
    return ALIAS.get(agent_id, agent_id)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="真写(默认 dry-run)")
    args = ap.parse_args()

    sys.path.insert(0, ".")
    from sqlalchemy import text  # noqa: E402
    from utils.database import SessionLocal  # noqa: E402

    db = SessionLocal()
    rows = [dict(r._mapping) for r in db.execute(text(
        "SELECT id, agent_id, linked_bounty_id, delta, created_at FROM platform_nau_ledger "
        "WHERE linked_bounty_id IS NOT NULL AND delta > 0 "
        "  AND reason NOT LIKE 'stake%' "
        "  AND linked_bounty_id NOT LIKE '%.dedup' "
        "  AND agent_id NOT IN :ex "
        "  AND linked_bounty_id IN ("
        "    SELECT linked_bounty_id FROM platform_nau_ledger "
        "    WHERE linked_bounty_id IS NOT NULL AND delta > 0 "
        "      AND reason NOT LIKE 'stake%' AND linked_bounty_id NOT LIKE '%.dedup' "
        "    GROUP BY linked_bounty_id HAVING count(*) > 1)"
    ), {"ex": tuple(EXCLUDED_AGENTS)}).fetchall()]

    done_keys = {(r[0], canonical(r[1])) for r in db.execute(text(
        "SELECT linked_bounty_id, agent_id FROM platform_nau_ledger "
        "WHERE linked_bounty_id LIKE '%.dedup'"))}

    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["linked_bounty_id"], canonical(r["agent_id"])), []).append(r)

    per_agent: dict[str, list[int]] = {}
    to_dedup = []
    for key, members in groups.items():
        if len(members) < 2 or (key[0] + ".dedup", key[1]) in done_keys:
            continue
        members.sort(key=lambda m: (m["created_at"], m["id"]))
        for m in members[1:]:
            to_dedup.append(m)
            per_agent.setdefault(m["agent_id"], []).append(m["delta"])

    total = -sum(sum(v) for v in per_agent.values())
    print(f"groups_dup={sum(1 for v in groups.values() if len(v) > 1)} dedup_rows={len(to_dedup)} "
          f"total_impact={total} apply={args.apply}  [门=C口径 974单/1039行/-30613]")
    for a, deltas in sorted(per_agent.items()):
        print(f"  {a}: rows={len(deltas)} impact=-{sum(deltas)}")

    # 拒负闸(#10474 第四节③,独立成立):apply 前若某 agent 冲后余额<0 → 拒批退出,不照扣。
    # 实现约束(#10474 第二节):归并身份只用于判重分组;扣余额必须按被冲行自己的 agent_id(本实现 m["agent_id"] 即是)。
    if args.apply and to_dedup:
        for a, deltas in per_agent.items():
            bal = db.execute(text(
                "SELECT nau_balance FROM platform_agents WHERE agent_id=:a"), {"a": a}).fetchone()
            bal = bal[0] if bal else 0
            if bal - sum(deltas) < 0:
                print(f"ABORT-NEGATIVE-GATE: {a} 冲后余额 {bal}-{sum(deltas)}<0 "
                      f"——拒批退出(#10474 拒负闸);先注资对平或裁口径后再来")
                db.rollback()
                db.close()
                return 2

    if args.apply and to_dedup:
        for m in to_dedup:
            db.execute(text(
                "INSERT INTO platform_nau_ledger (agent_id, delta, reason, balance_after, linked_bounty_id) "
                "VALUES (:a, :d, :r, "
                "  COALESCE((SELECT nau_balance FROM platform_agents WHERE agent_id=:a),0) - :amt, :lid)"
            ), {"a": m["agent_id"], "d": -m["delta"],
                "r": f"dedup vs ledger#{m['id']} (裁定C口径, 用户批 20261007)",
                "amt": m["delta"], "lid": m["linked_bounty_id"] + ".dedup"})
            # a+ 双腿标记(#10507):被冲重复正行同标 .dedup(仅元数据重命名,delta/id 不动,凭证保全可逆)
            db.execute(text(
                "UPDATE platform_nau_ledger SET linked_bounty_id = linked_bounty_id || '.dedup' "
                "WHERE id = :i"
            ), {"i": m["id"]})
            db.execute(text(
                "UPDATE platform_agents SET nau_balance = nau_balance - :amt "
                "WHERE agent_id = :a"
            ), {"amt": m["delta"], "a": m["agent_id"]})
        db.commit()
        print("APPLIED + 双写(nau_balance 同步扣减)完成")
    db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())