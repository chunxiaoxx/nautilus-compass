#!/bin/bash
# Bootstrap autonomous Soul on cloud-server in an isolated clean clone.
# Does NOT touch ~/nautilus-mvp.
set -euo pipefail

WORKSPACE="$HOME/nautilus-soul-workspace"
REPO="https://github.com/chunxiaoxx/nautilus-core.git"

if [ ! -d "$WORKSPACE" ]; then
    git clone "$REPO" "$WORKSPACE"
fi
cd "$WORKSPACE"
git fetch origin master
# Clean autonomous clone · no local drift. Goal-done state lives in PRs (merged
# → master goals.yaml updates), NOT local files · so reset --hard is safe.
# Anti-duplicate while a cycle PR is unmerged: daemon checks pr_gate.has_open_pr_for
# and skips re-selecting a goal that already has an open PR.
git reset --hard origin/master

# Env file (edit secrets here · never commit)
if [ ! -f "$WORKSPACE/.soul-env" ]; then
    cat > "$WORKSPACE/.soul-env" <<'EOF'
DEEPSEEK_API_KEY=__SET_ME__
DEEPSEEK_BASE_URL=https://api.deepseek.com/anthropic
DEEPSEEK_MODEL=deepseek-v4-pro
GOOGLE_APPLICATION_CREDENTIALS=/home/ubuntu/.config/gcloud/soul-sa.json
SOUL_DAILY_COST_CAP=20.0
PYTHONPATH=/home/ubuntu/nautilus-soul-workspace/phase3/backend
EOF
    echo "EDIT $WORKSPACE/.soul-env with real DEEPSEEK_API_KEY before enabling timer"
fi

pip install --user pyyaml psycopg2-binary anthropic >/dev/null 2>&1 || true

sudo cp phase3/soul/systemd/nautilus-soul.service /etc/systemd/system/
sudo cp phase3/soul/systemd/nautilus-soul.timer /etc/systemd/system/
sudo systemctl daemon-reload
echo "Bootstrap complete. To activate: sudo systemctl enable --now nautilus-soul.timer"
echo "First verify a manual run: cd $WORKSPACE/phase3 && python3 -m soul.daemon"
