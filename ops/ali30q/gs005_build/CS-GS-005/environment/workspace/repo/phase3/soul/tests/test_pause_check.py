from soul import pause_check


def test_paused_when_file_exists(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    pf.write_text("paused")
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    assert pause_check.is_paused() is True


def test_not_paused_when_absent(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    assert pause_check.is_paused() is False


def test_engage_then_lift(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    pause_check.engage_pause("manual stop")
    assert pause_check.is_paused() is True
    assert pf.read_text() == "manual stop"
    pause_check.lift_pause()
    assert pause_check.is_paused() is False


# --- 熔断分层(9/25 用户批):breaker 自动熔断只断 ship 路径,人工 pause 全停 ---


def test_pause_origin_breaker_keeps_letters_live(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    pf.write_text("circuit breaker · 5 consecutive failures · last=cyc9")
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    assert pause_check.pause_origin() == "breaker"
    assert pause_check.ship_blocked() is True
    assert pause_check.letters_blocked() is False


def test_pause_origin_manual_blocks_everything(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    pf.write_text("manual stop")
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    assert pause_check.pause_origin() == "manual"
    assert pause_check.ship_blocked() is True
    assert pause_check.letters_blocked() is True


def test_pause_origin_none_when_absent(tmp_path, monkeypatch):
    pf = tmp_path / ".soul-pause"
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    assert pause_check.pause_origin() is None
    assert pause_check.ship_blocked() is False
    assert pause_check.letters_blocked() is False


def test_pause_origin_unreadable_treated_manual(tmp_path, monkeypatch):
    """ fail-safe 向人工侧:文件存在但读不出 → 按人工 pause 全停(人监门至上)。"""
    pf = tmp_path / ".soul-pause"
    pf.write_text("x")
    monkeypatch.setattr(pause_check, "PAUSE_FILE", pf)
    monkeypatch.setattr(type(pf), "read_text",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("boom")))
    assert pause_check.pause_origin() == "manual"
    assert pause_check.letters_blocked() is True
