"""T5 · recall UserPromptSubmit 节流闸测试(R432 重做 · 2026-10-09)。

R432 发现链:①注入源 hook.sh→recall.py ②stdin JSON 含 session_id(节流键)
③early return 多点致 stdout 捕获地狱 → 重做方案:节流闸前置 main()·窗口内零输出
(不捕获/不重定向 stdout)·fail-open(节流器自身异常绝不阻断注入)。

判据:
- 首次注入;窗口内跳过;窗口过后再注入并刷新时间戳
- 无 session_id / 状态文件损坏 / window=0 → 全部 fail-open(注入)
- session_id sanitize(路径逃逸防护);状态 TTL 48h 清理
- stdin 单次读缓存(main 闸与 read_user_prompt_from_stdin 共享一次 read)
"""
import json
import os
import sys
from pathlib import Path

import pytest

import recall

NOW = 1_760_000_000.0  # 固定时钟(绝对值不重要,只要求单调)


@pytest.fixture()
def state_dir(tmp_path):
    return tmp_path / "throttle"


# ---- throttle_check 纯逻辑 ----

def test_first_call_injects(state_dir):
    skip, why = recall.throttle_check("sess-a", now=NOW, state_dir=state_dir, window_min=10)
    assert skip is False
    assert (state_dir / "sess-a.json").exists()


def test_within_window_skips(state_dir):
    recall.throttle_check("sess-a", now=NOW, state_dir=state_dir, window_min=10)
    skip, why = recall.throttle_check("sess-a", now=NOW + 60, state_dir=state_dir, window_min=10)
    assert skip is True
    assert why  # 带原因(剩余秒数等)


def test_after_window_injects_and_refreshes(state_dir):
    recall.throttle_check("sess-a", now=NOW, state_dir=state_dir, window_min=10)
    skip, _ = recall.throttle_check("sess-a", now=NOW + 11 * 60, state_dir=state_dir, window_min=10)
    assert skip is False
    # 时间戳已刷新 → 紧接着又在窗口内
    skip2, _ = recall.throttle_check("sess-a", now=NOW + 12 * 60, state_dir=state_dir, window_min=10)
    assert skip2 is True


def test_no_session_id_fail_open(state_dir):
    for bad in (None, "", 123):
        skip, _ = recall.throttle_check(bad, now=NOW, state_dir=state_dir, window_min=10)
        assert skip is False


def test_corrupt_state_fail_open(state_dir):
    state_dir.mkdir(parents=True)
    (state_dir / "sess-a.json").write_text("not json{", encoding="utf-8")
    skip, _ = recall.throttle_check("sess-a", now=NOW, state_dir=state_dir, window_min=10)
    assert skip is False  # 宁可多注入,不可断注入


def test_window_zero_disables(state_dir):
    recall.throttle_check("sess-a", now=NOW, state_dir=state_dir, window_min=0)
    skip, _ = recall.throttle_check("sess-a", now=NOW + 1, state_dir=state_dir, window_min=0)
    assert skip is False


def test_session_isolation(state_dir):
    recall.throttle_check("sess-a", now=NOW, state_dir=state_dir, window_min=10)
    skip, _ = recall.throttle_check("sess-b", now=NOW + 1, state_dir=state_dir, window_min=10)
    assert skip is False


def test_session_id_sanitized_no_escape(state_dir):
    weird = "../../evil && rm -rf x" * 10
    skip, _ = recall.throttle_check(weird, now=NOW, state_dir=state_dir, window_min=10)
    assert skip is False
    files = list(state_dir.glob("*.json"))
    assert len(files) == 1
    assert files[0].parent == state_dir  # 无路径逃逸
    assert len(files[0].stem) <= 80


def test_ttl_cleanup(state_dir):
    state_dir.mkdir(parents=True)
    old = state_dir / "old-sess.json"
    old.write_text('{"ts": 1}', encoding="utf-8")
    old_ts = NOW - 49 * 3600
    os.utime(old, (old_ts, old_ts))
    recall.throttle_check("sess-new", now=NOW, state_dir=state_dir, window_min=10)
    assert not old.exists()
    assert (state_dir / "sess-new.json").exists()


def test_state_file_content(state_dir):
    recall.throttle_check("sess-a", now=NOW, state_dir=state_dir, window_min=10)
    data = json.loads((state_dir / "sess-a.json").read_text(encoding="utf-8"))
    assert data["ts"] == NOW


# ---- stdin 单次读缓存 ----

class _FakeBuf:
    def __init__(self, payload: bytes):
        self._payload = payload
        self.n_reads = 0

    def read(self):
        self.n_reads += 1
        return self._payload


class _FakeStdin:
    def __init__(self, payload: bytes):
        self.buffer = _FakeBuf(payload)

    def isatty(self):
        return False


def test_stdin_json_cached_single_read(monkeypatch):
    payload = json.dumps({"session_id": "s-1", "prompt": "你好 world"}).encode("utf-8")
    fake = _FakeStdin(payload)
    monkeypatch.setattr(recall, "_STDIN_JSON_CACHE", None)
    monkeypatch.setattr(sys, "stdin", fake)

    p1 = recall.read_user_prompt_from_stdin()
    p2 = recall.read_user_prompt_from_stdin()
    assert p1 == "你好 world"
    assert p2 == "你好 world"
    assert fake.buffer.n_reads == 1  # 只读一次
    assert recall._read_stdin_json_cached().get("session_id") == "s-1"


def test_stdin_cache_bad_json(monkeypatch):
    fake = _FakeStdin(b"\xff\xfe not json")
    monkeypatch.setattr(recall, "_STDIN_JSON_CACHE", None)
    monkeypatch.setattr(sys, "stdin", fake)
    assert recall._read_stdin_json_cached() == {}
    assert recall.read_user_prompt_from_stdin() == ""
