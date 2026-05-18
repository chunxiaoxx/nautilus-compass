#!/usr/bin/env bash
# compass · weekly memory compaction · 老 session_*.md → Haiku 摘要 sidecar
#
# Cron (cloud · weekly Sun 04:00):
#   0 4 * * 0 /home/ubuntu/nautilus-compass/ops/memory_compact_cron.sh \
#             >> /home/ubuntu/.cache/compass/memory-compact.log 2>&1
set -euo pipefail

if [ -f /home/ubuntu/nautilus-v5/.env ]; then
  set -a
  # shellcheck disable=SC1091
  . /home/ubuntu/nautilus-v5/.env
  set +a
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/memory_compact_cron.py"
