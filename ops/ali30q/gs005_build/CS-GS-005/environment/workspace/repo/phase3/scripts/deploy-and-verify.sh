#!/bin/bash
# Nautilus deployment script with health verification and retry logic
# Usage: bash scripts/deploy-and-verify.sh
set -e

SERVER="cloud"
BACKEND_DIR="~/nautilus-mvp/phase3/backend"
TIMEOUT=15
MAX_RETRIES=3
RETRY_DELAY=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()    { echo -e "[INFO] $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

# Retry wrapper: retry_cmd <max_retries> <delay> <description> <command...>
retry_cmd() {
    local max_retries=$1
    local delay=$2
    local desc=$3
    shift 3

    local attempt=1
    while [ $attempt -le $max_retries ]; do
        if "$@" 2>&1; then
            return 0
        fi
        if [ $attempt -lt $max_retries ]; then
            log_warn "$desc failed (attempt $attempt/$max_retries), retrying in ${delay}s..."
            sleep $delay
        fi
        attempt=$((attempt + 1))
    done

    log_error "$desc failed after $max_retries attempts"
    return 1
}

# File transfer: prefer rsync, fall back to scp
transfer_files() {
    local src=$1
    local dest=$2

    if command -v rsync &>/dev/null; then
        log_info "Using rsync for file transfer..."
        rsync -avz --checksum --timeout=30 -e ssh "$src" "$SERVER:$dest"
    else
        log_info "Using scp for file transfer (rsync not available)..."
        scp -r "$src" "$SERVER:$dest"
    fi
}

# Verify file integrity after transfer
verify_transfer() {
    local local_path=$1
    local remote_path=$2

    if [ -d "$local_path" ]; then
        local local_count=$(find "$local_path" -type f | wc -l)
        local remote_count=$(ssh "$SERVER" "find $remote_path -type f 2>/dev/null | wc -l")
        if [ "$local_count" != "$remote_count" ]; then
            log_error "File count mismatch: local=$local_count remote=$remote_count"
            return 1
        fi
        log_success "File count verified: $local_count files"
    else
        local local_size=$(stat -f%z "$local_path" 2>/dev/null || stat -c%s "$local_path" 2>/dev/null || echo "0")
        local remote_size=$(ssh "$SERVER" "stat -c%s $remote_path 2>/dev/null || echo 0")
        if [ "$local_size" != "$remote_size" ]; then
            log_error "File size mismatch: local=${local_size}B remote=${remote_size}B"
            return 1
        fi
        log_success "File size verified: ${local_size}B"
    fi
    return 0
}

echo "=== Nautilus Deployment ==="
echo ""

# 0. Resolve branch (fail-closed: no branch, no deploy)
BRANCH="${DEPLOY_BRANCH:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null)}"
if [ -z "$BRANCH" ] || [ "$BRANCH" = "HEAD" ]; then
    log_error "cannot resolve branch to deploy (detached HEAD?); set DEPLOY_BRANCH explicitly"
    exit 1
fi
LOCAL_SHA=$(git rev-parse HEAD)
log_info "deploying branch=$BRANCH sha=${LOCAL_SHA:0:12}"

# 1. Push to GitHub origin (canonical chain; fail-closed — 9/12 定谳修复:不再写死 master、不再吞错)
echo "[1/6] Pushing to origin/$BRANCH..."
retry_cmd $MAX_RETRIES $RETRY_DELAY "git push" git push origin "$BRANCH" || {
    log_error "push to origin failed — aborting (do NOT deploy stale code; fallback: scp + cloud-side push)"
    exit 1
}

# 2. Update server working directory to exactly the pushed commit (sha-verified — 9/12 定谳修复:真拉+比对,杜绝空拉假成功)
echo ""
echo "[2/6] Updating server working directory..."
retry_cmd $MAX_RETRIES $RETRY_DELAY "server git update" \
    ssh $SERVER "cd ~/nautilus-mvp && git checkout -- . && git fetch origin $BRANCH && git reset --hard FETCH_HEAD" || {
    log_error "server update failed"
    exit 1
}
REMOTE_SHA=$(ssh $SERVER "cd ~/nautilus-mvp && git rev-parse HEAD")
if [ "$REMOTE_SHA" != "$LOCAL_SHA" ]; then
    log_error "sha mismatch after update: local=$LOCAL_SHA remote=$REMOTE_SHA — server is NOT on the pushed commit"
    exit 1
fi
log_success "server at ${REMOTE_SHA:0:12} (matches local)"

# 3. Sync agent-engine to backend/agent_engine (agent-engine/ = in-repo source of truth since 189310ef0)
echo ""
echo "[3/6] Syncing agent-engine to backend/agent_engine..."
retry_cmd $MAX_RETRIES $RETRY_DELAY "agent-engine sync" \
    ssh $SERVER "cd ~/nautilus-mvp && bash phase3/scripts/sync-agent-engine.sh" || {
    log_error "agent-engine sync failed"
    exit 1
}

# 4. Restart backend + verify active
echo ""
echo "[4/6] Restarting backend..."
ssh $SERVER "sudo systemctl restart nautilus-backend"
sleep 2
ACTIVE=$(ssh $SERVER "systemctl is-active nautilus-backend")
if [ "$ACTIVE" != "active" ]; then
    log_error "nautilus-backend not active after restart (state: $ACTIVE)"
    exit 1
fi
log_success "nautilus-backend active"

# 5. Wait and verify
echo ""
echo "[5/6] Waiting ${TIMEOUT}s for startup..."
sleep $TIMEOUT

echo ""
echo "[6/6] Running health checks..."

HEALTH_OK=true

# Check /api/stats
STATS=$(ssh $SERVER "curl -s -w '\n%{http_code}' http://localhost:8000/api/stats" 2>/dev/null)
STATS_CODE=$(echo "$STATS" | tail -1)
STATS_BODY=$(echo "$STATS" | sed '$d')

if [ "$STATS_CODE" = "200" ]; then
    log_success "/api/stats: OK"
else
    log_error "/api/stats: FAILED (HTTP ${STATS_CODE})"
    HEALTH_OK=false
fi

# Check /health
HEALTH=$(ssh $SERVER "curl -s -w '\n%{http_code}' http://localhost:8000/health" 2>/dev/null)
HEALTH_CODE=$(echo "$HEALTH" | tail -1)
HEALTH_BODY=$(echo "$HEALTH" | sed '$d')

if [ "$HEALTH_CODE" = "200" ]; then
    STATUS=$(echo "$HEALTH_BODY" | python3 -c "import sys,json;print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "unknown")
    log_success "/health: OK (status: ${STATUS})"
else
    log_warn "/health: HTTP ${HEALTH_CODE} (non-critical)"
fi

# Check survival API
SURV_CODE=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/survival/statistics" 2>/dev/null)
if [ "$SURV_CODE" = "200" ]; then
    log_success "/api/survival/statistics: OK"
else
    log_warn "/api/survival/statistics: HTTP ${SURV_CODE}"
fi

# Check academic API
ACAD_CODE=$(ssh $SERVER "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/api/academic/" 2>/dev/null)
if [ "$ACAD_CODE" = "200" ]; then
    log_success "/api/academic/: OK"
else
    log_warn "/api/academic/: HTTP ${ACAD_CODE}"
fi

echo ""
if [ "$HEALTH_OK" = true ]; then
    log_success "=== Deployment Complete ==="
else
    log_error "=== Deployment had issues - check logs ==="
    echo ""
    echo "Recent backend logs:"
    ssh $SERVER "journalctl -u nautilus-backend -n 15 --no-pager" 2>/dev/null
    exit 1
fi
