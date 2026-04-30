#!/bin/bash
# Nautilus Compass · container entrypoint
# 1. start BGE daemon in background (blocks until model loaded)
# 2. exec uvicorn gateway in foreground

set -e

cd /opt/compass

echo "[entrypoint] starting BGE daemon ..."
python daemon.py > /opt/compass/.cache/daemon.log 2>&1 &
DAEMON_PID=$!
echo "[entrypoint] daemon PID=$DAEMON_PID · waiting for port 9876 ..."

# wait up to 90s for daemon to listen
for i in $(seq 1 90); do
    if python -c "import socket; s=socket.socket(); s.settimeout(0.5); s.connect(('127.0.0.1',9876)); s.close()" 2>/dev/null; then
        echo "[entrypoint] daemon ready · launching gateway"
        break
    fi
    if ! kill -0 "$DAEMON_PID" 2>/dev/null; then
        echo "[entrypoint] daemon crashed · log:"
        tail -50 /opt/compass/.cache/daemon.log
        exit 1
    fi
    sleep 1
done

# trap to forward SIGTERM/SIGINT to daemon for graceful shutdown
trap "kill -TERM $DAEMON_PID 2>/dev/null; wait $DAEMON_PID" TERM INT

# foreground gateway
exec uvicorn compass_http:app \
    --host 0.0.0.0 \
    --port 8765 \
    --workers "${COMPASS_GATEWAY_WORKERS:-2}" \
    --log-level "${COMPASS_LOG_LEVEL:-info}"
