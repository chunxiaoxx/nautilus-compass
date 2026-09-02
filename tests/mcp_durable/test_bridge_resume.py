"""Task 4(2026-09-02 迁移版)· 桥的断线不丢消息契约 · v1.9 pending 重发模型。

契约沿革(考古:f01f9f0 → b29d0f7 → v1.9):
  旧模型(Task 2/3/4 原版):server 帧带单调 `_eid` → 桥剥 `_eid` 转发 + 记
  high-water → 重连时向 initialize 注入 `params.lastEventId` → server replay。
  8/24 双实锤后废弃:①顶层 `_eid` 是协议外字段,CC 2.1 严格客户端握手即弃连
  (f01f9f0 根因);②云桥重构(b29d0f7)改为 v1.9 模型。

现行 v1.9 契约(本文件钉的就是它):
  1. 转发给 Claude Code 的任何行**不带顶层 `_eid`**(belt-and-braces 剥离)。
  2. 断线不丢=按 json-rpc id 追踪:note_request 记录未答请求,note_reply 清除。
  3. 重连(connect(replay=True)):重放缓存的 initialize(带 authToken 重注);
     pending 里**只读幂等**工具静默重发;**非幂等写**(ingest_obs 等云端无幂等键)
     不盲重发,回 -32603 让客户端有意识地重试——不静默丢,也不静默重。
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent.parent
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))
os.environ.setdefault("COMPASS_CLOUD_TOKEN", "test-dummy-token")
bridge = importlib.import_module("ops.mcp_stdio_to_cloud")


# --------------------------------------------------------------------------
# (a) 顶层 _eid 剥离 · 纯函数 _strip_top_level_eid
# --------------------------------------------------------------------------

def test_strip_top_level_eid_removes_internal_field():
    line = json.dumps({"jsonrpc": "2.0", "id": 5, "result": {"ok": 1}, "_eid": 3})
    out = bridge._strip_top_level_eid(line)
    decoded = json.loads(out)
    assert "_eid" not in decoded
    assert decoded["id"] == 5
    assert decoded["result"] == {"ok": 1}


def test_strip_line_without_eid_unchanged():
    line = json.dumps({"jsonrpc": "2.0", "id": 9, "result": {}})
    assert bridge._strip_top_level_eid(line) == line


def test_strip_non_json_unchanged_and_never_crashes():
    assert bridge._strip_top_level_eid("not-json-at-all") == "not-json-at-all"
    assert bridge._strip_top_level_eid("") == ""
    # 非对象 JSON(数组/数字)也不崩、不加戏
    assert bridge._strip_top_level_eid("[1,2]") == "[1,2]"


def test_strip_preserves_cjk_bytes():
    """中文 recall 是主负载 · 转发行必须保留字面 CJK(ensure_ascii=False),
    不能变成 \\uXXXX 转义(体积 ~6x,94b002a 的原教训)。"""
    line = json.dumps({"_eid": 1, "result": {"text": "CPU饥饿诊断"}},
                      ensure_ascii=False)
    out = bridge._strip_top_level_eid(line)
    assert "CPU饥饿诊断" in out
    assert "\\u" not in out
    decoded = json.loads(out)
    assert decoded["result"]["text"] == "CPU饥饿诊断"
    assert "_eid" not in decoded


# --------------------------------------------------------------------------
# (b) pending 生命周期 · note_request / note_reply / pending_lines
# --------------------------------------------------------------------------

def _req(mid: int, tool: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                       "params": {"name": tool, "arguments": {"query": "q"}}})


def test_note_request_tracks_pending():
    link = bridge._CloudLink(opener=lambda: None)
    link.note_request(_req(1, "recall"))
    link.note_request(_req(2, "drift_check"))
    pend = link.pending_lines()
    assert len(pend) == 2
    assert json.loads(pend[0])["id"] == 1
    assert json.loads(pend[1])["id"] == 2


def test_note_reply_clears_pending():
    link = bridge._CloudLink(opener=lambda: None)
    link.note_request(_req(7, "recall"))
    assert len(link.pending_lines()) == 1
    link.note_reply(json.dumps({"jsonrpc": "2.0", "id": 7, "result": {}}))
    assert link.pending_lines() == []
    # error 回复同样清除(失败也是"已答",不该在重连时重发)
    link.note_request(_req(8, "recall"))
    link.note_reply(json.dumps({"jsonrpc": "2.0", "id": 8, "error": {"code": -1}}))
    assert link.pending_lines() == []


def test_note_request_ignores_initialize_and_garbage():
    """initialize 走 note_outgoing 的缓存通道,进 pending 会在重连时双发。"""
    link = bridge._CloudLink(opener=lambda: None)
    link.note_request(json.dumps({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                                  "params": {}}))
    link.note_request("garbage-not-json")
    link.note_request(json.dumps([1, 2, 3]))
    # 通知(method 无 id)不期待回复,不追踪
    link.note_request(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}))
    assert link.pending_lines() == []


def test_pending_lines_snapshot_is_copy():
    link = bridge._CloudLink(opener=lambda: None)
    link.note_request(_req(1, "recall"))
    snap = link.pending_lines()
    snap.clear()
    assert len(link.pending_lines()) == 1  # 内部不受快照篡改影响


# --------------------------------------------------------------------------
# (c) 重连重放集成 · connect(replay=True) over fake socket
# --------------------------------------------------------------------------

class _FakeSock:
    """记录 sendall 全部行;recv 只供 _recv_one_line 吞 duplicate init reply。"""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self._one_reply = b'{"jsonrpc":"2.0","id":0,"result":{"ok":1}}\n'

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, n: int) -> bytes:
        if self._one_reply:
            r, self._one_reply = self._one_reply, b""
            return r
        return b""

    def settimeout(self, *_a, **_k) -> None:
        pass

    def close(self) -> None:
        pass


def test_connect_replay_auth_and_idempotent_resend(monkeypatch):
    fake = _FakeSock()
    link = bridge._CloudLink(opener=lambda: fake)
    init_line = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2024-11-05"}})
    link.note_outgoing(init_line)

    # 断线前在途:一个幂等只读 + 一个非幂等写
    link.note_request(_req(11, "recall"))
    link.note_request(_req(12, "ingest_obs"))

    monkeypatch.setattr(bridge, "_recv_one_line", lambda s, timeout=10.0: b"{}\n")
    errors_emitted: list[bytes] = []
    monkeypatch.setattr(bridge, "_write_stdout", errors_emitted.append)

    link.connect(replay=True)

    sent_lines = [json.loads(d.decode("utf-8").strip()) for d in fake.sent
                  if d.strip()]

    # 1) 缓存的 initialize 被重放,且 authToken 重新注入(真实 token 来自 env)
    inits = [m for m in sent_lines if m.get("method") == "initialize"]
    assert len(inits) == 1, f"initialize 应恰好重放一次,实际 {len(inits)}"
    assert inits[0]["params"].get("authToken") == "test-dummy-token"

    # 2) 幂等只读请求被静默重发(auth 已注入)
    resent_ids = [m["id"] for m in sent_lines
                  if m.get("method") == "tools/call" and m.get("id") in (11, 12)]
    assert resent_ids == [11], (
        f"只应重发幂等 id=11;非幂等 id=12 不得盲发,实际 {resent_ids}")

    # 3) 非幂等写不静默丢:回 -32603 让客户端有意识重试;且它被移出 pending。
    #    幂等重发(id=11)仍留在 pending——重发≠已答,等真回复到达才清除。
    pend_ids = [json.loads(l)["id"] for l in link.pending_lines()]
    assert 11 in pend_ids, "幂等重发后应仍在 pending 等回复"
    assert 12 not in pend_ids, "非幂等写处理后应移出 pending"
    err_msgs = [json.loads(d.decode("utf-8")) for d in errors_emitted if d.strip()]
    err_ids = [m.get("id") for m in err_msgs if m.get("error")]
    assert 12 in err_ids, f"id=12 应收到 -32603 错误回执,实际 stdout: {err_msgs}"
    the_err = next(m for m in err_msgs if m.get("id") == 12)
    assert the_err["error"]["code"] == -32603
