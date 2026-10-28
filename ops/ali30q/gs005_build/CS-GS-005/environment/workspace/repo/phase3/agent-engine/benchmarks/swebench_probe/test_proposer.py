"""Tests for the soul-fitness evolution proposer (Probe 3 Task 2).

The proposer is the variation half of variation+selection: it reads the current
agent prompt + a sample of its failures and proposes one improved prompt. Pure
framing + extraction (no LLM here — the real M3 call is injected at run time).
"""
from proposer import build_proposer_prompt, extract_proposed_prompt


def test_prompt_includes_current_and_failures():
    cur = "You are a coding agent. Fix the issue."
    fails = [
        {"instance_id": "x-1", "problem_statement": "TypeError in foo", "error": "submitted empty patch"},
        {"instance_id": "x-2", "problem_statement": "off-by-one in bar", "error": "tests still fail"},
    ]
    p = build_proposer_prompt(cur, fails)
    assert cur in p                          # current prompt is shown verbatim
    assert "x-1" in p and "x-2" in p         # failures are surfaced
    assert "TypeError in foo" in p
    assert "submitted empty patch" in p
    # asks for a single improved prompt in a fenced block
    assert "```" in p


def test_extract_pulls_fenced_block():
    out = "Sure, here is an improved prompt:\n```text\nNEW PROMPT BODY here\n```\nDone."
    assert extract_proposed_prompt(out) == "NEW PROMPT BODY here"


def test_extract_prefers_last_fence():
    out = "```\nfirst\n```\nthen\n```\nsecond\n```"
    assert extract_proposed_prompt(out) == "second"


def test_extract_empty_on_no_fence():
    assert extract_proposed_prompt("no code block at all") == ""


def test_build_caps_failures_sample():
    fails = [{"instance_id": f"x-{i}", "problem_statement": "p", "error": "e"} for i in range(20)]
    p = build_proposer_prompt("cur", fails, max_failures=3)
    assert p.count("instance_id") <= 3 or sum(1 for i in range(20) if f"x-{i}" in p) <= 3
