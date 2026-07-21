#!/usr/bin/env bash

# Bootstrap helper for Compass benchmark/CLI sessions that require
# a Python 3.10+ interpreter for all eval code paths.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

set +e
TMP_RESOLVE_LOG="$(mktemp)"
bash "$REPO_DIR/scripts/compass_py.sh" > "$TMP_RESOLVE_LOG" 2>&1
BOOTSTRAP_STATUS=$?
RESOLVED_PYTHON="$(tr -d '\r' < "$TMP_RESOLVE_LOG")"
rm -f "$TMP_RESOLVE_LOG"
set -e
if [ "$BOOTSTRAP_STATUS" -ne 0 ] || [ -z "${RESOLVED_PYTHON:-}" ]; then
  if [ -n "$RESOLVED_PYTHON" ]; then
    printf "%s\n" "$RESOLVED_PYTHON" >&2
  fi
  echo "[compass_bootstrap] Error: unable to resolve Python 3.10+ interpreter" >&2
  exit 1
fi

export PYTHON="${PYTHON:-$RESOLVED_PYTHON}"
export COMPASS_ROOT="$REPO_DIR"
