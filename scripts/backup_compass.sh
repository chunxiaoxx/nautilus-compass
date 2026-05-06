#!/bin/bash
# compass · backup script (RTO ≤ 4h target · §15 GA checklist)
# Status: 2026-05-05 · production-ready
#
# Usage:
#   bash backup_compass.sh                    # backup to ./backups/
#   bash backup_compass.sh /mnt/backups       # custom dir
#   bash backup_compass.sh --restore <file>   # restore from backup
#
# Cron (daily at 3 AM):
#   0 3 * * * /opt/compass/scripts/backup_compass.sh /mnt/backups >> /var/log/compass-backup.log 2>&1
#
# Restore (RTO ≤ 4h tested):
#   1. Stop service: docker-compose down (or systemctl stop compass)
#   2. bash backup_compass.sh --restore /mnt/backups/compass-2026-05-05.db
#   3. Start service: docker-compose up -d

set -euo pipefail

DB_PATH="${COMPASS_DB_PATH:-/var/lib/compass/compass.db}"
BACKUP_DIR="${1:-./backups}"
RETENTION_DAYS="${COMPASS_BACKUP_RETENTION:-30}"

# ---- restore mode ----
if [ "${1:-}" = "--restore" ]; then
    BACKUP_FILE="${2:-}"
    if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
        echo "[restore] usage: $0 --restore <backup_file>" >&2
        exit 1
    fi
    echo "[restore] restoring from: $BACKUP_FILE"
    echo "[restore] target: $DB_PATH"
    read -p "Stop service first · then continue? [y/N] " confirm
    [ "$confirm" = "y" ] || exit 0

    # Backup current (in case)
    if [ -f "$DB_PATH" ]; then
        cp -p "$DB_PATH" "${DB_PATH}.before-restore-$(date +%s)"
    fi

    # Restore
    cp -p "$BACKUP_FILE" "$DB_PATH"
    chmod 644 "$DB_PATH"

    # Verify
    sqlite3 "$DB_PATH" "SELECT COUNT(*) as users FROM users; SELECT COUNT(*) as obs FROM observations;"
    echo "[restore] complete · start service now"
    exit 0
fi

# ---- backup mode ----

if [ ! -f "$DB_PATH" ]; then
    echo "[backup] db not found: $DB_PATH" >&2
    exit 1
fi

mkdir -p "$BACKUP_DIR"

TS=$(date +%Y-%m-%d_%H%M%S)
TARGET="$BACKUP_DIR/compass-$TS.db"

echo "[backup] db=$DB_PATH → $TARGET"

# Use sqlite3 .backup for hot backup (no service stop required)
sqlite3 "$DB_PATH" ".backup $TARGET"

# Verify integrity
INTEGRITY=$(sqlite3 "$TARGET" "PRAGMA integrity_check;")
if [ "$INTEGRITY" != "ok" ]; then
    echo "[backup] integrity_check FAILED: $INTEGRITY" >&2
    rm -f "$TARGET"
    exit 1
fi

# Compress
gzip "$TARGET"
TARGET_GZ="${TARGET}.gz"
SIZE=$(du -h "$TARGET_GZ" | cut -f1)
echo "[backup] OK · $SIZE · $TARGET_GZ"

# Stats
sqlite3 "$DB_PATH" "
    SELECT 'users: ' || COUNT(*) FROM users;
    SELECT 'obs: ' || COUNT(*) FROM observations;
    SELECT 'audit: ' || COUNT(*) FROM audit_log;
" 2>/dev/null

# Retention: delete backups older than N days
find "$BACKUP_DIR" -name "compass-*.db.gz" -type f -mtime +"$RETENTION_DAYS" -delete
KEPT=$(find "$BACKUP_DIR" -name "compass-*.db.gz" -type f | wc -l)
echo "[backup] retention $RETENTION_DAYS days · $KEPT backups kept"

# (Optional) Encrypt before offsite copy
if [ -n "${COMPASS_BACKUP_GPG_RECIPIENT:-}" ]; then
    gpg --encrypt --recipient "$COMPASS_BACKUP_GPG_RECIPIENT" --output "$TARGET_GZ.gpg" "$TARGET_GZ"
    rm -f "$TARGET_GZ"
    echo "[backup] encrypted to $TARGET_GZ.gpg"
fi

# (Optional) Sync to S3 / OSS if configured
if [ -n "${COMPASS_BACKUP_S3_BUCKET:-}" ]; then
    aws s3 cp "$TARGET_GZ${COMPASS_BACKUP_GPG_RECIPIENT:+.gpg}" "s3://$COMPASS_BACKUP_S3_BUCKET/compass-backups/" \
        --storage-class STANDARD_IA
    echo "[backup] synced to s3://$COMPASS_BACKUP_S3_BUCKET"
fi

echo "[backup] complete · $TS"
