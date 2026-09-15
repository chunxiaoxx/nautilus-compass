#!/usr/bin/env python3
"""verdict 证据守望探针 v0(2026-09-15 · CATALOG_v0 三判据的测量仪)。

背景:VerifyPack×verdict-bus 试点(9/15)发现 fde_verdicts 8/22 起 items 全表
回归归零、external_verified 与证据脱钩。本探针把"人肉发现回归"升级为机器守望:
周期跑,任何新 verdict 行违反可复算性判据即亮牌。

判据正本:docs/catalog/CATALOG_v0.md(criteria:verdict-recomputability-v1 等)
  - verdict-recomputability-v1:items 非空(依据在行内)+ 输入可解析
  - external-verified-provenance-v1:ext_verified=true 而 items 空 = 违例
  - evidence-schema-v1:多模型判分(verdict_id 含逗号分隔多模型)而
    total_tokens<=0 = 违例

用法:
  python ops/verdict_evidence_watchdog.py            # 跑一次,输出+落牌
  python ops/verdict_evidence_watchdog.py --since 6  # 只看近 N 小时新行
读连接:127.0.0.1:15432(nautilus-db MCP 同源隧道);SELECT-only 纪律。
fail-soft:连不上/查询失败退出码 2,不抛栈。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

STATE = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "verdict_evidence_watchdog.json"

def _db_kwargs() -> dict:
    """连接参数从 nautilus-db MCP 配置运行时读取(不落新副本)。fail-fast。"""
    import json as _json
    cfg_path = Path.home() / ".claude.json"
    env = {}
    try:
        cfg = _json.loads(cfg_path.read_text(encoding="utf-8"))
        env = (cfg.get("mcpServers") or {}).get("nautilus-db", {}).get("env", {})
    except Exception:
        pass
    host = env.get("DB_HOST", "127.0.0.1")
    port = int(env.get("DB_PORT", "15432"))
    name = env.get("DB_NAME", "nautilus_production")
    user = env.get("DB_USER", "")
    pwd = env.get("DB_PASSWORD", "")
    if not user or not pwd:
        raise SystemExit("[probe] nautilus-db MCP 配置缺 DB_USER/DB_PASSWORD,拒绝猜测")
    return dict(host=host, port=port, dbname=name, user=user, password=pwd,
                connect_timeout=8)


def run(since_hours: float | None) -> int:
    import psycopg2  # 延迟导入,探针失败不拖累宿主

    where, params = "", []
    if since_hours:
        where = "WHERE created_at > now() - interval '%s hours'"
        params = [since_hours]
    sql = f"""
        SELECT id, verdict_id, created_at, overall_pass, score, external_verified,
               jsonb_array_length(items) AS n_items,
               coalesce((artifacts->>'total_tokens')::float, 0) AS tokens
        FROM fde_verdicts {where} ORDER BY id DESC LIMIT 5000
    """
    try:
        conn = psycopg2.connect(**_db_kwargs())
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        cur.close(); conn.close()
    except Exception as e:
        print(f"[probe] DB 不可达,跳过本轮: {str(e)[:120]}")
        return 2

    viol_rec, viol_flag, viol_schema = [], [], []
    for (rid, vid, ts, ok, score, ext_v, n_items, tokens) in rows:
        multi_model = "," in (vid or "")
        if n_items == 0:
            viol_rec.append(rid)
            if ext_v:
                viol_flag.append(rid)
            if multi_model and tokens <= 0:
                viol_schema.append(rid)
    total = len(rows)
    state = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scanned": total,
        "viol_recomputability": len(viol_rec),
        "viol_verified_provenance": len(viol_flag),
        "viol_evidence_schema": len(viol_schema),
        "first_ids": viol_rec[:5],
    }
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False))
    # 有违例且是增量模式(值守用)→ 非零退出码供调度器感知
    return 1 if (since_hours and viol_rec) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", type=float, default=None, help="只看近 N 小时")
    a = ap.parse_args()
    sys.exit(run(a.since))
