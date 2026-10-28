"""ZERO→派单升级:派单函投 org mailbox(P0.5 · 2026-08-29 · SLA 2h 版)。

dry-run v1 只写 dispatch_recommendations.jsonl+telegram 建议;v1.1 = ZERO 判定轮
同时给 owner 框(to=v5)投 mailbox 工作单(deadline=now+2h,幂等 trace=zero-dispatch-<run_id>)。
纯函数+HTTP mock,不触网。
"""
import importlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

BACKEND = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BACKEND))

supervisor = importlib.import_module("ops.supervisor")


class _Resp:
    def __init__(self):
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_post_dispatch_mail_payload():
    """投递 payload:to=v5/from=platform/trace 带 run_id/body 含指令+2h deadline。"""
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["payload"] = json.loads(req.data.decode())
        return _Resp()

    before = datetime.now(timezone.utc)
    with patch.object(supervisor.urllib.request, "urlopen", fake_urlopen):
        ok = supervisor.post_dispatch_mail("YIELDED", "20260830-0030", {"commits_48h": 3})

    assert ok is True
    assert captured["url"].endswith("/api/platform/org/mailbox")
    p = captured["payload"]
    assert p["to_agent"] == "v5"
    assert p["from_agent"] == "platform"
    assert p["trace_id"] == "zero-dispatch-20260830-0030"
    assert "资源让位" in p["body"] and "commits_48h" in p["body"]
    dl = datetime.fromisoformat(p["deadline"])
    assert timedelta(hours=1, minutes=55) < dl - before <= timedelta(hours=2, minutes=5)


def test_post_dispatch_mail_fail_soft():
    """网络失败返回 False 不抛(mailbox 端点挂了不拖垮监督主流程)。"""
    def boom(req, timeout=None):
        raise OSError("conn reset")

    with patch.object(supervisor.urllib.request, "urlopen", boom):
        assert supervisor.post_dispatch_mail("CRASHED", "20260830-0100", {}) is False


def test_on_zero_dryrun_posts_mail_once():
    """_on_zero_dryrun 首轮 ZERO:写 jsonl 且投 mailbox;zero_dispatched 置位后不再投。"""
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        state_file = tdp / ".state.json"
        state_file.write_text(json.dumps({"state": "ACTIVE", "zero_dispatched": False}))
        rec_dir = tdp / "ev"
        rec_dir.mkdir()

        posted = []

        def fake_urlopen(req, timeout=None):
            posted.append(json.loads(req.data.decode()))
            return _Resp()

        with patch.object(supervisor, "STATE_FILE", state_file), \
             patch.object(supervisor, "REPORT_DIR", rec_dir), \
             patch.object(supervisor, "_v5_recent_commits", lambda: [("ops: dpo train run", "abc123")]), \
             patch.object(supervisor, "post_dispatch_mail", return_value=True) as mock_post:
            supervisor._on_zero_dryrun("ACTIVE", "ZERO", {}, "20260830-0030")
            assert mock_post.call_count == 1
            # 已派过 → 二轮不重发
            supervisor._on_zero_dryrun("ZERO", "ZERO", {}, "20260830-0100")
            assert mock_post.call_count == 1

        assert len(posted) == 0  # post 被 mock,走 mock_post 计数
        recs = [json.loads(l) for l in
                (rec_dir / "dispatch_recommendations.jsonl").read_text().splitlines() if l]
        assert len(recs) == 1
        assert recs[0]["cause"] == "YIELDED"      # dpo/train 命中实验关键词
        assert recs[0]["mail_posted"] is True
        assert json.loads(state_file.read_text())["zero_dispatched"] is True


def test_classify_cause_matrix():
    assert supervisor.classify_cause(None) == "UNKNOWN"
    assert supervisor.classify_cause([("dpo training", "a1")]) == "YIELDED"
    assert supervisor.classify_cause([("fix bug", "a2"), ("docs", "a3")]) == "CRASHED"
