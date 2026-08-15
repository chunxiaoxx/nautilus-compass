from pathlib import Path


ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "daemon_start.ps1"


def _script() -> str:
    return SCRIPT.read_text(encoding="utf-8")


def test_windows_launcher_prefers_explicit_compass_python() -> None:
    text = _script()

    assert "$env:COMPASS_PYTHON" in text
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
