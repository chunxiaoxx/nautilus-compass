#!/bin/bash
# compass · audit_log retention enforcement
# Runs daily via cron · purges audit entries older than 90 days
# Per V10_FINAL_SPEC §13 (compliance · GDPR Article 5.1.e storage limitation)
#
# Cron: 0 4 * * * /opt/compass/scripts/audit_retention_cron.sh

set -euo pipefail

DB_PATH="${COMPASS_DB_PATH:-/var/lib/compass/compass.db}"
RETENTION_DAYS="${COMPASS_AUDIT_RETENTION:-90}"
LOG="/var/log/compass-audit-retention.log"

if [ ! -f "$DB_PATH" ]; then
    echo "[$(date)] db not found · skip" | tee -a "$LOG"
    exit 0
fi

# Count what will be deleted
N_BEFORE=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM audit_log
    WHERE ts < datetime('now', '-$RETENTION_DAYS days');
" 2>/dev/null || echo "0")

if [ "$N_BEFORE" = "0" ]; then
    echo "[$(date)] 0 audit entries to purge · ok" | tee -a "$LOG"
    exit 0
fi

# Hard delete
sqlite3 "$DB_PATH" "
    DELETE FROM audit_log
    WHERE ts < datetime('now', '-$RETENTION_DAYS days');
    VACUUM;
"

# Verify
N_AFTER=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM audit_log;")
PURGED=$((N_BEFORE - 0))

echo "[$(date)] retention=$RETENTION_DAYS · purged=$PURGED · remaining=$N_AFTER" | tee -a "$LOG"

# Also: hard-delete soft-deleted users past 30d
N_USERS_HARD_DEL=$(sqlite3 "$DB_PATH" "
    SELECT COUNT(*) FROM users
    WHERE deleted_at IS NOT NULL
    AND deleted_at < datetime('now', '-30 days');
" 2>/dev/null || echo "0")

if [ "$N_USERS_HARD_DEL" != "0" ]; then
    echo "[$(date)] hard-deleting $N_USERS_HARD_DEL users past 30d soft-delete" | tee -a "$LOG"
    sqlite3 "$DB_PATH" "
        DELETE FROM observations WHERE user_id IN (
            SELECT user_id FROM users WHERE deleted_at IS NOT NULL
            AND deleted_at < datetime('now', '-30 days')
        );
        DELETE FROM agents WHERE user_id IN (
            SELECT user_id FROM users WHERE deleted_at IS NOT NULL
            AND deleted_at < datetime('now', '-30 days')
        );
        DELETE FROM profiles WHERE user_id IN (
            SELECT user_id FROM users WHERE deleted_at IS NOT NULL
            AND deleted_at < datetime('now', '-30 days')
        );
        DELETE FROM users
        WHERE deleted_at IS NOT NULL
        AND deleted_at < datetime('now', '-30 days');
    "
fi

echo "[$(date)] retention cron complete" | tee -a "$LOG"
