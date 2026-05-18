#!/usr/bin/env bash
# gmail inbound · 每 15min 真扫 unread · 新 reply 真 INSERT outreach-reply-draft bounty
#
# Cron: */15 * * * * /home/ubuntu/nautilus-compass/ops/gmail_inbound_monitor_cron.sh
set -euo pipefail
if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/gmail_inbound_monitor_cron.py"
