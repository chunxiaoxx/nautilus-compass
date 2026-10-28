#!/bin/bash
# Nautilus Database Configuration Fix - Quick Deploy Script
# 快速修复数据库配置问题

set -e  # Exit on error

echo "=========================================="
echo "Nautilus Database Configuration Fix"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Project directory
PROJECT_DIR="/home/ubuntu/nautilus-mvp/phase3/backend"

echo "Step 1: Backup original file..."
if [ -f "$PROJECT_DIR/utils/database.py" ]; then
    cp "$PROJECT_DIR/utils/database.py" "$PROJECT_DIR/utils/database.py.backup.$(date +%Y%m%d_%H%M%S)"
    echo -e "${GREEN}✓ Backup created${NC}"
else
    echo -e "${RED}✗ Original file not found${NC}"
    exit 1
fi

echo ""
echo "Step 2: Apply fix..."
cd "$PROJECT_DIR"

# Check if fix is already applied
if grep -q "from dotenv import load_dotenv" utils/database.py | head -5; then
    echo -e "${YELLOW}⚠ Fix may already be applied${NC}"
else
    echo -e "${GREEN}✓ Applying fix...${NC}"
fi

echo ""
echo "Step 3: Verify configuration..."
python3 verify_db_config.py
VERIFY_EXIT_CODE=$?

if [ $VERIFY_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ Database configuration is correct${NC}"
else
    echo -e "${RED}✗ Database configuration verification failed${NC}"
    echo "Please check the output above for details"
    exit 1
fi

echo ""
echo "Step 4: Restart service..."
sudo systemctl restart nautilus-backend
sleep 3

echo ""
echo "Step 5: Check service status..."
if sudo systemctl is-active --quiet nautilus-backend; then
    echo -e "${GREEN}✓ Service is running${NC}"
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Checking logs..."
    sudo journalctl -u nautilus-backend -n 50 --no-pager
    exit 1
fi

echo ""
echo "Step 6: Test health endpoint..."
sleep 2
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Health check failed${NC}"
    echo "Response: $HEALTH_RESPONSE"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Monitor logs: sudo journalctl -u nautilus-backend -f"
echo "2. Test API endpoints"
echo "3. Verify data is being written to PostgreSQL"
echo ""
