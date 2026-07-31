#!/usr/bin/env bash

# Unified Python resolver for Compass evaluation/runtime scripts.
# - Prefer PYTHON env var when set and valid.
# - Fallback to python3.13/3.12/3.11/3.10/python/python3 (if >=3.10).
# - Exit with clear remediation hints when unavailable.

set -euo pipefail

print_help() {
  cat <<'EOF'
Usage: scripts/compass_py.sh [--version]

Default: print selected python interpreter path.
--version: print selected interpreter + version.
EOF
}

need_python_at_least() {
  local py="$1"
  "$py" - <<'PY'
import sys
sys.exit(0 if sys.version_info >= (3, 10) else 1)
PY
}

resolver_path() {
  local candidate
  for candidate in "$@"; do
    if [ -z "$candidate" ]; then
      continue
    fi
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if need_python_at_least "$candidate"; then
      command -v "$candidate"
      return 0
    fi
  done
  return 1
}

VERSION_MODE=0
if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
  print_help
  exit 0
fi

if [ "${1:-}" = "--version" ]; then
  VERSION_MODE=1
fi

cands=()
if [ -n "${PYTHON:-}" ]; then
  cands+=("$PYTHON")
fi
cands+=(python3.13 python3.12 python3.11 python3.10 python3 python)

if [ "$#" -gt 1 ]; then
  echo "[compass_py] Error: unexpected argument(s)."
  print_help
  exit 2
fi

PYTHON_PATH="$(resolver_path "${cands[@]}")" || {
  echo "[compass_py] Error: need Python >= 3.10 for Compass eval stack (daemon.py uses Path | None)." >&2
  echo "[compass_py] Hint (from current env):" >&2
  echo "  - Set PYTHON=/path/to/python3.10+ and rerun" >&2
  echo "  - Or install 3.10/3.11/3.12/3.13 and rerun" >&2
  echo "  - Or open env shell with venv/python3.10+ activated." >&2
  exit 1
}

if [ "$VERSION_MODE" = "1" ]; then
  PYTHON_VER="$("$PYTHON_PATH" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')"
  echo "${PYTHON_PATH} (Python ${PYTHON_VER})"
else
  echo "$PYTHON_PATH"
fi
