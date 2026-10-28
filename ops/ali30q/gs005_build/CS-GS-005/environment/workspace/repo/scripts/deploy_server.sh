#!/bin/bash
# Nautilus server deployment script
# Usage: bash scripts/deploy_server.sh
# Requires: SSH access to server, git remote configured

set -e

echo "=== Nautilus Server Deployment ==="
echo "Time: $(date -u)"

# Config
REMOTE="origin"
BRANCH="master"
BACKEND_DIR="phase3/backend"
SERVICE="nautilus-backend.service"

# 1. Pull latest code
echo "[1/5] Pulling latest code..."
git fetch $REMOTE
git merge $REMOTE/$BRANCH --ff-only
echo "✓ Code updated to $(git rev-parse --short HEAD)"

# 2. Install Python dependencies
echo "[2/5] Installing dependencies..."
cd $BACKEND_DIR
pip install -r requirements.txt -q
cd ../..
echo "✓ Dependencies installed"

# 3. Run Alembic migrations
echo "[3/5] Running DB migrations..."
cd $BACKEND_DIR
alembic upgrade head
cd ../..
echo "✓ Migrations complete"

# 4. Check required env vars
echo "[4/5] Checking environment..."
REQUIRED_VARS=("DATABASE_URL" "SECRET_KEY")
OPTIONAL_VARS=("NAU_TOKEN_ADDRESS" "BLOCKCHAIN_PRIVATE_KEY" "TELEGRAM_BOT_TOKEN")

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "✗ MISSING required: $var"
        exit 1
    fi
done

for var in "${OPTIONAL_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "⚠ Optional not set: $var"
    else
        echo "✓ $var configured"
    fi
done

# 5. Restart service
echo "[5/5] Restarting service..."
sudo systemctl restart $SERVICE
sleep 3
STATUS=$(systemctl is-active $SERVICE)
if [ "$STATUS" = "active" ]; then
    echo "✓ Service $SERVICE is running"
else
    echo "✗ Service failed to start. Check: sudo journalctl -u $SERVICE -n 50"
    exit 1
fi

echo ""
echo "=== Deployment complete! ==="
echo "Commit: $(git log --oneline -1)"
echo "Service: $STATUS"
echo ""
echo "Verify:"
echo "  curl https://www.nautilus.social/api/hub/stats | python -m json.tool"
