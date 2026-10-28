"""CLI plumbing: --cycle-id flag must reach engine.ship.ship(cycle_id=...).

Mocks cmd_code to capture the parsed argparse.Namespace · does not call
the real engine (which needs DATABASE_URL + network for audit).
"""
from unittest.mock import patch

from nautilus_cli.__main__ import main


@patch("nautilus_cli.__main__.cmd_code")
def test_cli_passes_cycle_id_when_given(mock_cmd):
    """User passes --cycle-id abc123 · args.cycle_id must equal 'abc123'."""
    mock_cmd.return_value = 0
    rc = main([
        "code", "demo task",
        "--cycle-id", "abc123",
        "--no-audit", "--no-repo-map",
        "--base-dir", ".",
    ])
    assert rc == 0
    mock_cmd.assert_called_once()
    args = mock_cmd.call_args[0][0]
    assert args.cycle_id == "abc123"


@patch("nautilus_cli.__main__.cmd_code")
def test_cli_cycle_id_default_none(mock_cmd):
    """No --cycle-id given · args.cycle_id must default to None (ship() then auto-generates)."""
    mock_cmd.return_value = 0
    rc = main([
        "code", "demo task",
        "--no-audit", "--no-repo-map",
        "--base-dir", ".",
    ])
    assert rc == 0
    args = mock_cmd.call_args[0][0]
    assert args.cycle_id is None
