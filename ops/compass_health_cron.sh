#!/usr/bin/env bash
# Compass health cron wrapper · loads Telegram creds + invokes python.
#
# Cron (cloud):
#   */5 * * * * /home/ubuntu/nautilus-compass/ops/compass_health_cron.sh \
#               >> /home/ubuntu/.cache/compass/health-cron.log 2>&1
set -euo pipefail

if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/compass_health_cron.py"
