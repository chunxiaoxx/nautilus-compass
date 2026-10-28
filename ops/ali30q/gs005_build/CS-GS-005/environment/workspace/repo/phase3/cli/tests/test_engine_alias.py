"""CLI engine alias: `nautilus engine <task>` invokes cmd_code (alias for `code`).

Path B Week 1 Task C3 binding-DONE follow-through. HANDOFF #018 plan §C3 spec
called for `nautilus engine <task>` subcommand. Existing CLI v0 (5/26 ship) has
`nautilus code <task>` doing exactly engine.ship invocation. Per anchor #5
不重复造轮子, this PR adds `engine` as argparse alias (not rewrite) so both
typings work and the plan-spec naming is honored.

Backward compat: `nautilus code <task>` continues to work for existing users.
"""
from unittest.mock import patch

from nautilus_cli.__main__ import main


@patch("nautilus_cli.__main__.cmd_code")
def test_engine_alias_invokes_cmd_code(mock_cmd):
    """`nautilus engine <task>` is alias for `code` subcommand · invokes cmd_code."""
    mock_cmd.return_value = 0
    rc = main([
        "engine", "demo task",
        "--no-audit", "--no-repo-map",
        "--base-dir", ".",
    ])
    assert rc == 0
    mock_cmd.assert_called_once()
    args = mock_cmd.call_args[0][0]
    assert args.task == "demo task"
    assert args.base_dir == "."
    assert args.no_audit is True
    assert args.no_repo_map is True


@patch("nautilus_cli.__main__.cmd_code")
def test_code_subcommand_backward_compat(mock_cmd):
    """`nautilus code <task>` still works after engine alias added · backward compat."""
    mock_cmd.return_value = 0
    rc = main([
        "code", "demo task",
        "--no-audit", "--no-repo-map",
        "--base-dir", ".",
    ])
    assert rc == 0
    mock_cmd.assert_called_once()
    args = mock_cmd.call_args[0][0]
    assert args.task == "demo task"


@patch("nautilus_cli.__main__.cmd_code")
def test_engine_alias_accepts_all_code_flags(mock_cmd):
    """Engine alias inherits all code flags · `--cycle-id`, `--apply`, `--max-retries` etc."""
    mock_cmd.return_value = 0
    rc = main([
        "engine", "implement feature X",
        "--cycle-id", "test_cycle_001",
        "--max-retries", "2",
        "--no-audit", "--no-repo-map",
        "--base-dir", ".",
    ])
    assert rc == 0
    args = mock_cmd.call_args[0][0]
    assert args.cycle_id == "test_cycle_001"
    assert args.max_retries == 2
