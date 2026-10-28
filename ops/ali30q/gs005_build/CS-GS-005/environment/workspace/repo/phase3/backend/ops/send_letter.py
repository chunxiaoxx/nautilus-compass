#!/usr/bin/env python
"""平台发函工具——云 DB 直写 org_mailbox。

背景:收函只认 org_mailbox(2026-09-24 纪律),平台发函走云 DB 直写。
deadline 一律 now+2h 动态算(禁手写绝对时间戳,2026-09 教训)。

用法(在 phase3/backend/ 下):
  python ops/send_letter.py --to v5 --title "[回执] ..." --body-file reply.md
  python ops/send_letter.py --ack 1797 --ack-note "验收收讫"
  echo "正文" | python ops/send_letter.py --to soul --title "..." --body -
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/
from sqlalchemy import text  # noqa: E402

from utils.database import SessionLocal  # noqa: E402

DB_TZ = ZoneInfo("Asia/Shanghai")  # org_mailbox 时间列 = 上海 naive(platform_loop 同规)


def _now() -> datetime:
    return datetime.now(DB_TZ).replace(tzinfo=None)


def send_letter(to: str, title: str, body: str, from_agent: str = "platform") -> int:
    trace = f"platform-{_now():%Y%m%d%H%M}-{to}"
    with SessionLocal() as s:
        r = s.execute(
            text(
                "INSERT INTO org_mailbox (trace_id, from_agent, to_agent, title, body, deadline) "
                "VALUES (:t, :f, :to, :ti, :b, now() + interval '2 hours') RETURNING id"
            ),
            {"t": trace, "f": from_agent, "to": to, "ti": title, "b": body},
        ).fetchall()
        s.commit()
        return r[0][0]


def ack(mail_id: int, note: str) -> bool:
    with SessionLocal() as s:
        n = s.execute(
            text("UPDATE org_mailbox SET ack_at=now(), ack_note=:n WHERE id=:i AND to_agent='platform'"),
            {"n": note, "i": mail_id},
        ).rowcount
        s.commit()
        return n > 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--to", help="收件 agent 名")
    ap.add_argument("--title", help="函件标题")
    ap.add_argument("--body", help="正文;'-' 表示读 stdin")
    ap.add_argument("--body-file", help="正文文件路径")
    ap.add_argument("--ack", type=int, help="同时 ack 的函件 id")
    ap.add_argument("--ack-note", default="收讫", help="ack 备注")
    ap.add_argument("--from", dest="from_agent", default=None,
                    help="署名(缺省 MAIL_FROM env,再缺省 platform)——借工具的他框 agent 必须显式带")
    args = ap.parse_args()

    if args.ack:
        print(f"ack #{args.ack}: {ack(args.ack, args.ack_note)}")

    if args.to:
        body = sys.stdin.read() if args.body == "-" else (
            Path(args.body_file).read_text(encoding="utf-8") if args.body_file else (args.body or "")
        )
        import os
        frm = args.from_agent or os.environ.get("MAIL_FROM") or "platform"
        mid = send_letter(args.to, args.title or "(无标题)", body, from_agent=frm)
        print(f"sent #{mid} → {args.to}")


if __name__ == "__main__":
    main()
