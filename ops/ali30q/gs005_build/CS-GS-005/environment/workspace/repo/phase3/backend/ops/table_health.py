# -*- coding: utf-8 -*-
"""表健康采集器 v1——表级活性单一真相源(9/4 接线件)。

消费端:gen_architecture.py 拼"表健康"节进架构扫描页;
        frame_snapshot.py 每日取 JSON 行追加本地 table_health.jsonl(趋势=git 历史)。

两个 9/4 教训内嵌:
  - pg_stat 计数器会 reset(8/31 reset 曾把 67% 误判"建完就废")
    → 窗起点必输出,窗长不足 3 天不作孤儿判;
  - 零写入≠死表 → 区分"被读"(读侧活,如 tasks 3 万次扫)与
    "有历史行数"(清前必归档,如 platform_judge_scores 1607 行)。

刻意不写 platform_metrics_snapshots:其 6 个消费方无类型过滤读
LIMIT 1/7/30,插入会污染业务健康分(9/4 调研确认)。云端纯读,零写入。

用法(必须云端跑,本地连错 DB):
  ssh cloud "cd /home/ubuntu/nautilus-mvp/phase3/backend && python3 ops/table_health.py"
输出:markdown 节 + 末行 "JSON: {...}"(frame_snapshot 解析追加)。
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # 云端直跑时 cwd 不进 sys.path

from sqlalchemy import text

MIN_WINDOW_DAYS = 3.0  # stats_reset 距今不足此值,零写入数字不作孤儿判
READ_FLOOR = 10  # 被读≥此次数才算"读侧活":本采集器 --exact 的 count 每表只加
# 1 次 seq_scan(观测污染持续到下次 stats reset,跨天不清零),真业务读是几十~几万次


def main() -> None:
    exact = "--exact" in sys.argv  # 对零写入表逐个 count(*):准但慢(~秒级);默认用 planner 估计
    from utils.database import SessionLocal
    s = SessionLocal()
    try:
        reset = s.execute(text(
            "SELECT stats_reset FROM pg_stat_database WHERE datname=current_database()"
        )).scalar()
        rows = s.execute(text(
            "SELECT relname, coalesce(n_live_tup,0) live_tup, coalesce(n_tup_ins,0) ins, "
            "coalesce(n_tup_upd,0) upd, coalesce(seq_scan,0)+coalesce(idx_scan,0) reads "
            "FROM pg_stat_user_tables ORDER BY relname"
        )).fetchall()
        if exact:
            counts = {}
            count_failed = []
            for r in rows:
                if not (r.ins or r.upd):  # 只数零写入表(均为小表)
                    try:
                        counts[r.relname] = s.execute(
                            text(f'SELECT count(*) FROM "{r.relname}"')).scalar()
                    except Exception:
                        # 单表失败(权限等)会把连接打入 failed transaction,
                        # 不 rollback 则后续所有 count 连锁失败(9/4 实测 90+ 张全毁)
                        s.rollback()
                        counts[r.relname] = None
                        count_failed.append(r.relname)
    finally:
        s.close()

    now = datetime.now(timezone.utc)
    total = len(rows)
    written = [r for r in rows if r.ins or r.upd]
    zero = [r for r in rows if not (r.ins or r.upd)]
    zero_read = [r for r in zero if r.reads >= READ_FLOOR]
    if exact:
        zero_data = sorted(((r, counts[r.relname]) for r in zero if counts.get(r.relname)),
                           key=lambda t: -t[1])
        top = ", ".join(f"{r.relname}({n})" for r, n in zero_data[:8])
        note = "清前必 dump 归档"
    else:
        est = sorted(((r, r.live_tup) for r in zero if r.live_tup), key=lambda t: -t[1])
        top = ", ".join(f"{r.relname}({n}估)" for r, n in est[:8])
        note = "行数为 planner 估计,清前必实查 count(*)"
    window = ((now - reset).total_seconds() / 86400.0) if reset else 0.0
    ok = reset is not None and window >= MIN_WINDOW_DAYS

    warn = "" if ok else f"(<{MIN_WINDOW_DAYS:.0f} 天,零写入数字不作孤儿判)"
    print(f"- 统计窗起点 {reset:%Y-%m-%d %H:%M %z} · 窗长 {window:.1f} 天{warn}")
    print(f"- 生产表 {total} 张:有写入 {len(written)} · 零写入 {len(zero)}"
          f"({100.0 * len(zero) / max(total, 1):.0f}%) · 其中被读≥{READ_FLOOR} 次 {len(zero_read)} 张(读侧活)")
    if top:
        print(f"- 零写入但有历史数据 top8({note}): {top}")
    if exact and count_failed:
        print(f"- 无法精确 count(权限等): {len(count_failed)} 张,以 planner 估计/跳过")

    rec = {
        "date": f"{now:%Y-%m-%d}",
        "stats_reset": f"{reset:%Y-%m-%d %H:%M}" if reset else None,
        "window_days": round(window, 1), "insufficient_window": not ok,
        "tables_total": total, "tables_written": len(written),
        "tables_zero_write": len(zero),
        "zero_write_pct": round(100.0 * len(zero) / max(total, 1), 1),
        "zero_write_with_reads": len(zero_read),
        "zero_write_with_data": len(zero_data) if exact else len(est),
        "rows_basis": "exact" if exact else "planner_est",
        "count_failed": len(count_failed) if exact else 0,
    }
    print("JSON: " + json.dumps(rec, ensure_ascii=False))


if __name__ == "__main__":
    main()
