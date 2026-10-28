#!/usr/bin/env python3
"""渲染 canonical RSI+FDE 看板的离线快照(真飞轮数据·双击即开).

复用 api.platform_rsi_fde 的 canonical 看板 HTML + section builders(不另造页),
用真实飞轮 verdict 数据(本 session c2d 转一圈的 verdict + 已存在的 soul track)喂进去,
注入成离线 snapshot(fetch 失败也能开). 产出 = 与 live 看板同一视图的可交付文件.

用法: PYTHONUTF8=1 PYTHONPATH=. python scripts/render_flywheel_snapshot.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
from models.fde_verdict import FdeVerdict  # noqa: F401 · register table
from api import platform_rsi_fde as view

RESULT = Path(__file__).resolve().parent / "flywheel_demo_result.json"
BATCH = Path(__file__).resolve().parent / "flywheel_batch_result.json"
OUT = Path(__file__).resolve().parent / "flywheel_dashboard_snapshot.html"


def _real_verdicts():
    """优先用批量结果(全燃料集·真实 pass/fail 分布), 否则单题 demo."""
    if BATCH.exists():
        return json.loads(BATCH.read_text(encoding="utf-8")).get("verdicts") or []
    vb = json.loads(RESULT.read_text(encoding="utf-8")).get("verdict_body")
    return [vb] if vb else []


def _seed_db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    rows = []
    # 真: 飞轮转过的确定性 verdict(source=compass/bench_eval).
    for vb in _real_verdicts():
        rows.append((vb["verdict_id"], vb["task_uid"], vb["source"],
                     1 if vb["overall_pass"] else 0, float(vb["score"])))
    # 真: 已在生产存在的第3类 soul-judged 题(track 对照·见 control-plane 实测).
    rows.append(("soul|l0fire_ignite_huffman_20260614", "l0fire_ignite_huffman_20260614", "soul", 1, 0.8))
    rows.append(("soul|qc|expert_t2_drift_detection_20260612|a8b807a3ab",
                 "expert_t2_drift_detection_20260612", "soul", 1, 1.0))
    with engine.begin() as conn:
        for i, (vid, tu, src, ok, sc) in enumerate(rows):
            conn.execute(text(
                "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts, created_at) "
                "VALUES (:vid,:tu,:src,:ok,0,:sc,'[]','{}',CURRENT_TIMESTAMP)"),
                {"vid": vid, "tu": tu, "src": src, "ok": ok, "sc": sc})
    return sessionmaker(bind=engine)()


def main():
    db = _seed_db()
    snapshot = {
        "success": True,
        "data": {
            "verdicts": view._verdicts_section(db, 20),
            "flywheel": view._flywheel_section(db, 20),
            "agents": view._agents_section(db),
            "events": view._events_section(db, 20),
            "poi": view._poi_section(db),
            "generated_at": "2026-06-15 (snapshot · 真飞轮数据)",
        },
    }
    # 复用 canonical 看板 HTML, 把 live fetch 换成注入的离线 snapshot(双击即开).
    html = view._DASHBOARD_HTML.replace(
        "const res = await fetch('/api/platform/rsi-fde?limit=20');\n    const body = await res.json();",
        "const body = window.__SNAPSHOT__;",
    )
    inject = f"<script>window.__SNAPSHOT__ = {json.dumps(snapshot, ensure_ascii=False)};</script>\n</head>"
    html = html.replace("</head>", inject, 1)
    OUT.write_text(html, encoding="utf-8")
    det = snapshot["data"]["flywheel"]["deterministic"]
    print(f"[snapshot] {OUT}")
    print(f"  飞轮确定性 track: {det['passed']}/{det['total']} 过 · by_source={[s['source'] for s in snapshot['data']['flywheel']['by_source']]}")
    print(f"  PoI 可计入: {snapshot['data']['poi']['poi_eligible']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
