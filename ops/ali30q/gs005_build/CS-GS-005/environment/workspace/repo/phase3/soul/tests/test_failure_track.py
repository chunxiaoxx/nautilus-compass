import json

from soul import failure_track


def test_consecutive_failures_engage_pause(tmp_path, monkeypatch):
    state = tmp_path / "fail.json"
    pause = tmp_path / ".soul-pause"
    monkeypatch.setattr(failure_track, "FAILURE_STATE", state)
    monkeypatch.setattr(failure_track, "MAX_CONSECUTIVE_FAILURES", 3)
    monkeypatch.setattr(failure_track.pause_check, "PAUSE_FILE", pause)
    monkeypatch.setattr(failure_track, "_alert", lambda msg: None)
    for _ in range(2):
        failure_track.record_failure("cyc")
    assert not pause.exists()
    failure_track.record_failure("cyc")  # 3rd → trip
    assert pause.exists()


def test_success_resets(tmp_path, monkeypatch):
    state = tmp_path / "fail.json"
    monkeypatch.setattr(failure_track, "FAILURE_STATE", state)
    failure_track.record_failure("c")
    failure_track.record_success()
    assert json.loads(state.read_text())["consecutive"] == 0


def test_below_cap_no_pause_no_alert(tmp_path, monkeypatch):
    state = tmp_path / "fail.json"
    pause = tmp_path / ".soul-pause"
    alerts = []
    monkeypatch.setattr(failure_track, "FAILURE_STATE", state)
    monkeypatch.setattr(failure_track, "MAX_CONSECUTIVE_FAILURES", 5)
    monkeypatch.setattr(failure_track.pause_check, "PAUSE_FILE", pause)
    monkeypatch.setattr(failure_track, "_alert", lambda msg: alerts.append(msg))
    n = failure_track.record_failure("c1")
    assert n == 1
    assert not pause.exists()
    assert alerts == []


def test_trip_sends_distress_letter(tmp_path, monkeypatch):
    """呼救通道(9/25):熔断瞬间除 GitHub issue 外必投 org_mailbox 呼救函——
    issue 无人盯(02:08 熔断 17h 无人知实证),mailbox 是值守轮必扫通道。"""
    state = tmp_path / "fail.json"
    pause = tmp_path / ".soul-pause"
    distress = []
    monkeypatch.setattr(failure_track, "FAILURE_STATE", state)
    monkeypatch.setattr(failure_track, "MAX_CONSECUTIVE_FAILURES", 2)
    monkeypatch.setattr(failure_track.pause_check, "PAUSE_FILE", pause)
    monkeypatch.setattr(failure_track, "_alert", lambda msg: None)
    monkeypatch.setattr(failure_track, "_distress_letter", lambda msg: distress.append(msg))
    failure_track.record_failure("cyc-a")
    assert distress == []  # below cap → no distress
    failure_track.record_failure("cyc-b")  # trip
    assert len(distress) == 1
    assert "cyc-b" in distress[0]
