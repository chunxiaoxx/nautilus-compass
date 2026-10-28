#!/bin/bash
# Sync agent-engine source to backend/agent_engine on deploy
# The backend imports from backend/agent_engine/, but the git-tracked
# source of truth is agent-engine/. This script keeps them in sync.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="$(dirname "$SCRIPT_DIR")"

SRC="$BASE_DIR/agent-engine"
DST="$BASE_DIR/backend/agent_engine"

if [ ! -d "$SRC" ]; then
    echo "ERROR: source directory not found: $SRC"
    exit 1
fi

if [ ! -d "$DST" ]; then
    echo "ERROR: destination directory not found: $DST"
    exit 1
fi

# Sync each subdirectory
for subdir in executors bootstrap core; do
    if [ -d "$SRC/$subdir" ]; then
        mkdir -p "$DST/$subdir"
        cp -r "$SRC/$subdir/"* "$DST/$subdir/" 2>/dev/null || true
    fi
done

# Sync llm directory (flat .py files)
if [ -d "$SRC/llm" ]; then
    mkdir -p "$DST/llm"
    cp "$SRC/llm/"*.py "$DST/llm/" 2>/dev/null || true
fi

# Sync top-level .py files
cp "$SRC/"*.py "$DST/" 2>/dev/null || true

echo "agent-engine synced to backend/agent_engine"
