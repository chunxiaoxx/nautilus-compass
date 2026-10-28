"""_extract_text contract tests (2026-09-10, found via soul proposal queue).

Complex tasks flip MiniMax-M3 into thinking mode; with the old 4096-token
budget the thinking alone exhausted it, the response contained ONLY a
ThinkingBlock, and the old str() fallback returned 18k chars of thinking as
the "answer" — downstream file-block parsing then found zero files
(obscured twice on the proposal queue with empty check results).
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from agent_engine.llm.client import _extract_text


class _Block:
    def __init__(self, type=None, text=None, thinking=None, signature=None):
        self.type = type
        if text is not None:
            self.text = text
        if thinking is not None:
            self.thinking = thinking
        if signature is not None:
            self.signature = signature


class _Resp:
    def __init__(self, blocks):
        self.content = blocks


def test_text_block_returned():
    r = _Resp([_Block(type="text", text="```python:x.py\npass\n```")])
    assert _extract_text(r).startswith("```python")


def test_thinking_then_text_returns_text():
    r = _Resp([_Block(type="thinking", thinking="let me think", signature="sig"),
               _Block(type="text", text="the answer")])
    assert _extract_text(r) == "the answer"


def test_thinking_only_raises_instead_of_str_thinking():
    """The old str() fallback returned the thinking text as the answer."""
    r = _Resp([_Block(type="thinking", thinking="18k chars of reasoning", signature="sig")])
    with pytest.raises(ValueError, match="thinking"):
        _extract_text(r)


def test_untyped_thinking_block_excluded_by_attrs():
    """MiniMax compat layer may omit .type; attr-based exclusion must still work."""
    r = _Resp([_Block(thinking="reasoning", signature="sig"),
               _Block(type="text", text="final")])
    assert _extract_text(r) == "final"
