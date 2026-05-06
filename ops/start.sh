#!/bin/bash
# Cloud start · BGE daemon then uvicorn gateway
set -e
cd /home/ubuntu/nautilus-compass
mkdir -p .cache

# 1) start BGE daemon in background
python3 daemon.py >> .cache/daemon.log 2>&1 &
DAEMON_PID=$!
echo "$(date) daemon PID=$DAEMON_PID" >> .cache/service.log

# 2) wait for daemon socket up to 90s
for i in $(seq 1 90); do
    if python3 -c "import socket; s=socket.socket(); s.settimeout(0.5); s.connect(('127.0.0.1',9876)); s.close()" 2>/dev/null; then
        echo "$(date) daemon ready" >> .cache/service.log
        break
    fi
    if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
        echo "$(date) daemon crashed · log:" >> .cache/service.log
        tail -20 .cache/daemon.log >> .cache/service.log
        exit 1
    fi
    sleep 1
done

trap "kill -TERM $DAEMON_PID 2>/dev/null; wait $DAEMON_PID" TERM INT

# 3) exec gateway (foreground)
exec uvicorn compass_http:app \
    --host 127.0.0.1 \
    --port 8765 \
    --workers 2 \
    --log-level info
