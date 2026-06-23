# MCP Bridge 硬化(v1.9 在途请求持久化)Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在已合的 v1.8 自动重连之上,补 bridge 侧「在途请求持久化」——cloud 在收到请求但未回复时掉线,重连后能重发该请求拿到 reply,而不是让 Claude 等一个永不来的 id。外加激活验证 + liveness 探针。

**Architecture:** 全部改 `ops/mcp_stdio_to_cloud.py` 的 `_CloudLink`(它已 own socket + 重连)。新增 `_pending` 映射(json-rpc id → 已注入 auth 的请求行);`note_request` 在转发后登记、`note_reply` 在收到 reply 后销账;`connect(replay=True)` 重放 initialize 后追加重发所有 pending。零网络 TDD(注入 `_FakeSock`),与现有 `tests/test_mcp_bridge_reconnect.py` 同风格。

**Tech Stack:** Python 3 · stdlib(socket/threading/json)· pytest · 测试零网络(fake opener/fake sock)。

**范围边界(诚实账):** 本 plan 只覆盖 MCP 全深栈的 **bridge 侧**(① 在途持久化 + v1.8 激活验证 + ③ liveness 探针的 bridge 部分)。**不在本 plan**: serving 层 ②(staggered health check)④(下沉协议)= cloud `mcp_server.py` 改面大、SSH-gated,单独 plan;调度复利/GEP/learnability/负样本蒸馏 = gated 放大件,设计已出、施工 plan 待 gate 清(见证 + 蒸馏 sanity)。

**前置:** 工作树 = `nautilus-compass` 分支 `design/architecture-fusion-20260623`(已含设计 doc)。⚠️ 运行时真身 = `~/.claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py`;源仓 = 本 repo `ops/`。两份需同步(消除历史漂移)——见 Task 5。

---

### Task 1: 验证 v1.8 现状 baseline(先确认起点)

**Files:**
- Test: `tests/test_mcp_bridge_reconnect.py`(已存·7 测)

**Step 1: 跑现有测试确认绿**

Run: `cd ~/.claude/plugins/nautilus-compass && python -m pytest tests/test_mcp_bridge_reconnect.py -v`
Expected: 7 passed(`_CloudLink` 状态机已 pin)

**Step 2: 确认 `_pending` 尚不存在(本 plan 起点)**

Run: `python -c "import ops.mcp_stdio_to_cloud as b; print(hasattr(b._CloudLink(opener=lambda:None), '_pending'))"`
Expected: `False`(无在途持久化)— 这是要补的缺口。

---

### Task 2: `note_request` 登记在途请求(failing test first)

**Files:**
- Modify: `ops/mcp_stdio_to_cloud.py`(`_CloudLink`)
- Test: `tests/test_mcp_bridge_reconnect.py`

**Step 1: 写失败测试**

```python
def test_note_request_tracks_method_with_id():
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{}}')
    assert link.pending_lines()  # 一条在途

def test_note_request_ignores_initialize():
    # initialize 走 _init_line 重放,不进 pending(否则重连双发)
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","id":0,"method":"initialize","params":{}}')
    assert link.pending_lines() == []

def test_note_request_ignores_notification_without_id():
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","method":"notifications/initialized"}')
    assert link.pending_lines() == []
```

**Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_mcp_bridge_reconnect.py::test_note_request_tracks_method_with_id -v`
Expected: FAIL(`AttributeError: 'pending_lines'`)

**Step 3: 实现 `note_request` + `pending_lines`**

在 `_CloudLink.__init__` 加 `self._pending = {}`。新增方法:

```python
def note_request(self, line: str) -> None:
    """登记一条期待 reply 的请求(有 method + id·非 initialize),
    供重连后重发。initialize 由 _init_line 单独重放,不进 pending。"""
    try:
        msg = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(msg, dict) or msg.get("method") == "initialize":
        return
    if msg.get("method") is not None and "id" in msg:
        with self._lock:
            self._pending[msg["id"]] = line

def pending_lines(self):
    with self._lock:
        return list(self._pending.values())
```

**Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_mcp_bridge_reconnect.py -v`
Expected: PASS(含新 3 测 + 原 7 测)

**Step 5: Commit**

```bash
git add ops/mcp_stdio_to_cloud.py tests/test_mcp_bridge_reconnect.py
git commit -m "feat(mcp-bridge): v1.9 note_request 登记在途请求"
```

---

### Task 3: `note_reply` 销账(reply 到达清 pending)

**Files:**
- Modify: `ops/mcp_stdio_to_cloud.py`(`_CloudLink`)
- Test: `tests/test_mcp_bridge_reconnect.py`

**Step 1: 写失败测试**

```python
def test_note_reply_clears_pending():
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","id":5,"method":"tools/call","params":{}}')
    assert link.pending_lines()
    link.note_reply('{"jsonrpc":"2.0","id":5,"result":{"ok":true}}')
    assert link.pending_lines() == []  # 销账

def test_note_reply_ignores_non_reply():
    link = bridge._CloudLink(opener=_opener_factory([]))
    link.note_request('{"jsonrpc":"2.0","id":5,"method":"tools/call"}')
    link.note_reply('{"jsonrpc":"2.0","id":5,"method":"x"}')  # 无 result/error
    assert link.pending_lines()  # 仍在途
```

**Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_mcp_bridge_reconnect.py::test_note_reply_clears_pending -v`
Expected: FAIL(`AttributeError: 'note_reply'`)

**Step 3: 实现 `note_reply`**

```python
def note_reply(self, line: str) -> None:
    """收到 reply(有 id + result/error)→ 清对应在途请求。"""
    try:
        msg = json.loads(line)
    except (json.JSONDecodeError, TypeError):
        return
    if not isinstance(msg, dict):
        return
    if "id" in msg and ("result" in msg or "error" in msg):
        with self._lock:
            self._pending.pop(msg["id"], None)
```

**Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_mcp_bridge_reconnect.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add ops/mcp_stdio_to_cloud.py tests/test_mcp_bridge_reconnect.py
git commit -m "feat(mcp-bridge): v1.9 note_reply 销账"
```

---

### Task 4: 重连后重发在途请求 + 接线进 pumps

**Files:**
- Modify: `ops/mcp_stdio_to_cloud.py`(`connect` + `_pump_in_to_cloud` + `_pump_cloud_to_out`)
- Test: `tests/test_mcp_bridge_reconnect.py`

**Step 1: 写失败测试**

```python
def test_reconnect_resends_pending_after_init_replay():
    """重连: 先重放 initialize(吞其 reply),再重发在途请求。"""
    init = '{"jsonrpc":"2.0","id":7,"method":"initialize","params":{}}'
    init_reply = (json.dumps({"jsonrpc":"2.0","id":7,"result":{}}) + "\n").encode()
    s = _FakeSock(replies=[init_reply])
    link = bridge._CloudLink(opener=_opener_factory([s]))
    link.note_outgoing(init)
    link.note_request('{"jsonrpc":"2.0","id":9,"method":"tools/call","params":{"authToken":"t"}}')
    link.connect(replay=True)
    # 发了 2 帧: [0]=重放 initialize, [1]=重发的在途请求
    assert len(s.sent) == 2
    resent = json.loads(s.sent[1].decode().strip())
    assert resent.get("id") == 9 and resent.get("method") == "tools/call"
```

**Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_mcp_bridge_reconnect.py::test_reconnect_resends_pending_after_init_replay -v`
Expected: FAIL(只发 1 帧·没重发 pending)

**Step 3: 在 `connect(replay=True)` 重放 initialize 后追加重发 pending**

在 `connect` 的 `_recv_one_line(s)` 吞重复 reply 之后、`with self._lock: self._sock = s` 之前,加:

```python
            # v1.9 · re-send in-flight requests lost across the drop.
            # recall/drift 天然幂等;ingest_obs 用幂等键(含 source)→ 重发安全。
            for pl in self.pending_lines():
                s.sendall((pl + "\n").encode("utf-8"))
```

**Step 4: 接线 pumps**

- `_pump_in_to_cloud`: `link.send(out)` 成功后(`_trace("→CLOUD", out)` 那行旁)加 `link.note_request(out)`。
- `_pump_cloud_to_out`: 写 stdout 前(`_write_stdout(cl + b"\n")` 旁)加 `link.note_reply(cl.decode("utf-8", errors="replace"))`。

**Step 5: 跑全测 + 编译检查**

Run: `python -m pytest tests/test_mcp_bridge_reconnect.py -v && python -c "import ast; ast.parse(open('ops/mcp_stdio_to_cloud.py',encoding='utf-8').read()); print('OK')"`
Expected: 全 PASS + `OK`

**Step 6: Commit**

```bash
git add ops/mcp_stdio_to_cloud.py tests/test_mcp_bridge_reconnect.py
git commit -m "feat(mcp-bridge): v1.9 重连重发在途请求 + pumps 接线"
```

---

### Task 5: 同步 plugin 真身 + 源仓(消漂移)

**Files:**
- Modify: `~/.claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py`(运行时真身)
- Modify: `~/.claude/plugins/nautilus-compass/tests/test_mcp_bridge_reconnect.py`

**Step 1: 比对两份差异**

Run: `diff ~/.claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py ops/mcp_stdio_to_cloud.py`
Expected: 显示源仓比 plugin 多 v1.9 改动(或两者起点一致)。

**Step 2: 把 v1.9 改动同步到 plugin 真身**(运行时从这跑)

将源仓 `ops/mcp_stdio_to_cloud.py` + 测试 copy 到 plugin dir,或精确重放 4 处编辑。

**Step 3: 在 plugin dir 跑测试确认绿**

Run: `cd ~/.claude/plugins/nautilus-compass && python -m pytest tests/test_mcp_bridge_reconnect.py -v`
Expected: 全 PASS(真身已带 v1.9)

---

### Task 6: 激活验证(端到端·verification-before-completion)

> ⚠️ **激活=运行时副作用·gate 待用户点头**(R3/honest-account)。本 task 是验证步骤清单,执行需用户明示。

**Step 1: fake-server 重连 smoke(零真网络)**

写/跑一个 fake cloud server 脚本: conn1 接 initialize+tools/call→中途断→conn2 首条必须是 initialize、随后收到**重发的 tools/call**、bridge 回 reply。
Expected: conn2 收到 in-flight 请求重发,Claude 侧拿到 reply(非永等)。

**Step 2: `/mcp` 激活 + 真实瞬断实测**

用户在 dialog 跑 `/mcp` spawn 新桥 → 制造隧道瞬断(或等自然抖动)→ 确认无需手动 /mcp、且断时已发的 tool call 重连后返回结果。
Expected: 掉线自愈 + 在途请求不丢。

**Step 3: 回滚预案**

`git checkout main~N -- ops/mcp_stdio_to_cloud.py`(N=v1.9 commit 数)。

---

## 后续 plan(本 plan 范围外·已 design)

- **MCP serving 层 ②④**: cloud `mcp_server.py` staggered health check + session-resume 协议下沉。SSH-gated·改面大·影响 V5/kairos/A2A 所有 client。单独 plan + 单独评审。
- **gated 放大件**(调度复利闭环1 / GEP 复利 / learnability / 2b 负样本蒸馏): 设计已出(`2026-06-23-architecture-fusion-design.md`),施工 plan 待 gate 清:闭环(2)见证转一圈 + 蒸馏 SFT recipe 过 sanity + step-0 身份收口(平台/V5 turf)。
