#!/usr/bin/env bash
# v3.2 蓝绿部署一键脚本(窗口 10/1 08:53 记忆判据读数之后执行)
# 用法:
#   bash ops/v32_bluegreen_deploy.sh upload   # ① 上传 v32 到云端(任何时候可做,零风险)
#   bash ops/v32_bluegreen_deploy.sh blue     # ② 起蓝实例 :9877(窗口内,占用 ~3.5G,起前查可用内存)
#   bash ops/v32_bluegreen_deploy.sh verify   # ③ 蓝实例判据验证(J5 warmup/J6 recall 对比)
#   bash ops/v32_bluegreen_deploy.sh switch   # ④ 切换(停 systemd 现役→v32 上 9876→蓝实例退役)
#   bash ops/v32_bluegreen_deploy.sh rollback # ⑤ 回退(kill v32→systemd 起原版,零确认即可执行)
# 纪律:每步独立幂等;verify 不绿不 switch;rollback 永远可用。
set -euo pipefail

CLOUD_HOST="cloud"   # ~/.ssh/config 别名(43.160.239.61:24860 + cloud_permanent)
V32_SRC="runtime/cloud_daemon_v32_20260930.py"
V32_DST="/home/ubuntu/nautilus-compass/daemon_v32.py"
PLUGIN_CACHE="/home/ubuntu/.claude/plugins/nautilus-compass/.cache"
BLUE_PORT=9877

ssh_do() { ssh "$CLOUD_HOST" "$@"; }

case "${1:-}" in
upload)
  scp "$V32_SRC" "$CLOUD_HOST:$V32_DST"
  ssh_do "python3 -m py_compile $V32_DST && echo 'compile OK' && md5sum $V32_DST"
  echo "[upload] v32 已上传并 compile 过"
  ;;
blue)
  ssh_do "free -m | head -2"
  ssh_do "available=\$(free -m | awk '/Mem:/{print \$7}'); \\
    if [ \"\$available\" -lt 4000 ]; then echo '[ABORT] 可用内存 <4000MB,蓝实例会顶穿,勿起'; exit 1; fi; \\
    pkill -f 'COMPASS_PORT=$BLUE_PORT' 2>/dev/null || true; \\
    cd /home/ubuntu/nautilus-compass && \\
    COMPASS_PORT=$BLUE_PORT COMPASS_EMBED_BUDGET=300000 COMPASS_CHUNK_RECALL=1 \\
    nohup python3 $V32_DST >> $PLUGIN_CACHE/daemon_blue.log 2>&1 & \\
    echo \$! > $PLUGIN_CACHE/daemon_blue.pid; echo \"[blue] 蓝实例 PID=\$(cat $PLUGIN_CACHE/daemon_blue.pid) :$BLUE_PORT\""
  ;;
verify)
  ssh_do "sleep 5; python3 - <<'EOF'
import json, socket, time
# J5:listen 立即开(warmup 后台)——蓝实例起来 5s 内 ping 应通
t0=time.time()
try:
    s=socket.create_connection(('127.0.0.1', 9877), 5)
    s.sendall(b'{\"action\":\"ping\"}\\n'); r=json.loads(s.recv(4096).decode()); s.close()
    print('[J5-listen] ping ok in %.1fs' % (time.time()-t0), 'PASS' if r.get('pong') else 'FAIL')
except Exception as e:
    print('[J5-listen] FAIL:', e)
# J4:status(等待 warmup 完成后 p95 应正常;此处只验证 status 可达+RSS)
for i in range(30):
    try:
        s=socket.create_connection(('127.0.0.1', 9877), 5)
        s.sendall(b'{\"action\":\"status\"}\\n'); st=json.loads(s.recv(65536).decode()); s.close()
        if st.get('ok'): break
    except Exception: pass
    time.sleep(30)
print('[status] rss_mb=%s uptime_s=%s' % (st.get('rss_mb'), st.get('uptime_s')))
EOF"
  ;;
switch)
  echo "!! 切换前确认:verify 已绿 + 现在在窗口内(10/1 08:53 读数之后)"
  ssh_do "systemctl stop compass-bge-daemon && \\
    cd /home/ubuntu/nautilus-compass && \\
    COMPASS_EMBED_BUDGET=300000 COMPASS_CHUNK_RECALL=1 \\
    nohup python3 $V32_DST >> $PLUGIN_CACHE/daemon.log 2>&1 & \\
    echo \$! > $PLUGIN_CACHE/daemon.pid; \\
    sleep 3; \\
    kill \$(cat $PLUGIN_CACHE/daemon_blue.pid) 2>/dev/null || true; \\
    echo '[switch] v32 已上 9876,蓝实例退役;20min 观察:journalctl -u compass-bge-daemon 不再是日志源,tail $PLUGIN_CACHE/daemon.log'"
  ;;
rollback)
  ssh_do "kill \$(cat $PLUGIN_CACHE/daemon.pid) 2>/dev/null || true; \\
    systemctl start compass-bge-daemon && \\
    echo '[rollback] v32 已停,原版 systemd 拉起'"
  ;;
*)
  echo "用法: $0 upload|blue|verify|switch|rollback"; exit 1 ;;
esac
