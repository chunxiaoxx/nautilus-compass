#!/bin/bash
# safe_deploy.sh v0.1 · md5-verify-based atomic file deploy with optional service restart
#
# Born from 5/22-5/23 12h+ debug · root cause was cp daemon.py Permission denied
# silent fail · systemctl restart showed active running · handoff marked "trio
# shipped" · production was running old binary all along.
#
# This script makes "deploy assumed shipped" impossible: any failure exits
# non-zero · restart only triggers after md5+verify-patch pass.
#
# See SPEC: memory/spec_safe_deploy_sh_v01.md

set -e
set -o pipefail

# === defaults ===
OWNER="ubuntu"
GROUP="ubuntu"
MODE=""
RESTART_SVC=""
VERIFY_PATCH=""
SKIP_SYNTAX=false
DRY_RUN=false
LOG_FILE="${SAFE_DEPLOY_LOG:-/var/log/safe-deploy.log}"

usage() {
  cat <<EOF
usage: safe_deploy.sh SOURCE TARGET [OPTIONS]

required:
  SOURCE                  source file path
  TARGET                  target absolute path

options:
  --restart SERVICE       restart systemd service after deploy
  --verify-patch TEXT     grep TEXT in deployed file · fail if not found
  --owner USER:GROUP      chown target (default ubuntu:ubuntu)
  --mode MODE             chmod octal (default 0755 for .py/.sh · 0644 others)
  --skip-syntax-check     skip py_compile for .py files
  --dry-run               print actions · don't execute
  -h | --help             this help

exit codes:
  0 = success
  1 = pre-deploy fail OR deploy fail with auto-rollback successful
  2 = post-deploy service fail · needs manual rollback
EOF
}

# === parse args ===
if [ $# -lt 2 ]; then usage; exit 1; fi
SOURCE="$1"
TARGET="$2"
shift 2
while [ $# -gt 0 ]; do
  case "$1" in
    --restart) RESTART_SVC="$2"; shift 2 ;;
    --verify-patch) VERIFY_PATCH="$2"; shift 2 ;;
    --owner) OWNER="${2%%:*}"; GROUP="${2##*:}"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --skip-syntax-check) SKIP_SYNTAX=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "unknown opt: $1"; usage; exit 1 ;;
  esac
done

if [ -z "$MODE" ]; then
  case "$SOURCE" in
    *.py|*.sh) MODE="0755" ;;
    *) MODE="0644" ;;
  esac
fi

log() {
  TS=$(date '+%Y-%m-%d %H:%M:%S')
  echo "[$TS] $*"
  if $DRY_RUN; then return; fi
  if [ -w "$(dirname "$LOG_FILE")" ] 2>/dev/null; then
    echo "[$TS] $*" >> "$LOG_FILE" 2>/dev/null || true
  else
    echo "[$TS] $*" | sudo tee -a "$LOG_FILE" >/dev/null 2>&1 || true
  fi
}

# === step 1 · pre-flight ===
log "STEP 1 · pre-flight check"
[ -f "$SOURCE" ] && [ -r "$SOURCE" ] || { log "FAIL · source not readable: $SOURCE"; exit 1; }
[ -d "$(dirname "$TARGET")" ] || { log "FAIL · target dir missing: $(dirname "$TARGET")"; exit 1; }

case "$SOURCE" in
  *.py)
    if ! $SKIP_SYNTAX; then
      python3 -m py_compile "$SOURCE" || { log "FAIL · py_compile"; exit 1; }
      log "  py_compile OK"
    fi ;;
esac

# === step 2 · md5 source ===
SRC_MD5=$(md5sum "$SOURCE" | awk '{print $1}')
log "STEP 2 · SRC_MD5=$SRC_MD5"

# === step 3 · backup target if exists ===
BACKUP=""
if [ -f "$TARGET" ]; then
  BACKUP="${TARGET}.bak-pre-deploy-$(date +%Y%m%d-%H%M%S)"
  if $DRY_RUN; then
    log "STEP 3 · would backup → $BACKUP"
  else
    sudo cp -p "$TARGET" "$BACKUP" || { log "FAIL · backup"; exit 1; }
    log "STEP 3 · backup → $BACKUP"
  fi
else
  log "STEP 3 · no existing target · skip backup"
fi

rollback() {
  [ -z "$BACKUP" ] && return
  [ ! -f "$BACKUP" ] && return
  log "ROLLBACK · restoring $BACKUP → $TARGET"
  sudo install -o "$OWNER" -g "$GROUP" -m "$MODE" "$BACKUP" "$TARGET" 2>/dev/null || \
    sudo cp -p "$BACKUP" "$TARGET"
}

# === step 4 · atomic install ===
if $DRY_RUN; then
  log "STEP 4 · would install -o $OWNER -g $GROUP -m $MODE $SOURCE → $TARGET"
else
  sudo install -o "$OWNER" -g "$GROUP" -m "$MODE" "$SOURCE" "$TARGET" || {
    log "FAIL · install · TARGET unchanged"; exit 1;
  }
  log "STEP 4 · install OK · -o $OWNER -g $GROUP -m $MODE"
fi

# === step 5 · md5 target ===
if $DRY_RUN; then
  log "STEP 5 · would md5sum $TARGET (skipped in dry-run)"
else
  DST_MD5=$(md5sum "$TARGET" | awk '{print $1}')
  log "STEP 5 · DST_MD5=$DST_MD5"
fi

# === step 6 · md5 verify ===
if ! $DRY_RUN; then
  if [ "$SRC_MD5" != "$DST_MD5" ]; then
    log "FAIL · md5 mismatch · src=$SRC_MD5 dst=$DST_MD5"
    rollback; exit 1
  fi
  log "STEP 6 · md5 match ✓"
fi

# === step 7 · verify patch text ===
if [ -n "$VERIFY_PATCH" ]; then
  if $DRY_RUN; then
    log "STEP 7 · would grep '$VERIFY_PATCH' in $TARGET"
  else
    grep -q "$VERIFY_PATCH" "$TARGET" || {
      log "FAIL · verify-patch '$VERIFY_PATCH' not found in deployed file"
      rollback; exit 1;
    }
    log "STEP 7 · verify-patch found ✓"
  fi
fi

# === step 8 · restart service ===
if [ -n "$RESTART_SVC" ]; then
  if $DRY_RUN; then
    log "STEP 8 · would restart $RESTART_SVC"
  else
    sudo systemctl restart "$RESTART_SVC" || { log "FAIL · restart"; exit 2; }
    sleep 5
    systemctl is-active "$RESTART_SVC" >/dev/null || {
      log "FAIL · $RESTART_SVC not active post-restart · NOT auto-rolled-back · investigate"
      exit 2
    }
    log "STEP 8 · service active ✓"
  fi
fi

# === step 9 · service ready signal ===
if [ -n "$RESTART_SVC" ] && ! $DRY_RUN; then
  LOG_OUT=$(sudo journalctl -u "$RESTART_SVC" --since '1 minute ago' --no-pager 2>/dev/null || true)
  if echo "$LOG_OUT" | grep -qE 'ready|listening|started|active|loaded'; then
    log "STEP 9 · service ready signal found ✓"
  else
    log "WARN · service active but no ready signal · suspect slow start · check logs manually"
  fi
fi

# === step 10 · success log ===
SUMMARY="SUCCESS | $SOURCE → $TARGET | md5=$SRC_MD5"
[ -n "$RESTART_SVC" ] && SUMMARY="$SUMMARY | service=$RESTART_SVC"
[ -n "$VERIFY_PATCH" ] && SUMMARY="$SUMMARY | patch=$VERIFY_PATCH"
log "STEP 10 · $SUMMARY"

# === step 11 · exit 0 ===
$DRY_RUN && log "DRY-RUN done · 0 state changed"
exit 0
