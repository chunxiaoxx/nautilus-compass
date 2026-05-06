#!/bin/bash
# compass v0.9.0 · npm publish @nautilus/compass-mcp
# Status: 2026-05-05 · ready · 等用户 GO

set -euo pipefail

NPM_DIR="${NPM_DIR:-$HOME/.claude/plugins/nautilus-compass/npm}"

echo "=== @nautilus/compass-mcp npm publish ==="
echo "dir: $NPM_DIR"
echo

cd "$NPM_DIR"

# 1. Pre-flight
echo "[1] pre-flight..."
test -f package.json || { echo "no package.json"; exit 1; }
test -f bin/cli.js || { echo "no bin/cli.js"; exit 1; }
test -f README.md || { echo "no README.md"; exit 1; }
node --version
npm --version
echo "  ✓ files present"
echo

# 2. Selftest
echo "[2] running selftest..."
node bin/cli.js --selftest
echo "  ✓ selftest pass"
echo

# 3. npm whoami
echo "[3] checking npm login..."
WHO=$(npm whoami 2>&1 || echo "NOT_LOGGED_IN")
if [ "$WHO" = "NOT_LOGGED_IN" ]; then
  echo "  ⚠️ not logged in · run: npm login"
  echo "  required: npmjs.com account · @nautilus organization (must exist or be created first)"
  exit 1
fi
echo "  ✓ logged in as: $WHO"
echo

# 4. Verify @nautilus org
echo "[4] verifying @nautilus organization..."
npm org ls @nautilus 2>&1 | tail -3 || {
  echo "  ⚠️ @nautilus org may not exist · create at npmjs.com/org/create"
  echo "  proceeding anyway (npm publish will fail with clear message if org missing)"
}
echo

# 5. Dry run
echo "[5] dry-run publish..."
npm publish --dry-run 2>&1 | tail -15
echo "  ✓ dry-run looks clean (review file list above)"
echo

# 6. Confirm + publish
echo "[6] FINAL · ready to publish"
read -p "Publish @nautilus/compass-mcp@$(node -p "require('./package.json').version") to npm? [y/N] " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
  echo "Aborted by user. No changes."
  exit 0
fi
echo "  publishing..."
npm publish --access public 2>&1 | tail -10
echo

# 7. Verify
echo "[7] verifying publish..."
sleep 3
npm view @nautilus/compass-mcp version 2>&1 | head -3
echo

# 8. Smoke test via npx
echo "[8] smoke test via npx..."
npx -y @nautilus/compass-mcp --selftest 2>&1 | head -3
echo

echo "=== npm publish complete ==="
echo
echo "Next:"
echo "  1. Update README.md to use 'npm install -g @nautilus/compass-mcp' (replace TODO)"
echo "  2. Tweet/HN post · paper/BLOGPOST.md is 草稿"
echo "  3. Update GitHub release · paper/GITHUB_RELEASE.md"
