#!/usr/bin/env bash
# =============================================================================
# FDE T1 专家计划介绍页（单页站）部署脚本
# 使用方法:
#   bash scripts/deploy-phase3-expert-ops.sh [--skip-verify]
# 依赖:
#   - ssh 别名 cloud 可达
#   - 已具备 /var/www/fde.nautilus.social/ 写权限（通过 sudo）
# =============================================================================
set -euo pipefail

SSH_HOST="cloud"
SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=15)
REMOTE_ROOT="/var/www/fde.nautilus.social/t1-expert"
REMOTE_TMP="/tmp/t1_expert_publish_$(date +%s)"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCAL_DIR="${PROJECT_ROOT}/docs/business/phase3_expert_operations"
LOCAL_INDEX="${LOCAL_DIR}/phase3_expert_ops_single_page.html"

DRY_SKIP_VERIFY=false
for arg in "$@"; do
  case "$arg" in
    --skip-verify) DRY_SKIP_VERIFY=true ;;
    -h|--help)
      sed -n '1,80p' "$0"
      exit 0
      ;;
    *) ;;
  esac
done

log() { echo "[t1-expert] $*"; }
fail() { echo "[phase3-ops][FAIL] $*" >&2; exit 1; }

[[ -f "$LOCAL_INDEX" ]] || fail "Missing file: $LOCAL_INDEX"

log "上传会话目录：$REMOTE_TMP"
ssh "${SSH_OPTS[@]}" "$SSH_HOST" "mkdir -p ${REMOTE_TMP}"
scp "${SSH_OPTS[@]}" "$LOCAL_INDEX" "$SSH_HOST:${REMOTE_TMP}/index.html"

log "原子替换到 ${REMOTE_ROOT}"
ssh "${SSH_OPTS[@]}" "$SSH_HOST" "sudo mkdir -p ${REMOTE_ROOT}; sudo install -m 0644 ${REMOTE_TMP}/index.html ${REMOTE_ROOT}/index.html.new; sudo chown www-data:www-data ${REMOTE_ROOT}/index.html.new; sudo mv -f ${REMOTE_ROOT}/index.html.new ${REMOTE_ROOT}/index.html; rm -rf ${REMOTE_TMP}"

if ! $DRY_SKIP_VERIFY; then
  log "新路径验证"
  local_sha=$(sha256sum "$LOCAL_INDEX" | awk '{print $1}')
  remote_sha=$(ssh "${SSH_OPTS[@]}" "$SSH_HOST" "sudo sha256sum ${REMOTE_ROOT}/index.html" | awk '{print $1}')
  [[ "$local_sha" == "$remote_sha" ]] || fail "远端 index.html SHA256 与本地源不一致"

  public_html=$(curl -skfL "https://fde.nautilus.social/t1-expert/") || fail "公开页面无法读取"
  grep -Fq "三期垂直领域专家计划" <<<"$public_html" || fail "公开页面缺少 T1 唯一页面标记"
  grep -Fq "填写三期专家报名表" <<<"$public_html" || fail "公开页面缺少正式报名入口"
  grep -Fq "本科及以上学历" <<<"$public_html" || fail "公开页面缺少招募资格说明"
fi

log "部署与验证完成"
