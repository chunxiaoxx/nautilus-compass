#!/usr/bin/env python3
"""nautilus-compass KPI audit · 看真实使用率 · 1 周后跑."""
import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")  # safe · no buffer aliasing
except Exception:
    pass

LOG = Path.home() / ".claude" / "plugins" / "nautilus-compass" / ".cache" / "usage.jsonl"

if not LOG.exists():
    print("no usage log yet · plugin 未真用过")
    sys.exit(0)

events = []
with open(LOG, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            try: events.append(json.loads(line))
            except: pass

if not events:
    print("usage log empty")
    sys.exit(0)

now = datetime.now(timezone.utc)
since_24h = now - timedelta(hours=24)
since_7d = now - timedelta(days=7)

def in_range(rec, since):
    try:
        ts = datetime.fromisoformat(rec["ts"].replace("Z", "+00:00"))
        return ts >= since
    except: return False

types_24h = Counter(r["event"] for r in events if in_range(r, since_24h))
types_7d = Counter(r["event"] for r in events if in_range(r, since_7d))
profiles_7d = Counter(r.get("anchors_profile", "?") for r in events if in_range(r, since_7d))

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
