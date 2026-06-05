#!/usr/bin/env python3
"""nautilus-compass KPI audit · 看真实使用率 · 1 周后跑.

Adds (2026-05-30 · E.fix-2): `act_on_rate()` function reading
drift_mitigation_log.jsonl to compute act-on rate (closes 5/27 finding's
open loop · detection side ~25k events · ack side previously 0).
"""
import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

LOG = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "usage.jsonl"


def _in_range(rec: dict, since: datetime) -> bool:
    try:
        ts = datetime.fromisoformat(rec["ts"].replace("Z", "+00:00"))
        return ts >= since
    except Exception:
        return False


def act_on_rate(sidecar: Optional[Path] = None, window_hours: float = 168.0) -> dict:
    """E.fix-2 (2026-05-30): drift alert act-on rate over recent window.

    Reads `drift_mitigation_log.jsonl` (shared sidecar for fires + acks per
    E.fix-1) · groups records by `alert_id` · counts how many distinct fires
    (within `window_hours`) received at least one ack (any time).

    A fire record is any non-ack entry with `alert_id` (existing recall.py:159
    writer produces `kind: single_anchor_hit | score_threshold`). An ack record
    is any entry with `kind: "ack"` produced by `drift.act_log.log_drift_ack`.

    Returns:
        {"fires": int,           # distinct fired alert_ids within window
         "acked": int,           # subset of fires that also have an ack
         "rate": float,          # acked / fires · 0.0 when fires == 0
         "window_hours": float}

    5/27 finding (target ≥0.70): historically near 0% · this function makes
    the gap measurable so closure progress can be tracked.
    """
    from drift.act_log import iter_drift_events  # local import · avoid circular at module load

    cutoff = datetime.now(timezone.utc) - timedelta(hours=window_hours)
    fires_by_id: set[str] = set()
    acked_ids: set[str] = set()

    for rec in iter_drift_events(sidecar):
        alert_id = rec.get("alert_id")
        if not alert_id:
            continue
        if rec.get("kind") == "ack":
            acked_ids.add(alert_id)
            continue
        # fire-side: only count if within window
        ts_str = rec.get("ts", "")
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            continue
        if ts < cutoff:
            continue
        fires_by_id.add(alert_id)

    fires = len(fires_by_id)
    acked = len(fires_by_id & acked_ids)
    return {
        "fires": fires,
        "acked": acked,
        "rate": (acked / fires) if fires else 0.0,
        "window_hours": window_hours,
    }


def _print_audit() -> None:
    """Print KPI audit from usage.jsonl · the legacy script body."""
    if not LOG.exists():
        print("no usage log yet · plugin 未真用过")
        return

    events = []
    with open(LOG, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except Exception:
                    pass

    if not events:
        print("usage log empty")
        return

    now = datetime.now(timezone.utc)
    since_24h = now - timedelta(hours=24)
    since_7d = now - timedelta(days=7)

    types_24h = Counter(r["event"] for r in events if _in_range(r, since_24h))
    types_7d = Counter(r["event"] for r in events if _in_range(r, since_7d))
    profiles_7d = Counter(r.get("anchors_profile", "?") for r in events if _in_range(r, since_7d))

    print(f"=== nautilus-compass KPI · {now.strftime('%Y-%m-%d %H:%M UTC')} ===")

    # v0.7.2 · 24h recall_hit=0 自动报警 (daemon 没跑/失联)
    recall_24h = types_24h.get("recall_hit", 0)
    strategy_24h = types_24h.get("strategy_hit", 0)
    if recall_24h == 0 and strategy_24h > 0:
        print(f"\n🚨 ALERT · 24h recall_hit=0 · daemon 可能 down")
        print(f"   strategy_hit={strategy_24h} 说明 hook 在跑 · 但 BGE 召回 0 次 = daemon 失联或没启动")
        print(f"   修: nohup python ~/.claude/plugins/nautilus-compass/daemon.py > /tmp/compass_daemon.log 2>&1 &")
        print(f"   测: python -c \"import socket;s=socket.socket();s.settimeout(2);s.connect(('127.0.0.1',9876));s.sendall(b'\\\"action\\\":\\\"ping\\\"\\\\n');print(s.recv(64))\"")
    elif recall_24h == 0 and strategy_24h == 0:
        print(f"\n⚠️ 24h 无任何事件 · plugin hook 可能没装/没跑 · 检查 ~/.claude/settings.json")

    print(f"\n总事件: {len(events)}")
    print(f"\n24h 内 ({sum(types_24h.values())} events):")
    for k, v in types_24h.most_common():
        print(f"  · {k}: {v}")
    print(f"\n7d 内 ({sum(types_7d.values())} events):")
    for k, v in types_7d.most_common():
        print(f"  · {k}: {v}")
    print(f"\nProfile 分布 (7d):")
    for k, v in profiles_7d.most_common():
        print(f"  · {k}: {v}")

    # 价值估算
    drift_alerts = types_7d.get("drift_alert", 0)
    strategy_hits = types_7d.get("strategy_hit", 0)
    recall_hits = types_7d.get("recall_hit", 0)
    print(f"\n=== 7d 价值估算 ===")
    print(f"  · 反锚点 alert: {drift_alerts} (拦了 {drift_alerts} 次潜在错误)")
    print(f"  · Strategy 命中: {strategy_hits} (复用了 {strategy_hits} 次推理路径)")
    print(f"  · Memory 召回: {recall_hits} (避免了 {recall_hits} 次冷启)")
    total_value = drift_alerts * 5 + strategy_hits * 3 + recall_hits * 1
    print(f"  · 估算价值分: {total_value} (alert×5 + strategy×3 + recall×1)")

    # E.fix-2 (2026-05-30): act-on rate · north-star ≥0.70 per 5/27 finding
    try:
        aor = act_on_rate(window_hours=24)
        aor_7d = act_on_rate(window_hours=168)
        print(f"\n=== act-on rate (drift alert closure · target ≥0.70) ===")
        print(f"  · 24h: fires={aor['fires']:<4d} acked={aor['acked']:<4d} rate={aor['rate']:.3f}")
        print(f"  ·  7d: fires={aor_7d['fires']:<4d} acked={aor_7d['acked']:<4d} rate={aor_7d['rate']:.3f}")
    except Exception as e:
        print(f"\n(act_on_rate skipped: {e})")


if __name__ == "__main__":
    _print_audit()
