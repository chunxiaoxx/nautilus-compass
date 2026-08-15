"""nautilus-compass umbrella CLI dispatcher · TDD.

cli.py backs the pyproject console-script
`nautilus-compass = nautilus_compass.cli:main`. Before it, that entry
pointed at a non-existent module and the installed `nautilus-compass`
command crashed at import (Show HN material flagged "CLI command broken
in current PATH · noted as separate fix"). The 5 compass-* subcommand
modules already exist and read sys.argv[1:] themselves; the dispatcher
routes `nautilus-compass <sub> [args]` to them and restores sys.argv.
"""

import re
import sys
import types

from cli import main


def test_no_args_prints_usage_returns_0(capsys):
    rc = main([])
    out = capsys.readouterr().out
    assert rc == 0
    assert "nautilus-compass" in out
    assert "drift-history" in out


def test_help_lists_all_subcommands(capsys):
    rc = main(["--help"])
    out = capsys.readouterr().out
    assert rc == 0
    for sub in ("doctor", "drift-history", "session-search", "session-writer", "mcp", "a2a"):
        assert sub in out


def test_version_flag(capsys):
    rc = main(["--version"])
    out = capsys.readouterr().out
    assert rc == 0
    assert re.search(r"\d+\.\d+", out)


def test_unknown_subcommand_returns_2_stderr(capsys):
    rc = main(["bogus-cmd"])
    err = capsys.readouterr().err
    assert rc == 2
    assert "bogus-cmd" in err


def test_dispatch_delegates_and_restores_argv(monkeypatch):
    calls = {}
    fake = types.ModuleType("drift_history")

    def fake_main():
        calls["argv"] = list(sys.argv)
        return 0

    fake.main = fake_main
    monkeypatch.setitem(sys.modules, "drift_history", fake)
    monkeypatch.setitem(sys.modules, "nautilus_compass.drift_history", fake)

    saved = list(sys.argv)
    rc = main(["drift-history", "--last", "7d"])
    assert rc == 0
    # subcommand saw only its own args after argv[0]
    assert calls["argv"][1:] == ["--last", "7d"]
    # dispatcher restored sys.argv
    assert sys.argv == saved


def test_dispatch_propagates_nonzero_exit(monkeypatch):
    fake = types.ModuleType("session_search")
    fake.main = lambda: 3
    monkeypatch.setitem(sys.modules, "session_search", fake)
    monkeypatch.setitem(sys.modules, "nautilus_compass.session_search", fake)
    assert main(["session-search", "query"]) == 3


def test_dispatches_doctor_and_propagates_status(monkeypatch):
    calls = {}
    fake = types.ModuleType("doctor")

    def fake_main():
        calls["argv"] = list(sys.argv)
        return 1

    fake.main = fake_main
    monkeypatch.setitem(sys.modules, "doctor", fake)
    monkeypatch.setitem(sys.modules, "nautilus_compass.doctor", fake)

    assert main(["doctor", "--json"]) == 1
    assert calls["argv"][1:] == ["--json"]
