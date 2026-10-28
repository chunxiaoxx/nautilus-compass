source /etc/nautilus/secrets.env
#!/usr/bin/env bash
# V7 Marketing Daily Preview · W2 Gate 3
# Cron: daily 21:00 -> push top 5 approved+published marketing posts (last 24h)
#                      to Telegram chat 5888378695
# Usage:
#   v7-marketing-daily-preview.sh          # real send
#   v7-marketing-daily-preview.sh --dry    # stdout only
set -e
set -o pipefail

DRY_RUN="${1:-}"
DSN="${DATABASE_URL:-postgresql://nautilus_user:${PGPASSWORD}@127.0.0.1:5432/nautilus_production}"
BOT_TOKEN="${V7_BOT_TOKEN}"
CHAT_ID="${V7_CHAT_ID:-5888378695}"

DATE=$(date +%Y-%m-%d)
NOW=$(date +%H:%M)

# Pull top 5 approved+published in last 24h, ordered by score desc.
# Falls back to "approved+pending publish" if none published yet (so preview
# still shows planned posts).
QUERY=$(cat <<'SQL'
WITH published AS (
  SELECT id, channel, score, writer_agent,
         LEFT(draft_text, 240) AS preview,
         post_id, published_at, 'published' AS state
  FROM platform_marketing_review
  WHERE approved = TRUE
    AND published_at IS NOT NULL
    AND published_at >= NOW() - INTERVAL '24 hours'
  ORDER BY score DESC NULLS LAST, published_at DESC
  LIMIT 5
),
fallback AS (
  SELECT id, channel, score, writer_agent,
         LEFT(draft_text, 240) AS preview,
         post_id, reviewed_at AS published_at, 'approved' AS state
  FROM platform_marketing_review
  WHERE approved = TRUE
    AND published_at IS NULL
    AND reviewed_at >= NOW() - INTERVAL '24 hours'
  ORDER BY score DESC NULLS LAST, reviewed_at DESC
  LIMIT 5
)
SELECT id, channel, score, writer_agent, preview, post_id, published_at, state
FROM published
UNION ALL
SELECT id, channel, score, writer_agent, preview, post_id, published_at, state
FROM fallback
WHERE NOT EXISTS (SELECT 1 FROM published)
LIMIT 5;
SQL
)

ROWS=$(psql "$DSN" -At -F'|' -c "$QUERY")

if [ -z "$ROWS" ]; then
  MSG="*V7 Marketing Daily Preview · ${DATE} ${NOW}*
No approved marketing posts in last 24h.
(Quality gate working: nothing slipped through.)"
else
  MSG="*V7 Marketing Daily Preview · ${DATE} ${NOW}*
Top 5 approved posts (last 24h):
"
  IDX=1
  while IFS='|' read -r id channel score writer preview post_id pub_at state; do
    [ -z "$id" ] && continue
    SCORE_FMT=$(printf "%.1f" "${score:-0}")
    REJECT_LINK="https://www.nautilus.social/admin/marketing/reject?id=${id}&token=v7w2"
    MSG="${MSG}
${IDX}. [${state}] ch=${channel} · score=${SCORE_FMT} · by ${writer}
   ${preview}
   reject 24h: ${REJECT_LINK}
"
    IDX=$((IDX + 1))
  done <<< "$ROWS"
fi

if [ "$DRY_RUN" = "--dry" ]; then
  echo "===== DRY RUN · would send to chat_id=$CHAT_ID ====="
  echo "$MSG"
  echo "===== /DRY RUN ====="
  exit 0
fi

# Real send
RESP=$(curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
  -d chat_id="${CHAT_ID}" \
  -d parse_mode="Markdown" \
  --data-urlencode "text=${MSG}")
echo "[$(date -Iseconds)] sent: $(echo "$RESP" | head -c 200)"
