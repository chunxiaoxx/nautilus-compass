#!/bin/bash
# 停 V5 Memory Daemon

PLUGIN_DIR="$(dirname "$(readlink -f "$0")")"
PYTHON=""
for c in python3 python; do
    if command -v "$c" &>/dev/null; then PYTHON="$c"; break; fi
done
[ -z "$PYTHON" ] && exit 1

"$PYTHON" "$PLUGIN_DIR/daemon.py" stop
echo "✅ daemon stop 命令已发"
