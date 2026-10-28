#!/bin/bash
source /etc/nautilus/secrets.env
TG_CHAT='5888378695'
KPI=$(cd /home/ubuntu/nautilus-mvp/phase3/backend && env $(grep DATABASE_URL .env | xargs) /home/ubuntu/.local/bin/python3 2>/dev/null || cd /home/ubuntu/nautilus-mvp/phase3/backend && env $(grep DATABASE_URL .env | xargs) python3 -c "
import os, psycopg2
conn = psycopg2.connect(os.environ['DATABASE_URL']); cur = conn.cursor()
def s(sql): cur.execute(sql); return cur.fetchone()[0]
print('agents_30m:', s(\"SELECT count(distinct agent_id) FROM agent_tool_calls WHERE ts>NOW()-interval '30 min'\"))
print('helix_30m:', s(\"SELECT count(*) FROM helix_blocks WHERE ts>NOW()-interval '30 min'\"))
print('propose_30m:', s(\"SELECT count(*) FROM agent_tool_calls WHERE tool_name ILIKE '%propose%' AND ts>NOW()-interval '30 min'\"))
print('compass_30m:', s(\"SELECT count(*) FROM agent_tool_calls WHERE tool_name ILIKE '%compass%' AND ts>NOW()-interval '30 min'\"))
print('merged_total:', s(\"SELECT count(*) FROM platform_proposal_reviews WHERE status='merged'\"))
")
MSG="V7 KPI $(date +%H:%M)
$KPI"
curl -s --max-time 5 -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" --data-urlencode "chat_id=${TG_CHAT}" --data-urlencode "text=${MSG}" > /dev/null
