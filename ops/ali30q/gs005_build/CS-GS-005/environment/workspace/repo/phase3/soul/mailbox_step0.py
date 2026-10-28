"""步0 · 开轮先收信(中枢融合条一 · 20260928 平台修)。

soul daemon 原先只发不收(9/25-28 欠 ack 八封,评测令/UniPat/协议全盲)。
本模块在 run_once 开头调用:
- 扫 org_mailbox to='soul' 未 ack;
- 知会类(标题含 loop-diff / [知会] / [协议通告] / [通报] / 宪法)→ 自动 ack「机审线代收讫」;
- 其余(需答复)→ 追加写 .soul-inbox-pending.md(逐封一行),供本轮目标选择参考;
  并向 platform 发一封回执函(告知待答清单已入队)——平台侧可见 soul 已不聋。

fail-soft:本模块任何异常只记日志,不阻断主循环(宪法:回函通道保活)。
"""

from __future__ import annotations

import datetime as _dt
import logging
import os
import re

import psycopg2
import psycopg2.extras

logger = logging.getLogger("soul.mailbox_step0")

AUTO_ACK_MARKERS = ("loop-diff", "[知会]", "[协议通告]", "[通报]", "宪法", "[中继]")
PENDING_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".soul-inbox-pending.md")
# 2026-10-05 刷屏根治:待答集合不变则不发回执函(此前每轮 pending 非空即发,
# 24h 刷 12+ 封"[步0回执]"= 假活性噪音)。记上次已通知的 id 集,变化才发。
LAST_NOTIFY_FILE = PENDING_FILE + ".notified.json"


def _conn():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend", ".env")
        if os.path.isfile(cfg_path):
            for line in open(cfg_path, encoding="utf-8", errors="replace"):
                if line.startswith("DATABASE_URL="):
                    url = line.split("=", 1)[1].strip()
                    break
    return psycopg2.connect(url)


def run_step0() -> int:
    """Returns count of pending (non-auto-acked) letters. Fail-soft → 0."""
    handled = 0
    try:
        with _conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, title, body, deadline FROM org_mailbox "
                "WHERE to_agent='soul' AND ack_at IS NULL ORDER BY id"
            )
            rows = cur.fetchall()
            pending = []
            for r in rows:
                title = (r["title"] or "")
                if any(m in title for m in AUTO_ACK_MARKERS):
                    cur.execute(
                        "UPDATE org_mailbox SET ack_at=now(), ack_note='soul步0自动收讫(知会类·机审线代)' WHERE id=%s AND ack_at IS NULL",
                        (r["id"],),
                    )
                    handled += 1
                else:
                    deadline = r["deadline"].strftime("%m-%d %H:%M") if r.get("deadline") else "无死期"
                    excerpt = re.sub(r"\s+", " ", (r["body"] or ""))[:160]
                    pending.append(f"- #{r['id']} | {title[:70]} | 死期 {deadline} | {excerpt}")

            if pending:
                stamp = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
                with open(PENDING_FILE, "a", encoding="utf-8") as f:
                    f.write(f"\n## 步0待答清单 {stamp}\n" + "\n".join(pending) + "\n")
                pending_ids = [r["id"] for r in rows if not any(m in (r["title"] or "") for m in AUTO_ACK_MARKERS)]
                last_ids = []
                if os.path.isfile(LAST_NOTIFY_FILE):
                    try:
                        import json
                        with open(LAST_NOTIFY_FILE, encoding="utf-8") as jf:
                            last_ids = json.load(jf)
                    except Exception:  # noqa: BLE001 — 状态文件坏了当空,重发一次无害
                        last_ids = []
                new_ids = set(pending_ids) - set(last_ids)
                if not new_ids:
                    logger.info("step0: no new pending letters (%d outstanding) · skip receipt letter", len(pending))
                    return len(pending)
                import json
                with open(LAST_NOTIFY_FILE, "w", encoding="utf-8") as jf:
                    json.dump(pending_ids, jf)
                cur.execute(
                    "INSERT INTO org_mailbox (trace_id, from_agent, to_agent, title, body, deadline) "
                    "VALUES (%s, 'soul', 'platform', %s, %s, now() + interval '4 hours')",
                    (
                        f"soul-step0-{stamp.replace(' ', '-').replace(':', '')}",
                        "[步0回执] soul 信箱已接线,待答 %d 封入队" % len(pending),
                        "中枢融合条一落地(20260928 平台修):soul 开轮自动收信。当前待答:\n"
                        + "\n".join(pending[:12]),
                    ),
                )
        logger.info("step0 done: auto-acked=%d pending=%d", handled, len(pending))
        return len(pending)
    except Exception as e:  # noqa: BLE001 — 步0绝不阻断主循环
        logger.warning("step0 fail-soft: %s", e)
        return 0
