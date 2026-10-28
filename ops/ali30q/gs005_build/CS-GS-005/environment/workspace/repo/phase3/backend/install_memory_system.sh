#!/bin/bash

# Phase 1: Evomap.ai Memory System Installation Script
# This script installs dependencies and sets up the memory system

set -e

echo "🚀 Phase 1: Installing Evomap.ai Memory System"
echo "=============================================="

# Check if running on Windows (Git Bash)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "⚠️  Detected Windows environment"
    echo "Please run the following commands manually:"
    echo ""
    echo "1. Install Python dependencies:"
    echo "   pip install -r requirements.txt"
    echo ""
    echo "2. Install pgvector (if using PostgreSQL):"
    echo "   - Download from: https://github.com/pgvector/pgvector/releases"
    echo "   - Or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector"
    echo ""
    echo "3. Run database migration:"
    echo "   python manage_migrations.py upgrade"
    echo ""
    echo "4. Test the system:"
    echo "   python test_memory_system.py"
    exit 0
fi

# Linux/Mac installation
echo ""
echo "📦 Step 1: Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "🗄️  Step 2: Setting up PostgreSQL with pgvector..."

# Check if PostgreSQL is installed
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL found"

    # Try to install pgvector
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Installing pgvector on Linux..."
        sudo apt-get update
        sudo apt-get install -y postgresql-contrib postgresql-server-dev-all

        # Clone and build pgvector
        cd /tmp
        git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
        cd pgvector
        make
        sudo make install
        cd -

        echo "✅ pgvector installed"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Installing pgvector on macOS..."
        brew install pgvector
        echo "✅ pgvector installed"
    fi

    # Enable extension in database
    echo "Enabling pgvector extension..."
    psql -U postgres -d nautilus -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo "⚠️  Could not enable extension automatically"
else
    echo "⚠️  PostgreSQL not found. Please install PostgreSQL and pgvector manually."
    echo "   Or use Docker: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres ankane/pgvector"
fi

echo ""
echo "🔄 Step 3: Running database migrations..."
python3 manage_migrations.py upgrade || echo "⚠️  Migration failed. Please run manually: python manage_migrations.py upgrade"

echo ""
echo "🧪 Step 4: Testing memory system..."
python3 test_memory_system.py

echo ""
echo "✅ Installation complete!"
echo ""
echo "📚 Next steps:"
echo "1. Start the server: uvicorn main:app --reload"
echo "2. Check API docs: http://localhost:8000/docs"
echo "3. Test memory endpoints: http://localhost:8000/api/memory/memories"
echo ""
echo "📖 See MEMORY_SYSTEM_IMPLEMENTATION.md for detailed documentation"
