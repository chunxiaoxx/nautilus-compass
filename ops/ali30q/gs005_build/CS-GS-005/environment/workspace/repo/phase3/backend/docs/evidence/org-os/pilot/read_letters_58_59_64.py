"""读 id 58/59/64 函全文 + 相关函(52/53 上下文)· 只读"""
from urllib.parse import unquote
import sqlalchemy as sa

line = [l for l in open('/home/ubuntu/nautilus-mvp/phase3/backend/.env')
        if l.startswith('DATABASE_URL')][0].split('=', 1)[1].strip()
e = sa.create_engine(unquote(line.strip('"')))

with e.connect() as c:
    rows = c.execute(sa.text(
        "SELECT id, from_agent, to_agent, trace_id, title, body, "
        "created_at, deadline, ack_at FROM org_mailbox "
        "WHERE id IN (52,53,58,59,64) ORDER BY id")).fetchall()
    for r in rows:
        print(f"===== id={r[0]} from={r[1]} to={r[2]} =====")
        print(f"trace: {r[3]}")
        print(f"title: {r[4]}")
        print(f"created: {r[6]}  deadline: {r[7]}  ack_at: {r[8]}")
        print(f"body:\n{r[5]}")
        print()
