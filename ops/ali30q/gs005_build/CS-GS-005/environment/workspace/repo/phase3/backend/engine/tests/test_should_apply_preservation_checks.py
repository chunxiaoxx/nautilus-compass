"""Test should_apply_preservation_checks · closes handoff Gap 1 part 3 (OR trigger).

Fires when:
  - task contains MINIMAL CHANGE phrase (existing should_apply_semantic_check), OR
  - any block target file already exists with > 50 LOC.
"""
from pathlib import Path

from engine.checks import should_apply_preservation_checks


def _write_lines(path: Path, n_lines: int) -> None:
    path.write_text("\n".join(f"x = {i}" for i in range(n_lines)) + "\n", encoding="utf-8")


def test_trigger_via_phrase(tmp_path):
    blocks = [{"path": "new.py", "content": "x = 1"}]
    task = "only add greet function · keep all other code identical"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is True


def test_trigger_via_existing_file_size_over_50(tmp_path):
    large = tmp_path / "large.py"
    _write_lines(large, 100)
    blocks = [{"path": "large.py", "content": "irrelevant"}]
    task = "add greet to large.py"  # no MINIMAL CHANGE phrase
    assert should_apply_preservation_checks(task, blocks, tmp_path) is True


def test_no_trigger_for_small_existing_file(tmp_path):
    small = tmp_path / "small.py"
    _write_lines(small, 30)
    blocks = [{"path": "small.py", "content": "irrelevant"}]
    task = "add greet to small.py"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is False


def test_no_trigger_for_new_file_no_phrase(tmp_path):
    blocks = [{"path": "brand_new.py", "content": "x = 1"}]
    task = "create new helper.py"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is False


def test_or_logic_phrase_and_size(tmp_path):
    large = tmp_path / "large.py"
    _write_lines(large, 100)
    blocks = [{"path": "large.py", "content": "irrelevant"}]
    task = "only add greet · keep all other code identical"
    assert should_apply_preservation_checks(task, blocks, tmp_path) is True
