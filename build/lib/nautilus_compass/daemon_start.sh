#!/bin/bash
# 启动 V5 Memory Daemon · 后台跑 · 第一次 cold-load BGE 后常驻
# 可重复跑 · 如已在跑则 noop

PLUGIN_DIR="$(dirname "$(readlink -f "$0")")"

PYTHON=""
for c in python3 python; do
    if command -v "$c" &>/dev/null; then PYTHON="$c"; break; fi
done
[ -z "$PYTHON" ] && { echo "❌ no python"; exit 1; }

# 检查是否已 alive
if "$PYTHON" "$PLUGIN_DIR/daemon.py" ping 2>/dev/null; then
    echo "✅ V5 Memory Daemon 已在跑 (port 9876)"
    exit 0
fi

# 后台启动 · nohup + disown
echo "启动 V5 Memory Daemon ..."
nohup "$PYTHON" "$PLUGIN_DIR/daemon.py" > /dev/null 2>&1 &
DAEMON_PID=$!
disown $DAEMON_PID 2>/dev/null
echo "PID: $DAEMON_PID · 等 BGE load (~30s) ..."

# 轮询 ping 直到 alive (最多 60s)
for i in $(seq 1 60); do
    sleep 1
    if "$PYTHON" "$PLUGIN_DIR/daemon.py" ping 2>/dev/null; then
        echo "✅ V5 Memory Daemon ready (took ${i}s)"
        echo "   port 9876 · PID file: $PLUGIN_DIR/.cache/daemon.pid"
        echo "   log: $PLUGIN_DIR/.cache/daemon.log"
        exit 0
    fi
done

echo "❌ daemon 60s 内没起来 · 看 $PLUGIN_DIR/.cache/daemon.log"
exit 1
