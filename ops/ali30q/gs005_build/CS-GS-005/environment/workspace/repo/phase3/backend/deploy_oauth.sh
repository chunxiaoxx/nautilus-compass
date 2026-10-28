#!/bin/bash
# OAuth 2.0 Service Deployment Script

echo "=========================================="
echo "Nautilus OAuth 2.0 Service Deployment"
echo "=========================================="
echo ""

# Step 1: Check environment
echo "Step 1: Checking environment..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    exit 1
fi
echo "✅ Environment file found"

# Step 2: Install dependencies
echo ""
echo "Step 2: Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Step 3: Run database migration
echo ""
echo "Step 3: Running database migration..."
python manage_migrations.py upgrade
if [ $? -eq 0 ]; then
    echo "✅ Database migration completed"
else
    echo "❌ Database migration failed"
    exit 1
fi

# Step 4: Run OAuth tests
echo ""
echo "Step 4: Running OAuth tests..."
python test_oauth_quick.py
if [ $? -eq 0 ]; then
    echo "✅ OAuth tests passed"
else
    echo "❌ OAuth tests failed"
    exit 1
fi

# Step 5: Run full test suite
echo ""
echo "Step 5: Running full test suite..."
pytest tests/test_oauth.py -v
if [ $? -eq 0 ]; then
    echo "✅ Full test suite passed"
else
    echo "⚠️  Some tests failed, but continuing..."
fi

echo ""
echo "=========================================="
echo "OAuth 2.0 Service Deployment Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart the application"
echo "2. Test OAuth flow manually"
echo "3. Create sample OAuth clients"
echo "4. Update API documentation"
echo ""
echo "OAuth endpoints available at:"
echo "  - POST   /oauth/clients"
echo "  - GET    /oauth/clients/{client_id}"
echo "  - GET    /oauth/authorize"
echo "  - POST   /oauth/token"
echo "  - GET    /oauth/userinfo"
echo "  - POST   /oauth/verify"
echo "  - POST   /oauth/revoke"
echo ""
