#!/usr/bin/env bash
# =============================================================================
# Nautilus 一键部署脚本（本地运行）
# 用法:
#   bash scripts/deploy.sh              # 前端 + 后端
#   bash scripts/deploy.sh --frontend   # 只部署前端
#   bash scripts/deploy.sh --backend    # 只部署后端
#   bash scripts/deploy.sh --skip-build # 跳过 npm build（复用已有 dist/）
# 依赖: ssh alias "cloud" 已配置
# =============================================================================
set -euo pipefail

# ── 配置 ──────────────────────────────────────────────────────────────────────
SSH_HOST="cloud"
REMOTE_HOME="/home/ubuntu"
REMOTE_BACKEND="${REMOTE_HOME}/nautilus-mvp/phase3/backend"
REMOTE_WEB="/var/www/nautilus/current"
BACKEND_SERVICE="nautilus-backend"
FRONTEND_DIR="phase3/website"
BACKEND_DIR="phase3/backend"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# ── 参数解析 ──────────────────────────────────────────────────────────────────
DO_FRONTEND=true
DO_BACKEND=true
SKIP_BUILD=false

for arg in "$@"; do
  case "$arg" in
    --frontend)   DO_BACKEND=false ;;
    --backend)    DO_FRONTEND=false ;;
    --skip-build) SKIP_BUILD=true ;;
    --help|-h)
      sed -n '2,9p' "$0"
      exit 0
      ;;
  esac
done

# ── 颜色 ──────────────────────────────────────────────────────────────────────
GRN='\033[0;32m'; YLW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()   { echo -e "${GRN}[OK]${NC}  $*"; }
info() { echo -e "${YLW}[..]${NC}  $*"; }
fail() { echo -e "${RED}[!!]${NC}  $*"; exit 1; }

echo "============================================"
echo " Nautilus Deploy  $(date '+%Y-%m-%d %H:%M:%S')"
echo " frontend=${DO_FRONTEND}  backend=${DO_BACKEND}  skip-build=${SKIP_BUILD}"
echo "============================================"

# ── 前端 ──────────────────────────────────────────────────────────────────────
if $DO_FRONTEND; then
  info "Step 1/3  Frontend build"
  cd "${PROJECT_ROOT}/${FRONTEND_DIR}"

  if ! $SKIP_BUILD; then
    npm run build 2>&1 | tail -4
    ok "Build complete"
  else
    info "Skipping build (--skip-build)"
  fi

  [[ -d dist ]] || fail "dist/ not found — run without --skip-build"

  info "Step 2/3  Upload dist → server"
  # 先上传到临时目录再原子性替换，避免 partial state
  ssh "$SSH_HOST" "mkdir -p ${REMOTE_HOME}/nautilus-dist-new"
  scp -q -r dist/. "${SSH_HOST}:${REMOTE_HOME}/nautilus-dist-new/"
  ok "Upload complete"

  info "Step 3/3  Copy to web root"
  ssh "$SSH_HOST" "sudo cp -r ${REMOTE_HOME}/nautilus-dist-new/. ${REMOTE_WEB}/"
  ok "Web root updated"

  # 验证 index.html hash 一致
  LOCAL_HASH=$(md5sum "${PROJECT_ROOT}/${FRONTEND_DIR}/dist/index.html" | cut -d' ' -f1)
  REMOTE_HASH=$(ssh "$SSH_HOST" "md5sum ${REMOTE_WEB}/index.html 2>/dev/null | cut -d' ' -f1")
  [[ "$LOCAL_HASH" == "$REMOTE_HASH" ]] && ok "index.html hash verified" \
    || fail "index.html hash mismatch — local=${LOCAL_HASH} remote=${REMOTE_HASH}"

  cd "${PROJECT_ROOT}"
fi

# ── 后端 ──────────────────────────────────────────────────────────────────────
if $DO_BACKEND; then
  info "Backend  Detect changed Python files (vs HEAD~1)"
  cd "${PROJECT_ROOT}"

  # 找到自上次提交以来变动的 backend 文件
  CHANGED=$(git diff --name-only HEAD~1 HEAD -- "${BACKEND_DIR}/" 2>/dev/null || true)

  if [[ -z "$CHANGED" ]]; then
    info "No backend files changed since last commit — checking working tree"
    CHANGED=$(git diff --name-only HEAD -- "${BACKEND_DIR}/" 2>/dev/null || true)
  fi

  if [[ -z "$CHANGED" ]]; then
    info "No backend changes detected, skipping file upload (will still restart)"
  else
    echo "$CHANGED" | while read -r f; do
      [[ -f "$f" ]] || continue
      RELPATH="${f#${BACKEND_DIR}/}"
      DESTDIR="${REMOTE_BACKEND}/$(dirname "$RELPATH")"
      info "  upload: $f"
      ssh "$SSH_HOST" "mkdir -p ${DESTDIR}"
      scp -q "$f" "${SSH_HOST}:${DESTDIR}/"
      ssh "$SSH_HOST" "sudo cp ${REMOTE_HOME}/$(basename "$f") ${DESTDIR}/ 2>/dev/null || true"
    done
    ok "Backend files uploaded"
  fi

  info "Backend  Restart service"
  ssh "$SSH_HOST" "sudo systemctl restart ${BACKEND_SERVICE}"
  sleep 4

  STATUS=$(ssh "$SSH_HOST" "systemctl is-active ${BACKEND_SERVICE}" 2>/dev/null || echo "unknown")
  [[ "$STATUS" == "active" ]] && ok "Service ${BACKEND_SERVICE} is active" \
    || fail "Service not active (status=${STATUS}). Check: ssh cloud 'sudo journalctl -u ${BACKEND_SERVICE} -n 30'"
fi

# ── 健康检查 ──────────────────────────────────────────────────────────────────
info "Health check  /api/stats"
STATS=$(ssh "$SSH_HOST" "curl -s http://localhost:8000/api/stats" 2>/dev/null)
TASKS=$(echo "$STATS" | python3 -c "import json,sys; print(json.load(sys.stdin).get('total_tasks','?'))" 2>/dev/null || echo "?")
AGENTS=$(echo "$STATS" | python3 -c "import json,sys; print(json.load(sys.stdin).get('active_agents','?'))" 2>/dev/null || echo "?")

if [[ "$TASKS" != "?" ]]; then
  ok "API healthy — tasks=${TASKS} agents=${AGENTS}"
else
  fail "API health check failed: ${STATS}"
fi

echo ""
echo "============================================"
echo -e " ${GRN}Deploy complete!${NC}"
echo " Commit: $(git log --oneline -1)"
echo " Site:   https://www.nautilus.social"
echo "============================================"
