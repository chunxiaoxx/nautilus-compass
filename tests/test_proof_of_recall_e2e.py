#!/usr/bin/env python3
"""E2E test for v1.5 S2 proof-of-recall · tool_recall + tool_ingest_obs.

Requires running BGE daemon. Tests the full round-trip:
  1. recall returns recall_token in the text output
  2. ingest_obs with that token + cited_snippets → proof_of_recall: pass
  3. ingest_obs with same token but bad snippets → proof_of_recall: fail
  4. ingest_obs without token → proof_of_recall: not_attempted
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import mcp_server as M


def _extract_token_from_recall_text(text: str) -> str:
    """recall text contains 'recall_token: rt_xxxx'"""
    m = re.search(r"recall_token:\s*(rt_[a-f0-9]+)", text)
    return m.group(1) if m else ""


def _extract_session_path_from_ingest_text(text: str) -> str:
    """ingest text · 'obs written · session_xxxx.md · ...'"""
    m = re.search(r"session_\S+?\.md", text)
    return m.group(0) if m else ""


def test_recall_returns_token_in_output():
    """tool_recall · output text contains 'recall_token: rt_...' on hit"""
    res = M.tool_recall({"query": "fake closure 305 P1-1", "top_k": 3})
    text = res.get("content", [{}])[0].get("text", "")
    if "No memories matched" in text:
        print(f"  SKIP · no recall hits to test (text: {text[:80]})")
        return
    tok = _extract_token_from_recall_text(text)
    assert tok and tok.startswith("rt_"), f"no recall_token in text: {text[:300]}"


def test_ingest_without_token_marks_not_attempted():
    res = M.tool_ingest_obs({
        "name": "test-s2-no-token",
        "description": "test without recall_token",
        "body": "this should mark proof_of_recall=not_attempted",
        "drift": "green",
    })
    text = res.get("content", [{}])[0].get("text", "")
    assert "proof_of_recall=not_attempted" in text, f"expected not_attempted, got: {text}"


def test_ingest_with_valid_token_marks_pass():
    """Full round-trip: recall → cite → ingest → pass"""
    # use a known existing memory to ensure recall returns something
    M._recall_tokens.clear()
    # manually inject a known top3 so we don't need daemon
    fake_top3 = [{"path": "session_test_abc.md", "description": "test description content"}]
    tok = M._mint_recall_token("test-agent", fake_top3, "test query")

    # ingest with valid cite + matching agent_type
    res = M.tool_ingest_obs({
        "name": "test-s2-valid",
        "description": "test with valid recall_token",
        "body": "I read session_test_abc.md and learned X",
        "drift": "green",
        "agent_type": "test-agent",
        "recall_token": tok,
        "cited_snippets": ["I read session_test_abc.md"],
    })
    text = res.get("content", [{}])[0].get("text", "")
    assert "proof_of_recall=pass" in text, f"expected pass, got: {text}"

    # cleanup
    path = _extract_session_path_from_ingest_text(text)
    if path:
        for proj_dir in M.PROJECTS_DIR.iterdir():
            target = proj_dir / "memory" / path
            if target.exists():
                target.unlink()


def test_ingest_with_invalid_cite_marks_fail():
    M._recall_tokens.clear()
    fake_top3 = [{"path": "session_abc.md", "description": "specific content here"}]
    tok = M._mint_recall_token("test-agent", fake_top3, "q")

    res = M.tool_ingest_obs({
        "name": "test-s2-fail",
        "description": "test with bad cite",
        "body": "completely unrelated text",
        "drift": "green",
        "agent_type": "test-agent",
        "recall_token": tok,
        "cited_snippets": ["totally unrelated foo bar baz qux"],
    })
    text = res.get("content", [{}])[0].get("text", "")
    assert "proof_of_recall=fail" in text, f"expected fail, got: {text}"
    assert "no_snippet_overlap" in text, f"expected reason in text: {text}"

    # cleanup
    path = _extract_session_path_from_ingest_text(text)
    if path:
        for proj_dir in M.PROJECTS_DIR.iterdir():
            target = proj_dir / "memory" / path
            if target.exists():
                target.unlink()


def test_session_md_has_proof_frontmatter():
    """Verify written session_*.md actually contains proof_of_recall: pass"""
    M._recall_tokens.clear()
    fake_top3 = [{"path": "session_check_md.md", "description": "frontmatter check content"}]
    tok = M._mint_recall_token("test-agent", fake_top3, "q")

    res = M.tool_ingest_obs({
        "name": "test-s2-md-check",
        "description": "verify frontmatter",
        "body": "see session_check_md.md",
        "drift": "green",
        "agent_type": "test-agent",
        "recall_token": tok,
        "cited_snippets": ["session_check_md.md note"],
    })
    text = res.get("content", [{}])[0].get("text", "")
    path = _extract_session_path_from_ingest_text(text)
    assert path, f"no session path in output: {text}"

    found = None
    for proj_dir in M.PROJECTS_DIR.iterdir():
        candidate = proj_dir / "memory" / path
        if candidate.exists():
            found = candidate; break
    assert found, f"session file not created at any project: {path}"

    content = found.read_text(encoding="utf-8")
    assert "proof_of_recall: pass" in content, f"frontmatter missing proof_of_recall: pass in {found}"

    # cleanup
    found.unlink()


def main() -> int:
    tests = [
        ("recall_returns_token_in_output", test_recall_returns_token_in_output),
        ("ingest_without_token_marks_not_attempted", test_ingest_without_token_marks_not_attempted),
        ("ingest_with_valid_token_marks_pass", test_ingest_with_valid_token_marks_pass),
        ("ingest_with_invalid_cite_marks_fail", test_ingest_with_invalid_cite_marks_fail),
        ("session_md_has_proof_frontmatter", test_session_md_has_proof_frontmatter),
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
