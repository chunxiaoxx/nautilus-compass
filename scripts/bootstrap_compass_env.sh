#!/usr/bin/env bash

# Bootstrap helper for Compass benchmark/CLI sessions that require
# a Python 3.10+ interpreter for all eval code paths.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

set +e
ERR_LOG="$(mktemp)"
RESOLVED_PYTHON="$("$REPO_DIR/scripts/compass_py.sh" 2>"$ERR_LOG")"
BOOTSTRAP_STATUS=$?
set -e

if [ "$BOOTSTRAP_STATUS" -ne 0 ]; then
  if [ -s "$ERR_LOG" ]; then
    cat "$ERR_LOG" >&2
  fi
  echo "[compass_bootstrap] Error: unable to resolve Python 3.10+ interpreter" >&2
  rm -f "$ERR_LOG"
  exit 1
fi

rm -f "$ERR_LOG"
RESOLVED_PYTHON="$(printf "%s" "$RESOLVED_PYTHON" | tr -d '\r' | tr -d '\n')"
if [ -z "${RESOLVED_PYTHON:-}" ]; then
  echo "[compass_bootstrap] Error: resolver returned empty Python path" >&2
  exit 1
fi

export PYTHON="${PYTHON:-$RESOLVED_PYTHON}"
export COMPASS_ROOT="$REPO_DIR"
