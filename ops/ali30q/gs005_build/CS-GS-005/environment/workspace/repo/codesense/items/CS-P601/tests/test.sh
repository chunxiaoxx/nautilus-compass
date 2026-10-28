#!/usr/bin/env bash
set -euo pipefail
cd /workspace
pip install -q pytest 2>/dev/null || true
if python3 -m pytest /tests/test_csp601.py -q --tb=no 2>&1; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi
(
    set -u
    for _d in /workspace /testbed "$PWD"; do
        [ -d "$_d" ] || continue
        if git -c safe.directory='*' -C "$_d" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            git -C "$_d" add -A >/dev/null 2>&1 || true
            git -C "$_d" diff --cached > /logs/artifacts/agent.patch 2>/dev/null || true
            break
        fi
    done
)
