#!/bin/bash
# C 方案 · platform evolve cron · 5min/run · log to /var/log/nautilus/platform_evolve.log
set -e
LOG_DIR=/var/log/nautilus
mkdir -p "$LOG_DIR"
TS=$(date '+%Y-%m-%d %H:%M:%S')
{
  echo "=== $TS ==="
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production \
    -f /opt/nautilus/platform_evolve_cron.sql 2>&1
} >> "$LOG_DIR/platform_evolve.log" 2>&1
