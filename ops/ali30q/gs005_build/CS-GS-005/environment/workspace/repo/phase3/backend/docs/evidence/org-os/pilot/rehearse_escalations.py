"""误升级预演:用 loop 自身逻辑对未来各时点跑 classify_letters。"""
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")
from ops.platform_loop import classify_letters, load_platform_letters  # noqa: E402

letters = load_platform_letters()
now = datetime.utcnow()
print(f"=== now UTC {now:%m-%d %H:%M} · platform 发出函共 {len(letters)} 封")
for l in sorted(letters, key=lambda x: x["id"]):
    dl = l["deadline"]
    if isinstance(dl, datetime):
        dl_s, dl_dt = f"{dl:%m-%d %H:%M}", dl
    else:
        dl_dt = datetime.fromisoformat(str(dl))
        dl_s = str(dl)
    overdue = "超期" if dl_dt <= now else f"余{dl_dt-now}"
    flags = []
    if l["has_reply"]:
        flags.append("已回")
    if l["ack_at"]:
        flags.append("已ack")
    if l["notified_at"]:
        flags.append(f"已亮牌{str(l['notified_at'])[5:16]}")
    print(f"  #{l['id']:>3} →{l['to_agent']:<9} dl={dl_s}Z {overdue:<14} "
          f"{' '.join(flags) or '—'} {l['trace_id'][:42]}")

print("\n=== 未来各时点 classify_letters 预演(escalate/takeover)")
for delta_h, label in [(0, "现在"), (4, "+4h"), (8, "+8h"),
                       (16, "明早+16h"), (24, "+24h")]:
    t = now + timedelta(hours=delta_h)
    v = classify_letters(letters, t)
    print(f"  [{label} {t:%m-%d %H:%M}Z] escalate="
          f"{[x['id'] for x in v['escalate']]} takeover="
          f"{[x['id'] for x in v['takeover']]} pending={v['pending']} "
          f"resolved={v['resolved']} acked={v['acked']}")

# 回函匹配缺口检查:全表双向,找前缀匹配但未标 has_reply 的
print("\n=== 回函匹配缺口扫描(全表含双向)")
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402
sess = SessionLocal()
rows = sess.query(OrgMailbox).all()
sess.close()
all_rows = [dict(id=r.id, from_agent=r.from_agent, to_agent=r.to_agent,
                 trace_id=r.trace_id, created_at=r.created_at,
                 ack_at=r.ack_at) for r in rows]
by_to = {}
for l in letters:
    by_to.setdefault(l["to_agent"], []).append(l)
gaps = 0
for r in all_rows:
    if r["from_agent"] == "platform":
        continue  # 平台自发函(升级/自扰)不作回函——与 loop match_replies 同口径
    for orig in by_to.get(r["from_agent"], []):
        if (r["id"] != orig["id"]
                and r["trace_id"].startswith(orig["trace_id"])
                and r["created_at"] and orig["_created"]
                and r["created_at"] >= orig["_created"]
                and not orig["has_reply"]):
            gaps += 1
            print(f"  ⚠️ #{orig['id']} 未标已回但 #{r['id']}"
                  f"(from={r['from_agent']},trace={r['trace_id'][:40]})"
                  f"前缀匹配")
print(f"  缺口数={gaps}" if gaps else "  无缺口,has_reply 判定与全表一致")
