#!/usr/bin/env bash
# compass · poll _platform_results/ · ingest into compass memory dir.
# BP3 closure · file→session_*.md · cron-safe · idempotent.
#
# Cron (cloud):
#   */5 * * * * /home/ubuntu/nautilus-compass/ops/platform_results_ingest_cron.sh \
#               >> /home/ubuntu/.cache/compass/platform-results-ingest.log 2>&1
set -euo pipefail

# Load env if present (mostly for COMPASS_PLATFORM_INGEST_PROJECT override)
if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/platform_results_ingest_cron.py"
