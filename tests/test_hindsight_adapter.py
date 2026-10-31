"""Hindsight adapter 单测——transport 全注入,零网络(冻结前骨架即测,预注册 §一 纪律)。"""
import pytest

from hindsight_adapter import HindsightError, HindsightMemory, RECALL_TOP_K


def _sess(turns, ):
    return [{"role": r, "content": c} for r, c in turns]


def _fake_sess_to_text(session, max_chars=600, date=None):
    prefix = f"[{date}] " if date else ""
    parts = [f"[{t.get('role', '?')}] {t.get('content', '')}" for t in session]
    return (prefix + "\n".join(parts))[:max_chars]


class RecordingTransport:
    """记录调用并按脚本回放的假传输。"""

    def __init__(self, responses):
        self.calls = []
        self.responses = responses  # list of (响应 dict | Exception)

    def __call__(self, method, url, payload):
        self.calls.append((method, url, payload))
        r = self.responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_retain_corpus_逐会话同源内容():
    t = RecordingTransport([{"ok": True}] * 3)
    hm = HindsightMemory("longmemeval-s-test", "http://x", transport=t)
    sessions = [_sess([("user", "我叫王小明"), ("assistant", "好的")]),
                _sess([("user", "我家在杭州")]),
                _sess([("user", "我养了只猫叫咪咪")])]
    dates = ["2026-01-01", "2026-01-02", None]
    n = hm.retain_corpus(sessions, dates, session_to_text=_fake_sess_to_text)
    assert n == 3 and hm.retained == 3
    # 同源公平性:内容经同一 session_to_text 形态注入;时间锚经 context 透传
    assert "[user] 我叫王小明" in t.calls[0][2]["content"]
    assert t.calls[0][2]["context"] == "2026-01-01"
    assert "context" not in t.calls[2][2]  # 无日期不传 context


def test_recall_memory_解析与截断():
    t = RecordingTransport([{"results": [
        {"text": f"memory-{i}", "score": 1 - i * 0.1} for i in range(8)]}])
    hm = HindsightMemory("b", "http://x", transport=t)
    out = hm.recall_memory("user 的猫叫什么", top_k=5)
    assert len(out) == 5  # 截到 top_k
    assert out[0]["text"] == "memory-0"
    assert t.calls[0][2]["top_k"] == RECALL_TOP_K


def test_recall_空结果是数据不是错误():
    t = RecordingTransport([{"results": []}])
    hm = HindsightMemory("b", "http://x", transport=t)
    assert hm.recall_memory("q") == []  # 照报 0 分路径


def test_recall_缺results键_显式错误():
    t = RecordingTransport([{"unexpected": 1}])
    hm = HindsightMemory("b", "http://x", transport=t)
    with pytest.raises(HindsightError, match="results"):
        hm.recall_memory("q")


def test_recall_条目缺文本_显式错误():
    t = RecordingTransport([{"results": [{"score": 0.9}]}])
    hm = HindsightMemory("b", "http://x", transport=t)
    with pytest.raises(HindsightError, match="text/content"):
        hm.recall_memory("q")


def test_传输失败_转HindsightError不静默():
    import urllib.request
    t = RecordingTransport([urllib.request.URLError("conn refused")])
    hm = HindsightMemory("b", "http://x", transport=t)
    with pytest.raises(HindsightError, match="failed"):
        hm.recall_memory("q")


def test_伪会话视图兼容top_sessions契约():
    out = HindsightMemory.to_pseudo_sessions([{"text": "事实A"}, {"text": "事实B"}])
    assert out[0] == [{"role": "memory", "content": "事实A"}]  # 伪会话=单turn列表
    rendered = _fake_sess_to_text(out[0])
    assert rendered == "[memory] 事实A"  # build_context 可直接消费


def test_retain_corpus_缺同源函数_拒绝():
    hm = HindsightMemory("b", "http://x", transport=RecordingTransport([]))
    with pytest.raises(HindsightError, match="session_to_text"):
        hm.retain_corpus([_sess([("user", "x")])])
