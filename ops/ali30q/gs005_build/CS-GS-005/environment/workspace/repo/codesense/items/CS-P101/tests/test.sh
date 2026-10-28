#!/usr/bin/env bash
set -euo pipefail
# CS-P101 判分器(甲方demo形态):pytest 21条→reward二值;收集agent.patch
cd /workspace

pip install -q pytest 2>/dev/null || true
if python3 -m pytest /tests/test_csp101.py -q --tb=no 2>&1; then
    echo 1 > /logs/verifier/reward.txt
else
    echo 0 > /logs/verifier/reward.txt
fi

# 收集 agent.patch(甲方demo同款)
(
    set -u
    _repo=""
    for _d in /workspace /testbed "$PWD"; do
        [ -d "$_d" ] || continue
        if git -c safe.directory='*' -C "$_d" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            _repo="$_d"; break
        fi
    done
    if [ -n "$_repo" ]; then
        git -C "$_repo" add -A >/dev/null 2>&1 || true
        git -C "$_repo" diff --cached > /logs/artifacts/agent.patch 2>/dev/null || true
    fi
)
