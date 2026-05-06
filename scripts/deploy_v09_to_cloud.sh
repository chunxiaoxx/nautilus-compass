#!/bin/bash
# compass v0.9.0-dev → cloud :8770 · UPDATED 2026-05-06 · 14 step production-ready
#
# Run from local dev box (assumes:
#   - ssh alias 'cloud' = 43.160.239.61:24860
#   - PEM auth set up
#   - all v0.9 files present in $PLUGIN_DIR
# )
#
# Usage:
#   bash deploy_v09_to_cloud.sh                # interactive · pauses on each step
#   bash deploy_v09_to_cloud.sh --auto         # no pauses · for CI
#   bash deploy_v09_to_cloud.sh --dry-run      # show actions only

set -euo pipefail

CLOUD="${COMPASS_CLOUD:-cloud}"
CLOUD_PORT="${COMPASS_CLOUD_PORT:-24860}"
PLUGIN_DIR="${PLUGIN_DIR:-$HOME/.claude/plugins/nautilus-compass}"
REMOTE_DIR="${REMOTE_DIR:-/home/ubuntu/compass}"
DRY_RUN=false
AUTO=false

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=true ;;
        --auto) AUTO=true ;;
    esac
done

ssh_remote() {
    if $DRY_RUN; then
        echo "[dry] ssh $CLOUD: $*"
    else
        ssh -p "$CLOUD_PORT" "$CLOUD" "$@"
    fi
}

confirm() {
    if $AUTO; then return 0; fi
    read -p "[$1] continue? [Y/n] " r
    [ "${r:-Y}" = "Y" ] || [ "${r:-y}" = "y" ]
}

log() { echo "==> $*"; }

# ============================================================
# STEP 1 · pre-flight tests (local)
# ============================================================
log "STEP 1 · pre-flight local tests"
cd "$PLUGIN_DIR"
PYTHONUTF8=1 python tests/test_compass_v09.py | tail -3
PYTHONUTF8=1 python tests/test_crypto.py | tail -3
PYTHONUTF8=1 python tests/test_e2e_encryption.py | tail -3
PYTHONUTF8=1 python tests/test_stake_publisher.py | tail -3
PYTHONUTF8=1 python tests/test_sqlite_migration.py | tail -3
PYTHONUTF8=1 python tests/test_auth_v091.py | tail -3
python sdk/compass_crypto.py | tail -2
log "  ✓ pre-flight pass"
confirm "STEP 1 done · proceed to STEP 2 (backup)" || exit 0

# ============================================================
# STEP 2 · backup current cloud state
# ============================================================
log "STEP 2 · backup current cloud state"
ssh_remote "
  cd $REMOTE_DIR
  ts=\$(date +%Y%m%d_%H%M%S)
  mkdir -p backups
  if [ -f compass_http.py ]; then
    cp compass_http.py backups/compass_http.py.\$ts
  fi
  if [ -f tenants.json ]; then
    cp tenants.json backups/tenants.json.\$ts
  fi
  echo '  ✓ backup at backups/*.'\$ts
"
confirm "STEP 2 done · proceed to STEP 3 (sync files)" || exit 0

# ============================================================
# STEP 3 · sync v0.9 files (26 files)
# ============================================================
log "STEP 3 · sync v0.9 files"
NEW_FILES=(
    compass_http_v09.py
    openapi.yaml
    session_writer.py
    drift_history.py
    session_search.py
    daemon_anchor_loader.py
    daemon_anchor_apply.py
    anchors_platform_base.json
    compass_raid.py
    stake_publisher.py
    mcp_server.py
    stop_hook.py
    sdk/compass_client.py
    sdk/attach_memory.py
    sdk/a2a_adapter.py
    sdk/compass_crypto.py
    sdk/profile_aggregator.py
    tools/migrate_to_sqlite.py
    tools/migrate_from_v5.py
    tools/encrypt_legacy_obs.py
    Dockerfile
    docker-compose.yml
    .env.example
    scripts/compass.service
    scripts/compass-daemon.service
    scripts/audit_retention_cron.sh
    scripts/backup_compass.sh
    nginx_v10.conf
)
for f in "${NEW_FILES[@]}"; do
    if [ -f "$PLUGIN_DIR/$f" ]; then
        if $DRY_RUN; then
            echo "[dry] rsync $f"
        else
            rsync -avz -e "ssh -p $CLOUD_PORT" "$PLUGIN_DIR/$f" "$CLOUD:$REMOTE_DIR/$f"
        fi
    else
        echo "[warn] missing: $f"
    fi
done
log "  ✓ files synced"
confirm "STEP 3 done · proceed to STEP 4 (install deps)" || exit 0

# ============================================================
# STEP 4 · install Python deps
# ============================================================
log "STEP 4 · pip install fastapi · uvicorn · jose · cryptography"
ssh_remote "
  pip install --upgrade fastapi 'uvicorn[standard]' 'python-jose[cryptography]' cryptography 2>&1 | tail -3
"
confirm "STEP 4 done · proceed to STEP 5 (init schema)" || exit 0

# ============================================================
# STEP 5 · sqlite schema init
# ============================================================
log "STEP 5 · sqlite schema init"
ssh_remote "
  sudo mkdir -p /var/lib/compass
  sudo chown ubuntu:ubuntu /var/lib/compass
  cd $REMOTE_DIR
  python -c '
import sys; sys.path.insert(0, \".\")
from compass_http_v09 import init_db, init_audit_table
init_db()
init_audit_table()
print(\"  ✓ schema OK · users · agents · observations · audit_log\")
  '
"
confirm "STEP 5 done · proceed to STEP 6 (env file)" || exit 0

# ============================================================
# STEP 6 · /etc/default/compass with NAUTILUS_JWT_SECRET
# ============================================================
log "STEP 6 · /etc/default/compass setup"
ssh_remote "
  if [ ! -f /etc/default/compass ]; then
    sudo tee /etc/default/compass > /dev/null <<EOF
NAUTILUS_JWT_SECRET=\$(openssl rand -base64 32)
COMPASS_DB_PATH=/var/lib/compass/compass.db
COMPASS_REGION=cn-shanghai
COMPASS_DAEMON_HOST=127.0.0.1:9876
EOF
    sudo chmod 600 /etc/default/compass
    echo '  ✓ /etc/default/compass created · 600 perms'
  else
    echo '  · /etc/default/compass already exists · skip'
  fi
"
confirm "STEP 6 done · proceed to STEP 7 (systemd install)" || exit 0

# ============================================================
# STEP 7 · systemd unit · production service
# ============================================================
log "STEP 7 · systemd · production service"
ssh_remote "
  sudo cp $REMOTE_DIR/scripts/compass.service /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable compass.service
  sudo systemctl start compass.service
  sleep 5
  sudo systemctl status compass.service --no-pager | head -12
"
confirm "STEP 7 done · proceed to STEP 8 (verify)" || exit 0

# ============================================================
# STEP 8 · /healthz verification
# ============================================================
log "STEP 8 · /healthz verification"
ssh_remote "
  for i in 1 2 3 4 5; do
    if curl -fs http://127.0.0.1:8770/healthz > /tmp/h.json 2>/dev/null; then
      cat /tmp/h.json
      echo
      break
    fi
    echo '  · waiting (attempt '\$i')...'
    sleep 3
  done
"
confirm "STEP 8 done · proceed to STEP 9 (e2e test)" || exit 0

# ============================================================
# STEP 9 · 16-step e2e test
# ============================================================
log "STEP 9 · e2e test (16 steps)"
if $DRY_RUN; then
    echo "[dry] would run test_http_server_e2e.py against :8770"
else
    cd "$PLUGIN_DIR"
    COMPASS_BASE_URL=http://$CLOUD:8770 PYTHONUTF8=1 python tests/test_http_server_e2e.py 2>&1 | tail -25
fi
confirm "STEP 9 done · proceed to STEP 10 (Prometheus metrics)" || exit 0

# ============================================================
# STEP 10 · /metrics endpoint
# ============================================================
log "STEP 10 · Prometheus /metrics"
ssh_remote "
  curl -s http://127.0.0.1:8770/metrics | head -25
"
confirm "STEP 10 done · proceed to STEP 11 (audit retention cron)" || exit 0

# ============================================================
# STEP 11 · audit retention cron
# ============================================================
log "STEP 11 · install audit retention cron (daily 4 AM)"
ssh_remote "
  sudo mkdir -p /opt/compass
  sudo cp $REMOTE_DIR/scripts/audit_retention_cron.sh /opt/compass/
  sudo chmod +x /opt/compass/audit_retention_cron.sh
  ( sudo crontab -l 2>/dev/null | grep -v audit_retention_cron; echo '0 4 * * * /opt/compass/audit_retention_cron.sh' ) | sudo crontab -
  echo '  ✓ audit cron installed'
"
confirm "STEP 11 done · proceed to STEP 12 (backup cron)" || exit 0

# ============================================================
# STEP 12 · backup cron (daily 3 AM)
# ============================================================
log "STEP 12 · install daily backup cron (3 AM)"
ssh_remote "
  sudo cp $REMOTE_DIR/scripts/backup_compass.sh /opt/compass/
  sudo chmod +x /opt/compass/backup_compass.sh
  sudo mkdir -p /mnt/backups
  ( sudo crontab -l 2>/dev/null | grep -v backup_compass; echo '0 3 * * * /opt/compass/backup_compass.sh /mnt/backups' ) | sudo crontab -
  echo '  ✓ backup cron installed'
"
confirm "STEP 12 done · proceed to STEP 13 (nginx reminder)" || exit 0

# ============================================================
# STEP 13 · nginx routing reminder (manual · varies per setup)
# ============================================================
log "STEP 13 · nginx routing"
cat <<EOF

  ⚠️  ATTENTION · MANUAL STEP

  v0.7.2 still on :8765 · v0.9 now on :8770

  Pick A or B for :8770 routing:

  A. Subdomain (recommended for testing)
       cn-v9.compass.nautilus.social → 127.0.0.1:8770
       (let's encrypt cert needed)

  B. Path prefix
       compass.nautilus.social/v9/* → 127.0.0.1:8770/v1/*
       (same cert)

  Edit nginx config + reload:
       sudo systemctl reload nginx

  Then test from outside:
       curl https://cn-v9.compass.nautilus.social/healthz

EOF
confirm "STEP 13 reviewed · proceed to STEP 14 (final verify)" || exit 0

# ============================================================
# STEP 14 · final verify
# ============================================================
log "STEP 14 · final state report"
ssh_remote "
  echo === systemd status
  systemctl status compass.service --no-pager | head -8
  echo
  echo === healthz
  curl -s http://127.0.0.1:8770/healthz
  echo
  echo
  echo === metrics summary
  curl -s http://127.0.0.1:8770/metrics | grep -E '^compass_(users|observations|drift)' | head -5
  echo
  echo === sqlite size
  du -sh /var/lib/compass/compass.db 2>/dev/null
  echo
  echo === crontab
  sudo crontab -l 2>/dev/null
  echo
  echo === v0.7.2 still alive on :8765?
  curl -fs http://127.0.0.1:8765/healthz 2>/dev/null | head -1 || echo '  · v0.7.2 not running on :8765 (or different port)'
"

echo
log "✅ DEPLOY COMPLETE"
log "v0.9 on :8770 · v0.7.2 untouched · 1-month dual-track observation"
log ""
log "Next: nginx route :8770 (manual STEP 13) · then announce to users"
