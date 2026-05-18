#!/usr/bin/env bash
# arxiv discovery · 每 6h 真扫 new papers · INSERT outreach-discovery bounty raid
#
# Cron: 0 */6 * * * /home/ubuntu/nautilus-compass/ops/arxiv_discovery_cron.sh
set -euo pipefail
if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/arxiv_discovery_cron.py"
