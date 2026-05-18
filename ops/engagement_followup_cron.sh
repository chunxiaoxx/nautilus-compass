#!/usr/bin/env bash
# engagement followup · daily 真扫 7-21d 无回 outreach · INSERT followup bounty
#
# Cron: 30 9 * * * /home/ubuntu/nautilus-compass/ops/engagement_followup_cron.sh
set -euo pipefail
if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/engagement_followup_cron.py"
