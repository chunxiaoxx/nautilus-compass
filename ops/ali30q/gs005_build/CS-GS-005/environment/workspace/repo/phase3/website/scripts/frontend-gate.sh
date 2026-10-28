#!/usr/bin/env bash
#
# 前端验证门 (P0) — frontend-gate.sh
# 任何前端改动部署前必跑。退出码 0 = 可安全部署。
#
# 设计:docs/plans/2026-06-07-frontend-maintenance-agentification-design.md
# 硬门(任一红 → exit 1):build / dist静态检查 / 生产端点 smoke
# baseline 门(超基线=新回归才红):vitest / lint —— 预存债务不挡,新增回归才拦
#   预存基线(2026-06-07):vitest 36 失败(全在陈旧 Login/Register.test·测已删的email-UI)
#                          lint 117 errors(no-explicit-any 为主)
#   降基线:修了陈旧测试/lint 后,把下面 BASELINE_* 调低,门会守住不回弹
BASELINE_VITEST_FAILS=36
BASELINE_LINT_ERRORS=117
#
# 用法:
#   bash scripts/frontend-gate.sh                 # smoke 打生产 www.nautilus.social
#   SMOKE_BASE=http://host.docker.internal:4318 bash scripts/frontend-gate.sh   # 打本地预览
#   SKIP_SMOKE=1 bash scripts/frontend-gate.sh    # 跳网络 smoke(离线只跑 build/test/dist)
#
set -uo pipefail
cd "$(dirname "$0")/.."   # phase3/website

GREEN='\033[0;32m'; RED='\033[0;31m'; YEL='\033[1;33m'; NC='\033[0m'
PASS=0; FAIL=0
ok()   { echo -e "${GREEN}✓ PASS${NC} $1"; PASS=$((PASS+1)); }
bad()  { echo -e "${RED}✗ FAIL${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YEL}! WARN${NC} $1"; }
hr()   { echo "────────────────────────────────────────"; }

SMOKE_BASE="${SMOKE_BASE:-https://www.nautilus.social}"

echo "前端验证门 · $(node -v 2>/dev/null) · smoke→${SMOKE_BASE}"
hr

# 1) BUILD (tsc + vite) ─ 硬门
echo "[1/6] build (tsc && vite build)…"
if npm run build >/tmp/fg_build.log 2>&1; then
  ok "build green"
else
  bad "build 失败 → tail /tmp/fg_build.log"; tail -8 /tmp/fg_build.log
fi

# 2) VITEST ─ baseline 门(失败数 > 基线 = 新回归才红)
echo "[2/6] vitest run (baseline ≤ ${BASELINE_VITEST_FAILS})…"
npx vitest run >/tmp/fg_test.log 2>&1
# strip ANSI 后只读 "Tests" 汇总行(避免抓 per-file 计数 / 色码干扰)
TLINE=$(sed 's/\x1b\[[0-9;]*m//g' /tmp/fg_test.log | grep -E "Tests[[:space:]]+[0-9]" | tail -1)
VF=$(echo "$TLINE" | grep -oE "[0-9]+ failed" | grep -oE "[0-9]+"); VF="${VF:-0}"
VP=$(echo "$TLINE" | grep -oE "[0-9]+ passed" | grep -oE "[0-9]+"); VP="${VP:-0}"
if [ "$VF" -le "$BASELINE_VITEST_FAILS" ]; then
  ok "vitest ${VP} passed / ${VF} failed(≤基线${BASELINE_VITEST_FAILS}·预存陈旧测试)"
  [ "$VF" -lt "$BASELINE_VITEST_FAILS" ] && warn "失败降到 ${VF} < 基线 ${BASELINE_VITEST_FAILS} · 可调低 BASELINE_VITEST_FAILS"
else
  bad "vitest ${VF} failed > 基线 ${BASELINE_VITEST_FAILS} = 新增回归! → tail /tmp/fg_test.log"; tail -12 /tmp/fg_test.log
fi

# 3) DIST 静态检查:无硬编码 IP base(mixed-content 拦截点)─ 硬门
echo "[3/6] dist 无硬编码 http://IP base…"
if [ -d dist/assets ]; then
  N=$(grep -roE "43\.160\.239\.61:8000" dist/assets/*.js 2>/dev/null | wc -l | tr -d ' ')
  [ "$N" = "0" ] && ok "无 43.160.239.61:8000 残留" || bad "dist 含 $N 处硬编码 IP base(HTTPS mixed-content 会阻断)"
else
  bad "dist/ 不存在(build 未成功?)"
fi

# 4) DIST 静态检查:无双 /api(双api → 404 拦截点)─ 硬门
echo "[4/6] dist 无双 /api/api…"
if [ -d dist/assets ]; then
  N=$(grep -roE "nautilus\.social/api/api" dist/assets/*.js 2>/dev/null | wc -l | tr -d ' ')
  [ "$N" = "0" ] && ok "无双 /api/api 残留" || bad "dist 含 $N 处双 /api(VITE_API_URL 尾多 /api?)"
else
  bad "dist/ 不存在"
fi

# 5) 端点 smoke:关键端点路径对 ─ 硬门(可 SKIP_SMOKE=1 跳)
echo "[5/6] 生产端点 smoke (${SMOKE_BASE})…"
if [ "${SKIP_SMOKE:-0}" = "1" ]; then
  warn "SKIP_SMOKE=1 · 跳过网络 smoke"
else
  code_stats=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${SMOKE_BASE}/api/stats" 2>/dev/null)
  [ "$code_stats" = "200" ] && ok "/api/stats → 200" || bad "/api/stats → ${code_stats}(应 200)"

  code_me=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${SMOKE_BASE}/api/auth/me" 2>/dev/null)
  case "$code_me" in
    200|401|403) ok "/api/auth/me → ${code_me}(端点存在)";;
    *) bad "/api/auth/me → ${code_me}(应 401/200·404=路由错/缺/api)";;
  esac

  # 双 /api 必须 404(证单 /api 才是对的)
  code_dbl=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "${SMOKE_BASE}/api/api/stats" 2>/dev/null)
  [ "$code_dbl" != "200" ] && ok "/api/api/stats → ${code_dbl}(双 /api 正确地 404)" || bad "/api/api/stats → 200(路由异常)"
fi

# 6) LINT ─ baseline 门(errors > 基线 = 新回归才红)
echo "[6/6] lint (baseline ≤ ${BASELINE_LINT_ERRORS} errors)…"
LINT_OUT=$(npm run lint 2>&1 || true)
LE=$(echo "$LINT_OUT" | grep -oE "[0-9]+ errors?" | grep -oE "[0-9]+" | tail -1); LE="${LE:-0}"
if [ "$LE" -le "$BASELINE_LINT_ERRORS" ]; then
  ok "eslint ${LE} errors(≤基线${BASELINE_LINT_ERRORS}·预存 no-explicit-any)"
  [ "$LE" -lt "$BASELINE_LINT_ERRORS" ] && warn "errors 降到 ${LE} · 可调低 BASELINE_LINT_ERRORS"
else
  bad "eslint ${LE} errors > 基线 ${BASELINE_LINT_ERRORS} = 新增 lint 回归"
fi

hr
echo -e "硬门:${GREEN}${PASS} pass${NC} / ${RED}${FAIL} fail${NC}"
if [ "$FAIL" -eq 0 ]; then
  echo -e "${GREEN}✓ GATE GREEN — 可安全部署${NC}"; exit 0
else
  echo -e "${RED}✗ GATE RED — 禁止部署,先修上面 FAIL${NC}"; exit 1
fi
