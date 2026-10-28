#!/bin/bash

# Agent Identity System V2 - Complete Deployment Script
# This script automates the deployment of the new agent identity system

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════╗"
echo "║   Agent Identity System V2 - Deployment Script            ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check environment
echo "Step 1: Checking environment..."
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file not found${NC}"
    echo "Please create .env file with DATABASE_URL"
    exit 1
fi

if ! grep -q "DATABASE_URL" .env; then
    echo -e "${RED}❌ DATABASE_URL not found in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Environment configured${NC}"
echo ""

# Step 2: Run tests
echo "Step 2: Running tests..."
python -m pytest tests/test_agent_auth.py -v --tb=short
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Tests failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ All tests passed${NC}"
echo ""

# Step 3: Run database migration
echo "Step 3: Running database migration..."
python migrations/create_agents_v2_table.py
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Migration failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Database migration completed${NC}"
echo ""

# Step 4: Verify integration
echo "Step 4: Verifying integration..."
if ! grep -q "agents_v2_router" main.py; then
    echo -e "${RED}❌ V2 router not integrated in main.py${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Integration verified${NC}"
echo ""

# Step 5: Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Deployment Complete!                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "1. Start the server: uvicorn main:app --reload"
echo "2. Test endpoints: curl http://localhost:8000/api/agents/v2"
echo "3. Try example: python examples/agent_sdk_example.py"
echo ""
echo -e "${GREEN}✅ Agent Identity System V2 is ready!${NC}"
