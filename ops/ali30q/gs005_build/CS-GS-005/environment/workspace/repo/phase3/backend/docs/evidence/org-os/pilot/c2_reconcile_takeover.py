"""C2 函件对账 · L2 接管版(实证 #120/#125 两函 SLA 未回,compass 记违约×2)。

独立复算(不 import loop 代码,防自指验证):回函判定/escalated 落库/孤儿函/
提前亮牌四项对账 mailbox DB vs loop_state.json。
产出: docs/evidence/org-os/pilot/c2_reconcile_result_20260901.md
云端跑: cd /home/ubuntu/nautilus-mvp/phase3/backend && python3 <this>
"""
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, ".")
import models.agent_survival  # noqa: F401  (mapper chain)
from models.org_mailbox import OrgMailbox  # noqa: E402
from utils.database import SessionLocal  # noqa: E402

VALID_TO = {"v5", "compass", "flywheel", "platform"}  # 正身名(#115 教训)

s = SessionLocal()
rows = s.query(OrgMailbox).all()
letters = [r for r in rows if r.from_agent == "platform"]


def is_reply(r, o):
    """独立版回函判定:from=原收件人 且(trace前缀 或 标题引用#id) 且晚于原函。"""
    if not r.created_at or not o.created_at or r.created_at < o.created_at:
        return False
    if r.trace_id and o.trace_id and r.trace_id.startswith(o.trace_id):
        return True
    return f"#{o.id}" in (r.title or "")


by_to: dict[str, list] = {}
for l in letters:
    by_to.setdefault(l.to_agent, []).append(l)
resolved_ids: set[int] = set()
for r in rows:
    if r.from_agent == "platform":
        continue
    for o in by_to.get(r.from_agent, []):
        if r.id != o.id and is_reply(r, o):
            resolved_ids.add(o.id)

state = json.loads(Path("ops/loop_state.json").read_text(encoding="utf-8"))
last = state.get("last_stats", {})
loop_resolved = last.get("resolved")

# escalated 条目必须在 mailbox 有函且已亮牌
esc_bad = []
for ent in last.get("escalated", []):
    to, _, trace = ent.partition(":")
    hit = [r for r in rows
           if r.to_agent == to and (r.trace_id or "").startswith(trace)]
    if not hit or all(h.notified_at is None for h in hit):
        esc_bad.append(ent)

# 孤儿函:收件人非正身名(实证 #115 发 compass-daemon-001 永无回函)
orphans = [(r.id, r.to_agent) for r in letters
           if r.to_agent not in VALID_TO]

# 提前亮牌:notified_at 早于 deadline(喂 #107 审计案)
early = [(r.id, str(r.deadline), str(r.notified_at)) for r in letters
         if r.notified_at and r.deadline and r.notified_at < r.deadline]

match = "一致" if len(resolved_ids) == loop_resolved else \
    f"不一致(复算 {sorted(resolved_ids)} vs 自报 {loop_resolved} → 审计线索)"
lines = [
    f"# C2 函件对账 · L2 接管版({datetime.utcnow():%Y-%m-%d %H:%M}Z)",
    "",
    f"- mailbox 总函 {len(rows)}(platform 发出 {len(letters)})",
    f"- resolved:独立复算 {len(resolved_ids)} vs loop 自报 {loop_resolved} → {match}",
    f"- escalated 落库断言(有函+已亮牌): {'全过' if not esc_bad else esc_bad}",
    f"- 孤儿函(收件人非正身): {orphans or '无'}",
    f"- 提前亮牌(notified_at<deadline,喂 #107 审计): {early or '无'}",
    "",
    "## 接管处置",
    "- 接管原因:#120(C2) deadline 08:00Z、#125(CPU) 07:30Z 均无回函且 grace 过",
    "  → compass 记 SLA 违约 ×2(协议 §4)。",
    "- #125 事实闭环:复查 compass-bge-daemon 已无高 CPU(active 7h,top 峰值",
    "  6.2%),compass 框已自行处置,平台无需代加护栏。",
    "- C2 对账本体=本文件(平台代执行,结果如上)。",
    "",
    "— platform C2-L2-takeover",
]
out = Path("docs/evidence/org-os/pilot/c2_reconcile_result_20260901.md")
out.write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))
s.close()
