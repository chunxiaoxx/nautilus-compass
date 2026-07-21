#!/bin/bash
# Run behavior A/B using zenmind project's existing API keys.
# Reads .env via Python (no shell echo · keys never enter transcript).
#
# Subject = Claude Sonnet 4.6 (zenmind ANTHROPIC config)
# Judge   = Vertex AI Gemini Flash (GOOGLE_APPLICATION_CREDENTIALS)
#
# Usage:
#   bash tests/run_behavior_ab_zenmind.sh [n]
#   default n=10 (~$0.30 in API cost)

set -e

N="${1:-10}"
RUN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="$RUN_DIR/../scripts/bootstrap_compass_env.sh"
PLUGIN="$HOME/.claude/plugins/zenmind-mem"
# .env (production) has real MiniMax key (len=125) ·
# .env.development has stale 20-char placeholders, don't use.
ZENMIND_ENV="$HOME/quantum-buddha-project/.env"
GCP_JSON="${GOOGLE_APPLICATION_CREDENTIALS:-$HOME/Downloads/chunxiao-vm-260414-de9e73f4697d.json}"

if [ ! -f "$ZENMIND_ENV" ]; then
    echo "❌ zenmind .env.development not found: $ZENMIND_ENV"
    exit 1
fi

# Use Python to parse .env safely · never echo to stdout · pass via env to subprocess
bash "$SCRIPT"
RUN_PYTHON="$PYTHON"

PYTHONIOENCODING=utf-8 PYTHONUTF8=1 "$RUN_PYTHON" -c "
import os, subprocess, sys
from pathlib import Path

import os.path as _op
# bash $HOME on git-bash is /c/Users/chunx · Windows Python wants C:\Users\chunx
env_file = Path(_op.expanduser('~/quantum-buddha-project/.env'))
gcp_json = Path(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS') or
                _op.expanduser('~/Downloads/chunxiao-vm-260414-de9e73f4697d.json'))
plugin = Path(_op.expanduser('~/.claude/plugins/zenmind-mem'))
n = int('$N')

# Parse zenmind .env
env_extra = {}
for line in env_file.read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#'): continue
    if '=' not in line: continue
    k, _, v = line.partition('=')
    env_extra[k.strip()] = v.strip().strip('\"').strip(\"'\")

# Use real MiniMax production key (verified · len=125 on api.minimaxi.com)
mm_key = env_extra.get('MINIMAX_API_KEY', '')
if not mm_key or len(mm_key) < 50:
    print(f'❌ MINIMAX_API_KEY in {env_file} too short (len={len(mm_key)}); '
          'use .env not .env.development', file=sys.stderr)
    sys.exit(1)
if not gcp_json.exists():
    print(f'❌ GCP service account JSON not found: {gcp_json}', file=sys.stderr)
    sys.exit(1)

print(f'subject = MiniMax-M2 (via api.minimaxi.com · zenmind production key)')
print(f'judge   = Gemini Flash (Vertex AI · {gcp_json.name})')
print(f'n = {n}')
print()

# Build env for subprocess · keys never echoed
sub_env = os.environ.copy()
sub_env['MINIMAX_API_KEY'] = mm_key
sub_env['MINIMAX_GROUP_ID'] = env_extra.get('MINIMAX_GROUP_ID', '')
sub_env['GOOGLE_APPLICATION_CREDENTIALS'] = str(gcp_json)
sub_env['ZMM_SUBJECT_PROVIDER'] = 'minimax'
sub_env['ZMM_SUBJECT_MODEL'] = 'MiniMax-M2'
sub_env['ZMM_JUDGE_PROVIDER'] = 'gemini'
# call_subject_llm 用 'https://api.minimax.io' 默认 · 改 intl
sub_env['ZMM_MINIMAX_BASE'] = 'https://api.minimaxi.com'

# Run eval
ret = subprocess.run(
    [sys.executable, '-u', str(plugin / 'tests/eval_behavior_ab.py'), '--n', str(n)],
    env=sub_env, cwd=str(plugin),
)
sys.exit(ret.returncode)
"
