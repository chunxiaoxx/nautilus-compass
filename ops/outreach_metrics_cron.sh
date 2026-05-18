#!/usr/bin/env bash
# Outreach metrics cron wrapper · loads Telegram + PG creds · invokes python.
#
# Cron (cloud) · daily 9am Beijing (01:00 UTC):
#   0 9 * * * /home/ubuntu/nautilus-compass/ops/outreach_metrics_cron.sh \
#             >> /home/ubuntu/.cache/compass/outreach-metrics.log 2>&1
#
# First run sets baseline. Subsequent runs Telegram-push delta vs baseline.
# When user satisfied, `crontab -e` and remove the line.
set -euo pipefail

if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/outreach_metrics.py"
