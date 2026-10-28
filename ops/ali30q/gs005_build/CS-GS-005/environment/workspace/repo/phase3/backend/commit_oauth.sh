#!/bin/bash
# Git commit script for OAuth 2.0 implementation

echo "=========================================="
echo "Committing OAuth 2.0 Implementation"
echo "=========================================="
echo ""

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Not in a git repository"
    echo "Please run this from the repository root"
    exit 1
fi

# Show status
echo "Git status:"
git status --short

echo ""
echo "Files to be committed:"
echo "  New files: 16"
echo "  Modified files: 2"
echo ""

# Ask for confirmation
read -p "Proceed with commit? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Commit cancelled"
    exit 0
fi

# Stage all OAuth-related files
echo ""
echo "Staging files..."

# New files
git add models/oauth.py
git add api/oauth.py
git add migrations/002_add_oauth_tables.py
git add sdk/python/nautilus_oauth.py
git add sdk/python/examples.py
git add sdk/python/setup.py
git add sdk/python/README.md
git add tests/test_oauth.py
git add test_oauth_quick.py
git add docs/OAUTH_GUIDE.md
git add OAUTH_IMPLEMENTATION.md
git add OAUTH_README.md
git add OAUTH_FINAL_REPORT.md
git add OAUTH_FILES_SUMMARY.md
git add deploy_oauth.sh
git add deploy_oauth.bat
git add COMMIT_MESSAGE.txt

# Modified files
git add models/database.py
git add main.py

echo "✅ Files staged"

# Commit with message from file
echo ""
echo "Creating commit..."
git commit -F COMMIT_MESSAGE.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Commit successful!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Review the commit: git show"
    echo "2. Push to remote: git push"
    echo "3. Create pull request"
    echo ""
else
    echo ""
    echo "❌ Commit failed"
    exit 1
fi
