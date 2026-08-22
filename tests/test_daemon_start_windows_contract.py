from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "daemon_start.ps1"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_windows_launcher_prefers_explicit_compass_python() -> None:
    text = _script()

    assert "$env:COMPASS_PYTHON" in text
    assert "$env:USERPROFILE" in text
    assert '".venvs\\nautilus-compass\\Scripts\\python.exe"' in text
    assert "Resolve-Path" in text
    assert "Get-Command python" in text


def test_windows_launcher_preflights_model_dependencies() -> None:
    text = _script()

    assert "import torch; import sentence_transformers" in text
    assert "dependency preflight failed" in text


def test_windows_launcher_does_not_compose_commands_through_cmd() -> None:
    text = _script().lower()

    assert "cmd /c" not in text
    assert "cmd.exe" not in text
    assert "start-process" in text
    assert "-windowstyle hidden" in text


def test_windows_launcher_requires_functional_doctor_not_only_ping() -> None:
    text = _script()

    assert "doctor.py" in text
    assert "--json" in text
    assert "daemon pinged but functional doctor failed" in text


def test_windows_launcher_cleans_up_only_the_process_it_started() -> None:
    text = _script()

    assert "Stop-StartedCompassProcess" in text
    assert "Get-Process -Id $Process.Id" in text
    assert "$Running.StartTime -eq $Process.StartTime" in text
    assert "Stop-Process -Id $Process.Id" in text


def test_windows_launcher_quotes_daemon_path_for_start_process() -> None:
    text = _script()

    assert "$DaemonArgument = '\"' + $DaemonPath + '\"'" in text
    assert "-ArgumentList @($DaemonArgument)" in text
