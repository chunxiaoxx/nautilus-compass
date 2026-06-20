import compass_http_v09 as srv


def test_daemon_score_parses(monkeypatch):
    class FakeSock:
        def __init__(s): s.sent = b""
        def settimeout(s, t): pass
        def connect(s, a): pass
        def sendall(s, b): s.sent += b
        def recv(s, n): return b'{"ok":true,"scores":[0.9,0.1]}\n'
        def close(s): pass
    monkeypatch.setattr(srv.socket, "socket", lambda *a, **k: FakeSock())
    assert srv._daemon_score("q", ["a", "b"]) == [0.9, 0.1]


def test_daemon_score_unreachable_returns_none(monkeypatch):
    def boom(*a, **k): raise ConnectionError("down")
    monkeypatch.setattr(srv.socket, "socket", boom)
    assert srv._daemon_score("q", ["a"]) is None


def test_daemon_score_empty_candidates_returns_none():
    assert srv._daemon_score("q", []) is None
