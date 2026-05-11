#!/usr/bin/env python3
"""Unit tests for v1.5 S2 proof-of-recall · in-process · no daemon required.

Tests the token mint + validate logic in mcp_server.py · doesn't hit BGE daemon
or filesystem.

Run:
    python3 tests/test_proof_of_recall.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# add parent dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mcp_server as M


def test_mint_returns_prefixed_token():
    M._recall_tokens.clear()
    top3 = [{"path": "session_xx.md", "description": "desc1"}]
    tok = M._mint_recall_token("v5", top3, "test query")
    assert tok.startswith("rt_"), f"token should start with 'rt_', got {tok!r}"
    assert len(tok) == 19, f"token should be 19 chars (rt_ + 16 hex), got {len(tok)}"
    assert tok in M._recall_tokens


def test_validate_pass_on_path_match():
    M._recall_tokens.clear()
    top3 = [{"path": "session_20260511_v13.md", "description": "drift calibration"}]
    tok = M._mint_recall_token("v5", top3, "query")
    # cite path basename
    ok, reason = M._validate_recall_proof(tok, ["I read session_20260511_v13.md and learned X"], "v5")
    assert ok, f"path-match cite should pass, got reason={reason}"


def test_validate_pass_on_description_overlap():
    M._recall_tokens.clear()
    top3 = [{"path": "x.md", "description": "extreme-literal phrasing is necessary for FP suppression"}]
    tok = M._mint_recall_token("v5", top3, "query")
    # cite 20+ char chunk from description
    ok, reason = M._validate_recall_proof(tok, ["The lesson was extreme-literal phrasing is necessary"], "v5")
    assert ok, f"description overlap should pass, got reason={reason}"


def test_validate_fail_no_overlap():
    M._recall_tokens.clear()
    top3 = [{"path": "session_alpha.md", "description": "alpha content"}]
    tok = M._mint_recall_token("v5", top3, "query")
    ok, reason = M._validate_recall_proof(tok, ["totally unrelated text without any match"], "v5")
    assert not ok
    assert reason == "no_snippet_overlap"


def test_validate_fail_agent_mismatch():
    M._recall_tokens.clear()
    top3 = [{"path": "x.md", "description": "y"}]
    tok = M._mint_recall_token("v5", top3, "q")
    ok, reason = M._validate_recall_proof(tok, ["I read x.md"], "v6")  # wrong agent
    assert not ok
    assert reason == "agent_type_mismatch"


def test_validate_fail_no_token():
    M._recall_tokens.clear()
    ok, reason = M._validate_recall_proof("", ["anything"], "v5")
    assert not ok
    assert reason == "no_token_provided"

    ok, reason = M._validate_recall_proof("rt_nonexistent12345678", ["x"], "v5")
    assert not ok
    assert reason == "token_not_found_or_expired"


def test_validate_fail_empty_cited():
    M._recall_tokens.clear()
    top3 = [{"path": "x.md", "description": "y"}]
    tok = M._mint_recall_token("v5", top3, "q")
    ok, reason = M._validate_recall_proof(tok, [], "v5")
    assert not ok
    assert reason == "empty_cited"


def test_token_ttl_expiry():
    M._recall_tokens.clear()
    top3 = [{"path": "x.md", "description": "y"}]
    tok = M._mint_recall_token("v5", top3, "q")
    # backdate
    M._recall_tokens[tok]["issued_at"] = time.time() - M.RECALL_TOKEN_TTL_S - 10
    ok, reason = M._validate_recall_proof(tok, ["I read x.md"], "v5")
    assert not ok
    assert reason == "token_not_found_or_expired"
    # auto-cleanup
    assert tok not in M._recall_tokens


def test_lru_eviction_at_max():
    M._recall_tokens.clear()
    # mint MAX+5 tokens · oldest 5 should evict
    original_max = M.RECALL_TOKEN_MAX
    try:
        M.RECALL_TOKEN_MAX = 10
        tokens = []
        for i in range(15):
            t = M._mint_recall_token("v5", [{"path": f"f{i}.md", "description": ""}], f"q{i}")
            tokens.append(t)
        # first 5 should be evicted
        for old_t in tokens[:5]:
            assert old_t not in M._recall_tokens, f"{old_t} should have been evicted"
        # last 10 should remain
        for new_t in tokens[5:]:
            assert new_t in M._recall_tokens, f"{new_t} should still be present"
    finally:
        M.RECALL_TOKEN_MAX = original_max


def test_expired_pruning_on_mint():
    M._recall_tokens.clear()
    # add an expired token
    M._recall_tokens["rt_expired00000000"] = {
        "issued_at": time.time() - M.RECALL_TOKEN_TTL_S - 100,
        "agent_type": "v5",
        "query": "old",
        "top3_paths": ["x"],
        "top3_descriptions": [""],
    }
    # mint a new token · should trigger TTL prune
    new_t = M._mint_recall_token("v5", [{"path": "y.md", "description": ""}], "q")
    assert "rt_expired00000000" not in M._recall_tokens
    assert new_t in M._recall_tokens


def main() -> int:
    tests = [
        ("mint_returns_prefixed_token", test_mint_returns_prefixed_token),
        ("validate_pass_on_path_match", test_validate_pass_on_path_match),
        ("validate_pass_on_description_overlap", test_validate_pass_on_description_overlap),
        ("validate_fail_no_overlap", test_validate_fail_no_overlap),
        ("validate_fail_agent_mismatch", test_validate_fail_agent_mismatch),
        ("validate_fail_no_token", test_validate_fail_no_token),
        ("validate_fail_empty_cited", test_validate_fail_empty_cited),
        ("token_ttl_expiry", test_token_ttl_expiry),
        ("lru_eviction_at_max", test_lru_eviction_at_max),
        ("expired_pruning_on_mint", test_expired_pruning_on_mint),
    ]
    failed = []
    for name, fn in tests:
        try:
            fn()
            print(f"  PASS · {name}")
        except AssertionError as e:
            print(f"  FAIL · {name} · {e}")
            failed.append(name)
        except Exception as e:
            print(f"  ERROR · {name} · {type(e).__name__}: {e}")
            failed.append(name)
    print(f"\n{len(tests) - len(failed)}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
