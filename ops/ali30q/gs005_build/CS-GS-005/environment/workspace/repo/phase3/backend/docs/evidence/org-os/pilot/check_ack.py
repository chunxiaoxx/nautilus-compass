"""核对 compass 收函的真实 ack 状态(试点发现#4 验证)· 只读"""
from urllib.parse import unquote
import sqlalchemy as sa

line = [l for l in open('/home/ubuntu/nautilus-core/phase3/backend/.env') if l.startswith('DATABASE_URL')][0].split('=', 1)[1].strip()
url = unquote(line.strip('"'))
e = sa.create_engine(url)

with e.connect() as c:
    rows = c.execute(sa.text(
        "SELECT id, trace_id, ack_at IS NOT NULL, ack_at FROM org_mailbox "
        "WHERE to_agent='compass' ORDER BY id")).fetchall()
    print(f"compass 收函 {len(rows)} 封:")
    for r in rows:
        print(f"  id={r[0]} acked={r[2]} ack_at={r[3]} trace={(r[1] or '')[:55]}")

    # 对照:platform 收到的回函(41/43/44/45-51)
    rows2 = c.execute(sa.text(
        "SELECT id, from_agent, ack_at IS NOT NULL FROM org_mailbox "
        "WHERE to_agent='platform' AND id>=41 ORDER BY id")).fetchall()
    print(f"\nplatform 收到的回函(id>=41):{len(rows2)} 封:")
    for r in rows2:
        print(f"  id={r[0]} from={r[1]} acked={r[2]}")
