"""cloud_ingest must authenticate without putting a JWT in the repository or argv."""

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("cloud_ingest", ROOT / "cloud_ingest.py")
cloud_ingest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cloud_ingest)


def test_ingest_uses_header_file_and_explicit_project(tmp_path, monkeypatch):
    session = tmp_path / "session_20261123_test.md"
    session.write_text("---\nname: test\n---\n\nA verified cloud ingest payload.", encoding="utf-8")
    captured = {}

    def fake_run(cmd, input, capture_output, timeout):
        captured["cmd"] = cmd
        captured["payload"] = json.loads(input.decode("utf-8"))
        return SimpleNamespace(returncode=0, stdout=b'{"ok": true}', stderr=b"")

    monkeypatch.setattr(cloud_ingest.subprocess, "run", fake_run)
    monkeypatch.setattr(cloud_ingest, "_already_pushed", lambda _: False)
    monkeypatch.setattr(cloud_ingest, "_record_push", lambda *_: None)
    monkeypatch.setenv("COMPASS_V14_INGEST_PROJECT", "C--Users-chunx")
    monkeypatch.setattr(
        cloud_ingest,
        "V14_AUTH_HEADER_FILE",
        "$HOME/.config/compass/v14_test_auth_header",
    )

    result = cloud_ingest.ingest_session_to_cloud(session)

    assert result == {"ok": True}
    assert captured["payload"]["project"] == "C--Users-chunx"
    remote_command = captured["cmd"][-1]
    assert "-H @$HOME/.config/compass/v14_test_auth_header" in remote_command
    assert (
        "python3 $HOME/compass/ops/v14_auth_header_refresh.py "
        "--header-file $HOME/.config/compass/v14_test_auth_header && "
    ) in remote_command
    assert "X-User-ID" not in remote_command
    assert "X-Tenant-ID" not in remote_command
    assert "Bearer " not in remote_command


def test_ingest_project_has_no_ambiguous_server_side_default(monkeypatch):
    monkeypatch.delenv("COMPASS_V14_INGEST_PROJECT", raising=False)

    assert cloud_ingest._ingest_project() == "C--Users-chunx"


def test_token_refresher_reuses_valid_cache_and_refreshes_missing_token(tmp_path, monkeypatch, capsys):
    import base64
    import io
    import time

    spec = importlib.util.spec_from_file_location(
        "v14_auth_header_refresh", ROOT / "ops" / "v14_auth_header_refresh.py"
    )
    refresher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(refresher)

    def token(exp):
        payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).rstrip(b"=")
        return "e30." + payload.decode() + ".signature"

    now = time.time()
    credentials = tmp_path / "credentials.json"
    credentials.write_text(json.dumps({"email": "service@example.invalid", "passphrase": "secret"}))
    header = tmp_path / "auth_header"
    fresh_token = token(now + 86400)
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request)
        return io.BytesIO(json.dumps({"token": fresh_token}).encode())

    monkeypatch.setattr(refresher.urllib.request, "urlopen", fake_urlopen)
    assert refresher.refresh_if_expiring(credentials, header, "http://127.0.0.1:8770", now=now) is True
    assert header.read_text() == f"Authorization: Bearer {fresh_token}\n"
    assert refresher.refresh_if_expiring(credentials, header, "http://127.0.0.1:8770", now=now) is False
    assert len(calls) == 1
    assert json.loads(calls[0].data)["passphrase"] == "secret"
    assert capsys.readouterr().out == ""
