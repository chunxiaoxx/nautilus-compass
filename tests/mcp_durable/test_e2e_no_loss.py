"""Task 6(2026-09-02 契约迁移版)· e2e 零丢失 · v1.9 pending 重发闭环。

旧版钉的是 Last-Event-ID 补帧闭环(server replay k+1..N)。8/24 f01f9f0 +
b29d0f7 重构后,桥的零丢失语义 = v1.9 pending 模型:

  durable 路径:请求在途时掉线 → mark_down → connect(replay=True) 重连 →
    幂等只读请求静默重发(回复可达,不丢)→ 非幂等写回 -32603(不静默丢,
    客户端有意识重试)。
  对比(v1.8-only):只重连(replay=False)不重发 pending → 在途请求的回复
    永不到达 = 丢失。这正是 durable 层消除的 gap。

server 侧的 Last-Event-ID replay 能力另由 test_resume_handshake 直连覆盖
(该机制代码仍在,只是 v1.9 桥不再依赖它)。
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


class _FakeSock:
    """Phase 感知的 fake 云端 socket:记录全部上行;recv 供 _recv_one_line 吞
    duplicate init reply。phase2 起 recv 直接 EOF(泵 mark_down 前的最后读)。"""

    def __init__(self) -> None:
        self.sent: list[bytes] = []
        self.replies: list[bytes] = [
            b'{"jsonrpc":"2.0","id":0,"result":{"ok":1}}\n']
        self.closed = False

    def sendall(self, data: bytes) -> None:
        self.sent.append(data)

    def recv(self, n: int) -> bytes:
        if self.replies:
            return self.replies.pop(0)
        return b""

    def settimeout(self, *_a, **_k) -> None:
        pass

    def close(self) -> None:
        self.closed = True


def _tool_req(mid: int, tool: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "id": mid, "method": "tools/call",
                       "params": {"name": tool, "arguments": {"query": f"q{mid}"}}})


def _setup(monkeypatch):
    """公共前置:真 _CloudLink + 缓存 init + burst pending(3 幂等 + 2 非幂等)。"""
    fake1 = _FakeSock()
    link = bridge._CloudLink(opener=lambda: fake1)
    link.note_outgoing(json.dumps(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2024-11-05"}}))
    link.connect(replay=False)  # 首连:install socket,真 initialize 正常流过
    # stdin-pump 语义:每个待答请求 send 后 note_request(行 658-659)
    inflight = [(10, "recall"), (11, "drift_check"), (12, "thread_recall"),
                (13, "ingest_obs"), (14, "feedback_log")]
    for mid, tool in inflight:
        line = bridge._inject_auth(_tool_req(mid, tool))
        link.send(line)
        link.note_request(line)
    emitted: list[bytes] = []
    monkeypatch.setattr(bridge, "_write_stdout", emitted.append)
    monkeypatch.setattr(bridge, "_recv_one_line",
                        lambda s, timeout=10.0: b'{"jsonrpc":"2.0","id":0,"result":{}}\n')
    return link, fake1, inflight, emitted


# --------------------------------------------------------------------------
# 1) POSITIVE — durable 路径闭环:幂等全重发、非幂等全报错、无静默丢。
# --------------------------------------------------------------------------

def test_e2e_zero_loss_across_drop_durable_path(monkeypatch):
    link, fake1, inflight, emitted = _setup(monkeypatch)
    assert len(link.pending_lines()) == 5

    # --- transport drop · pump 语义 ---
    link.mark_down()

    # --- reconnect(durable seam):fake2 是新隧道对端 ---
    fake2 = _FakeSock()
    link._opener = lambda: fake2
    link.connect(replay=True)

    sent2 = [json.loads(d.decode("utf-8").strip()) for d in fake2.sent
             if d.strip()]

    # (a) initialize 恰好重放一次,authToken 重新注入
    inits = [m for m in sent2 if m.get("method") == "initialize"]
    assert len(inits) == 1
    assert inits[0]["params"].get("authToken") == "test-dummy-token"

    # (b) 幂等只读(10/11/12)全部重发,auth 注入 —— 回复可达 = 不丢
    resent = sorted(m["id"] for m in sent2 if m.get("method") == "tools/call")
    assert resent == [10, 11, 12], f"幂等重发集不符: {resent}"

    # (c) 非幂等写(13/14)不盲发,逐个回 -32603 —— 不静默丢、不静默重
    errs = [json.loads(d.decode("utf-8")) for d in emitted if d.strip()]
    err_ids = sorted(m["id"] for m in errs if m.get("error"))
    assert err_ids == [13, 14], f"应恰好 13/14 收到错误回执: {err_ids}"
    assert all(m["error"]["code"] == -32603 for m in errs if m.get("error"))

    # (d) durable 闭环:重发的幂等请求收到云端回复 → note_reply 清 pending
    for mid in (10, 11, 12):
        link.note_reply(json.dumps({"jsonrpc": "2.0", "id": mid, "result": {}}))
    assert link.pending_lines() == [], "全部在途应有终态(重发后已答/错误回执)"

    # (e) 转发链路 _eid 不漏:任一云端行过 _strip_top_level_eid 后无 _eid
    leaked = json.dumps({"jsonrpc": "2.0", "id": 99, "_eid": 7,
                         "result": {"text": "中文"}}, ensure_ascii=False)
    assert "_eid" not in bridge._strip_top_level_eid(leaked)


# --------------------------------------------------------------------------
# 2) CONTRAST — v1.8-only(replay=False 只重连不重发)在途请求丢失。
#    证明 durable 层(pending 重发)非平凡:去掉它,gap 就回来。
# --------------------------------------------------------------------------

def test_e2e_v18_only_reconnect_loses_inflight_frames(monkeypatch):
    link, fake1, inflight, emitted = _setup(monkeypatch)
    assert len(link.pending_lines()) == 5

    link.mark_down()

    fake2 = _FakeSock()
    link._opener = lambda: fake2
    link.connect(replay=False)   # v1.8 行为:只重连,pending 不重发

    sent2 = [json.loads(d.decode("utf-8").strip()) for d in fake2.sent
             if d.strip()]

    # 重连后仅初始化(本次为 Claude 真实 initialize 流过),无任何 tools/call 重发
    assert not [m for m in sent2 if m.get("method") == "tools/call"], (
        "v1.8 不重发 pending,却出现了 tools/call——replay=False 语义被破坏")
    # 无错误回执:客户端不知道在途请求死了 → 回复永不到达 = 丢失(旧 gap)
    assert not [d for d in emitted if d.strip()], "v1.8 不该有 -32603 回执"
    # pending 仍挂着:既没重发也没报错,这就是丢失本身
    assert len(link.pending_lines()) == 5
