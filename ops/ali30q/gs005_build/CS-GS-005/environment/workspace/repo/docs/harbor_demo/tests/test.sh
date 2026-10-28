#!/usr/bin/env bash
set -euo pipefail

# ── 将测试文件复制到 workspace（按需） ──
# cp /tests/<test_file> /workspace/<target_path>/

cd /workspace

# ── 编译检查（可选，按语言调整） ──
# if ! go build ./... 2>&1; then
#   echo "COMPILE ERROR"
#   echo 0 > /logs/verifier/reward.txt
#   exit 0
# fi

# ── 运行测试 ──
# if go test -v -race -count=1 -timeout 120s ./... 2>&1; then
#   echo 1 > /logs/verifier/reward.txt
# else
#   echo 0 > /logs/verifier/reward.txt
# fi

# ── 收集 agent.patch（agent 的代码改动） ──
(
  set -u
  _repo=""
  for _d in /workspace /testbed /app /apollo "$PWD"; do
    [ -d "$_d" ] || continue
    if git -c safe.directory='*' -C "$_d" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
      _repo="$_d"; break
    fi
  done
  if [ -n "$_repo" ]; then
    mkdir -p /logs/artifacts
    git -c safe.directory='*' -C "$_repo" add -A >/dev/null 2>&1 || true
    git -c safe.directory='*' -C "$_repo" diff --cached --binary HEAD > /logs/artifacts/agent.patch 2>/dev/null || true
    echo "agent.patch: $(wc -c < /logs/artifacts/agent.patch 2>/dev/null) bytes" >&2
  else
    echo "WARN: no git repo found, skip agent.patch" >&2
  fi
) || true

# ── 占位：当前默认 reward=0，请替换为实际测试逻辑 ──
echo 0 > /logs/verifier/reward.txt
