#!/usr/bin/env bash
# L2 evidence gate Telegram alert · cron every 6h
#
# Reads /var/log/compass-l2-metrics.json (written by compass_l2_metrics.py)
# If V5/V6/V7/Kairos miss the ≥10/day gate for 3 consecutive runs (18h) ·
# sends Telegram alert · 24h cooldown per agent to avoid spam.
#
# Cron:
#   0 */6 * * * /home/ubuntu/nautilus-compass/ops/monitor_l2_evidence_gate.sh \
#               >> /var/log/compass-l2-gate.log 2>&1
#
# Bash here is just env loading + curl · all logic in monitor_l2_evidence_gate.py
set -euo pipefail

# Load Telegram creds from V5 .env (single source of truth on cloud)
if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi

if [ -z "${TELEGRAM_BOT_TOKEN:-}" ] || [ -z "${TELEGRAM_CHAT_ID:-}" ]; then
  echo "$(date -u +%FT%TZ) · ERR · TELEGRAM_BOT_TOKEN/CHAT_ID not set" >&2
  exit 1
fi

# Python does all parsing · state tracking · alert decision
# Outputs Telegram message text on stdout if alert needed · empty otherwise
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
msg="$(python3 "$SCRIPT_DIR/monitor_l2_evidence_gate.py")"

if [ -z "$msg" ]; then
  echo "$(date -u +%FT%TZ) · all required agents at gate or in cooldown · no alert"
  exit 0
fi

# Send Telegram alert
resp="$(curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    --data-urlencode "text=${msg}")"

ok="$(echo "$resp" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ok',False))")"
echo "$(date -u +%FT%TZ) · alert sent · telegram_ok=$ok"
