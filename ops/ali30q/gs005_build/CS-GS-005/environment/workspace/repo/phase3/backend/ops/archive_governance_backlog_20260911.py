#!/usr/bin/env python3
"""2026-09-11 治理表分层归档(L2 接管,用户拍板)· UPDATE-only 禁 DELETE。

207 号请示函超期+超 grace(v5 结构性失聪)→协议 §4 L2 接管执行。
四层(全部 status→archived + resolution_note,resolved_by 留痕,可逆):
  A 误灌指令串: created<2026-09-01 且 root_cause LIKE 'intent_router|evolve%'
  B 陈旧内部提案: created<2026-09-01 其余(voting 死信全在此层内)
  C 治理表 approved 未消费: status='approved'(实为 1 条;9/10 说的 117 条
    在 platform_proposals 表=soul/v7 队列,另案不动;goal_stack P1 源实为
    status='accepted',当前 0 行,归档后防未来翻转成误派单源)
  D 不动: 9 月 101 条真 bug 流(pending 继续走 v7 分流)
用法: python archive_governance_backlog_20260911.py [--apply](默认 dry-run 只打印对账)
"""
import os
import sys

import psycopg

DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production",
)

LAYERS = [
    ("A_misrouted", "goal 管道误灌治理表(9/10 体检定性+9/11 预检抽样复核)",
     "status IN ('pending','voting') AND created_at < '2026-09-01'"
     " AND root_cause LIKE 'intent_router|evolve%%'"),
    ("B_stale_content", "陈旧 V5 内部提案·3 月未执行预检发现非误灌·同批退场(可逆)",
     "status IN ('pending','voting') AND created_at < '2026-09-01'"
     " AND (root_cause NOT LIKE 'intent_router|evolve%%' OR root_cause IS NULL)"),
    ("C_approved_unconsumed", "approved 未消费超期·内容已被后续事件超越·goal_stack P1 误派单源清障",
     "status = 'approved'"),
]


def main() -> int:
    apply = "--apply" in sys.argv
    with psycopg.connect(DSN, connect_timeout=10) as c:
        with c.cursor() as cu:
            for name, note, where in LAYERS:
                cu.execute(f"SELECT COUNT(*) FROM platform_improvement_proposals WHERE {where}")
                n = cu.fetchone()[0]
                print(f"[{name}] match={n} note={note[:30]}…")
                if apply and n:
                    cu.execute(
                        "UPDATE platform_improvement_proposals SET status='archived',"
                        " resolution_note=%s, resolved_at=now(),"
                        " resolved_by='platform-loop L2 takeover 2026-09-11'"
                        f" WHERE {where} RETURNING id",
                        (note,),
                    )
                    print(f"[{name}] archived={len(cu.fetchall())}")
        c.commit() if apply else c.rollback()
    # 对账(apply 后必读): 各状态余量
    with psycopg.connect(DSN, connect_timeout=10) as c:
        with c.cursor() as cu:
            cu.execute("SELECT status, COUNT(*) FROM platform_improvement_proposals"
                       " GROUP BY status ORDER BY 2 DESC")
            print("=== AFTER ===" if apply else "=== CURRENT (unchanged, dry-run) ===")
            for s, n in cu.fetchall():
                print(f"{s}: {n}")
    print("MODE:", "APPLIED" if apply else "DRY-RUN(rollback)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())