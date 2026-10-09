#!/usr/bin/env bash
# check_env.sh · 会话环境探针(S3)——哪台机/哪个仓/哪个分支/凭据/服务,一行摘要防串环境三坑
# 用法: bash tools/check_env.sh
set -u
echo "== host: $(hostname) | $(date '+%m-%d %H:%M')"
echo "== user: $(whoami) | cwd: $(pwd)"

# git 仓与分支
if git rev-parse --git-dir >/dev/null 2>&1; then
  echo "== repo: $(git remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]||;s|\.git$||') | branch: $(git branch --show-current) | HEAD: $(git log --oneline -1 2>/dev/null | head -c 60)"
  DIRTY=$(git status --porcelain 2>/dev/null | wc -l)
  echo "== dirty files: $DIRTY"
else
  echo "== repo: (not a git repo)"
fi

# 凭据与 daemon token(只报存在性,不显示内容)
for f in ~/.claude/.cache/compass_daemon_token ~/.claude/.cache/a100_env; do
  [ -s "$f" ] && echo "== cred: $f ($(wc -c < "$f")B)"
done

# 本地 daemon(若有)
python - <<'PYE' 2>/dev/null
import socket
try:
    s = socket.create_connection(("127.0.0.1", 9876), 3)
    s.sendall(b'{"action":"ping"}\n')
    print("== daemon 9876:", s.recv(40).decode()[:30])
except Exception as e:
    print("== daemon 9876: DOWN", e)
PYE
echo "== done"

# --remote 可选:探 cloud/A100 两对端(默认只探本地)
if [ "${1:-}" = "--remote" ]; then
  echo "== cloud (nautilus.social):"
  ssh -o ConnectTimeout=10 cloud 'hostname; cd /home/ubuntu/nautilus-compass 2>/dev/null && git log --oneline -1 | head -c 60; echo; systemctl is-active compass-bge-daemon compass-judge-status compass-a100-tunnel 2>/dev/null | paste -sd/ -' 2>/dev/null || echo "  UNREACHABLE"
  echo "== A100 (embed+judge):"
  A100_HOST=$(grep A100_HOST ~/.claude/.cache/a100_env 2>/dev/null | cut -d= -f2)
  A100_PORT=$(grep A100_PORT ~/.claude/.cache/a100_env 2>/dev/null | cut -d= -f2)
  ssh -o ConnectTimeout=10 -p "${A100_PORT:-23236}" root@"${A100_HOST:-223.109.239.30}" 'hostname; curl -s -m 5 http://127.0.0.1:8400/health | head -c 60; echo; curl -s -m 8 http://127.0.0.1:19988/health | head -c 80' 2>/dev/null || echo "  UNREACHABLE"
fi
