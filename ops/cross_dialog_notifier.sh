#!/usr/bin/env bash
# Cross-dialog handoff notifier · loads Telegram env + invokes python.
#
# Cron (cloud):
#   */5 * * * * /home/ubuntu/nautilus-compass/ops/cross_dialog_notifier.sh \
#               >> /home/ubuntu/.cache/compass/cross-dialog-notifier.log 2>&1
set -euo pipefail

# Load TELEGRAM_BOT_TOKEN / CHAT_ID from V5 .env (single source on cloud)
if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/cross_dialog_notifier.py"
