"""TDD basic tests for NautilusEngine cycle 1 · pure unit · no real LLM call."""
from unittest.mock import MagicMock

import pytest

from engine.nautilus_engine import NautilusEngine


def test_engine_instantiates_with_mock_llm():
    mock_llm = MagicMock()
    engine = NautilusEngine(llm_client=mock_llm, dry_run=True)
    assert engine.dry_run is True
    assert engine.llm is mock_llm


def test_generate_calls_llm_chat():
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "generated text"
    engine = NautilusEngine(llm_client=mock_llm)
    result = engine.generate("write hello")
    assert result == "generated text"
    mock_llm.chat.assert_called_once()


def test_generate_passes_context_into_prompt():
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "ok"
    engine = NautilusEngine(llm_client=mock_llm)
    engine.generate("task X", context="some context Y")
    args, kwargs = mock_llm.chat.call_args
    sent_prompt = args[0] if args else kwargs.get("prompt", "")
    assert "some context Y" in sent_prompt
    assert "task X" in sent_prompt


def test_parse_file_blocks_single():
    engine = NautilusEngine(llm_client=MagicMock())
    text = 'Preamble.\n\n```python:hello.py\nprint("hello")\n```\n\nEnd.'
    blocks = engine.parse_file_blocks(text)
    assert len(blocks) == 1
    assert blocks[0]["path"] == "hello.py"
    assert blocks[0]["content"] == 'print("hello")'
    assert blocks[0]["lang"] == "python"


def test_parse_file_blocks_multiple_languages():
    engine = NautilusEngine(llm_client=MagicMock())
    text = (
        "```python:a.py\nx = 1\n```\n\n"
        "between\n\n"
        "```typescript:src/b.ts\nconst x = 1;\n```\n"
    )
    blocks = engine.parse_file_blocks(text)
    assert len(blocks) == 2
    assert blocks[0]["path"] == "a.py"
    assert blocks[1]["path"] == "src/b.ts"
    assert blocks[1]["lang"] == "typescript"


def test_parse_file_blocks_no_match_returns_empty():
    engine = NautilusEngine(llm_client=MagicMock())
    assert engine.parse_file_blocks("Just prose, no code blocks.") == []


def test_write_file_dry_run_does_not_write(tmp_path):
    engine = NautilusEngine(
        llm_client=MagicMock(), dry_run=True, base_dir=str(tmp_path)
    )
    result = engine.write_file("out.py", "x = 1")
    assert result["written"] is False
    assert result["dry_run"] is True
    assert "preview" in result
    assert not (tmp_path / "out.py").exists()


def test_write_file_apply_writes(tmp_path):
    engine = NautilusEngine(
        llm_client=MagicMock(), dry_run=False, base_dir=str(tmp_path)
    )
    result = engine.write_file("out.py", "x = 1\n")
    assert result["written"] is True
    target = tmp_path / "out.py"
    assert target.exists()
    assert target.read_text(encoding="utf-8") == "x = 1\n"


def test_write_file_creates_subdirs(tmp_path):
    engine = NautilusEngine(
        llm_client=MagicMock(), dry_run=False, base_dir=str(tmp_path)
    )
    result = engine.write_file("sub/dir/out.py", "x = 1")
    assert result["written"] is True
    assert (tmp_path / "sub" / "dir" / "out.py").exists()


def test_write_file_rejects_path_escape(tmp_path):
    engine = NautilusEngine(
        llm_client=MagicMock(), dry_run=False, base_dir=str(tmp_path)
    )
    result = engine.write_file("../escape.py", "x = 1")
    assert result["written"] is False
    assert result.get("error") == "path_escape"


def test_run_end_to_end_dry_run(tmp_path):
    mock_llm = MagicMock()
    mock_llm.chat.return_value = '```python:out.py\nprint("hi")\n```'
    engine = NautilusEngine(
        llm_client=mock_llm, dry_run=True, base_dir=str(tmp_path)
    )
    summary = engine.run("write a hello script to out.py")
    assert summary["files_planned"] == 1
    assert summary["files_written"] == 0
    assert summary["dry_run"] is True
    assert not (tmp_path / "out.py").exists()


def test_run_end_to_end_apply(tmp_path):
    mock_llm = MagicMock()
    mock_llm.chat.return_value = '```python:out.py\nprint("hi")\n```'
    engine = NautilusEngine(
        llm_client=mock_llm, dry_run=False, base_dir=str(tmp_path)
    )
    summary = engine.run("write out.py")
    assert summary["files_planned"] == 1
    assert summary["files_written"] == 1
    assert (tmp_path / "out.py").exists()


# ---------- cycle 2 · RepoMap integration ----------

def test_engine_uses_repo_map_when_no_explicit_context(tmp_path):
    from engine.repo_map import RepoMap

    (tmp_path / "auth.py").write_text(
        "class AuthService:\n    def verify(self, token: str) -> bool:\n        return True\n"
    )
    rm = RepoMap(str(tmp_path))
    rm.scan()

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "ok"
    engine = NautilusEngine(llm_client=mock_llm, repo_map=rm, base_dir=str(tmp_path))
    engine.generate("write a new AuthService.verify variant")

    sent_prompt = mock_llm.chat.call_args[0][0]
    assert "AuthService" in sent_prompt
    assert "verify" in sent_prompt
    assert "Repository Map" in sent_prompt


def test_engine_explicit_context_overrides_repo_map(tmp_path):
    from engine.repo_map import RepoMap

    (tmp_path / "auth.py").write_text("class AuthService:\n    pass\n")
    rm = RepoMap(str(tmp_path))
    rm.scan()

    mock_llm = MagicMock()
    mock_llm.chat.return_value = "ok"
    engine = NautilusEngine(llm_client=mock_llm, repo_map=rm, base_dir=str(tmp_path))
    engine.generate("task", context="EXPLICIT_CONTEXT_MARKER")

    sent_prompt = mock_llm.chat.call_args[0][0]
    assert "EXPLICIT_CONTEXT_MARKER" in sent_prompt
    # Explicit context wins · RepoMap not consulted
    assert "Repository Map" not in sent_prompt


# ---------- cycle 12 · MINIMAL CHANGE MODE prompt constraint ----------

def test_default_system_prompt_has_minimal_change_mode():
    """Regression guard for cycle 12 ship · Layer 5 BUDDHA-A.1+A.2 over-rewrite gap.

    The engine LLM had a pattern of either over-shipping (whole file rewrite when
    only a docstring add was asked) or under-shipping (0 files when over-constrained).
    Cycle 12 adds explicit MINIMAL CHANGE MODE directives to the system prompt.
    This test asserts the directives are present so future drift doesn't silently
    re-open the gap.
    """
    from engine.nautilus_engine import DEFAULT_SYSTEM_PROMPT
    assert "MINIMAL CHANGE MODE" in DEFAULT_SYSTEM_PROMPT
    assert "preserve ALL other lines" in DEFAULT_SYSTEM_PROMPT
    assert "change LESS rather than MORE" in DEFAULT_SYSTEM_PROMPT
    # The trigger phrases the LLM should recognize:
    assert "keep ALL other code identical" in DEFAULT_SYSTEM_PROMPT
    assert "only add" in DEFAULT_SYSTEM_PROMPT
    assert "minimal diff" in DEFAULT_SYSTEM_PROMPT


def test_default_system_prompt_has_minimal_change_few_shot_example():
    """Cycle 14 strengthens cycle 12 P0 with a concrete before/after exemplar.

    Cycle 12 P2 verification (LAYER5-CYCLE12-P2-VERIFY) showed the textual
    MINIMAL CHANGE MODE constraint alone did not change LLM behavior on MiniMax M2.7
    for the BUDDHA-A.1 task class. Cycle 14 adds a small concrete example showing
    correct minimal-change output AND a list of WRONG outputs (under-ship,
    over-rewrite, drop-unrelated-imports, rename, add-unrequested-guards).
    """
    from engine.nautilus_engine import DEFAULT_SYSTEM_PROMPT
    assert "EXAMPLE · MINIMAL CHANGE" in DEFAULT_SYSTEM_PROMPT
    assert "count.py" in DEFAULT_SYSTEM_PROMPT
    assert "WRONG outputs to avoid" in DEFAULT_SYSTEM_PROMPT
    # Each WRONG pattern must be enumerated so the LLM learns the failure modes:
    assert "under-shipping" in DEFAULT_SYSTEM_PROMPT
    assert "over-rewriting" in DEFAULT_SYSTEM_PROMPT
    assert "Renaming" in DEFAULT_SYSTEM_PROMPT
