#!/bin/bash
# Prepare a clean public repo from current HEAD (no history, no secrets)
#
# Prerequisites:
#   1. Rename current repo to nautilus-core-private on GitHub (set Private)
#   2. Create new empty nautilus-core repo on GitHub (Public)
#   3. Run this script from the nautilus-core-private local directory
#
# Usage: bash scripts/prepare-public-repo.sh

set -e

PUBLIC_REPO="https://github.com/chunxiaoxx/nautilus-core.git"
WORK_DIR="/tmp/nautilus-public"

echo "=== Step 1: Create clean copy ==="
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# Copy only tracked files (excludes .env, node_modules, etc.)
git ls-files | while read f; do
    # Skip files that should not be in public repo
    case "$f" in
        _dead_code_backup_*) continue ;;
        ai-automation-system/*) continue ;;
        */node_modules/*) continue ;;
        *.env) continue ;;
        *.env.*) continue ;;
    esac
    mkdir -p "$WORK_DIR/$(dirname "$f")"
    cp "$f" "$WORK_DIR/$f"
done

echo "=== Step 2: Initialize fresh git repo ==="
cd "$WORK_DIR"
git init
git checkout -b main

echo "=== Step 3: Add all clean files ==="
git add -A

echo "=== Step 4: Create initial commit ==="
git commit -m "$(cat <<'COMMIT'
Initial release: Nautilus | 智涌 — DMAS + Economic Survival + Self-Bootstrapping

Three-layer Agent-First platform:
  Layer 1: DMAS Protocol (arXiv:2512.02410) — decentralized agent registry,
           trust-aware communication, service discovery
  Layer 2: Economic Survival — PoUW tokens, 6-tier survival mechanism,
           autonomous bidding, reputation system
  Layer 3: Self-Bootstrapping Engine — Observatory, RAID-3 analysis,
           proposal consensus, A/B sandbox, evolution ledger

578 commits of development consolidated into clean public release.
COMMIT
"

echo "=== Step 5: Push to public repo ==="
git remote add origin "$PUBLIC_REPO"
git push -u origin main

echo ""
echo "=== Done! ==="
echo "Public repo: $PUBLIC_REPO"
echo "Files copied: $(git ls-files | wc -l)"
echo ""
echo "Next steps:"
echo "  1. Verify https://github.com/chunxiaoxx/nautilus-core"
echo "  2. Add topics: ai-agents, multi-agent-system, blockchain, dmas"
echo "  3. Rotate ALL secrets that were ever in the private repo"
