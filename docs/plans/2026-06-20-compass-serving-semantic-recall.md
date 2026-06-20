# Compass Serving 语义 Recall(记忆胶囊 bge-m3 升级)Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 serving `/v1/recall?cross_agent=true` 从 sqlite 关键词匹配升级为 bge-m3 语义召回,使 live RSI loop 的 W2 跨 agent peer-learning recall 按语义相关性排序(B 用不同措辞也能召回 A 的 learning)。

**Architecture:** 不在 serving 另载模型、不建持久 embedding 索引(v1·YAGNI)。recall 时 serving 仍从 sqlite 取候选 observations(现行 over-fetch top_k×4),把 query + 候选文本经 cloud→T4 隧道发给已加载 bge-m3 的 compass-daemon(:9876)新增 `score` action,daemon 返 cosine 分,serving 按分排序返 top-k。daemon 不可达 → 优雅降级回现有关键词打分(recall 永不因 daemon 抖动崩)。

**Tech Stack:** Python · FastAPI(`compass_http_v09.py`)· daemon TCP JSON 协议(`daemon.py`)· sentence-transformers bge-m3(daemon 已载·T4 GPU)· socket。

**🔴 前提纪律(改 live 服务铁律·本仓踩过 7 副本漂移坑)**:改 cloud/T4 服务前核运行真身(`/proc/<pid>/cwd` + healthz 版本号 + `systemctl cat`)。daemon 加 action 不得破 recall/drift 现行为(6/20 刚瘦身部署过 `compass-daemon.service`)。每段 ship 走 verification-before-completion(真 socket/curl 实测·非"我以为")。

---

## Task 0: 核实部署拓扑 + daemon 协议(动手前必做·不写码)

**为什么**:serving 与 daemon 可能不同机(serving cloud / daemon T4·靠 `compass-t4-tunnel`),`DAEMON_HOST` 默认 `127.0.0.1:9876` 需确认在 serving 所在机能解析到 daemon。

**Steps:**
1. 核 serving 运行真身:`ssh <serving-box> "systemctl cat compass.service | grep -E 'ExecStart|WorkingDir'; cat /proc/\$(pgrep -f compass_http)/cwd -L 2>/dev/null; curl -s localhost:<port>/healthz"` → 记版本号 + CWD + 端口。
2. 核 daemon 真身:T4 `43.166.8.20` `compass-daemon.service`(6/20 瘦身后 PID·:9876)。确认从 serving box 能 `nc -z <DAEMON_HOST>`(隧道通)。
3. 读 daemon 现有 recall action 协议(`daemon.py` `_handle`/请求分发):确认 JSON 行协议 `{"action":...}` → `{"ok":...}`,记 socket 读写格式(换行分帧)。
4. 产出:在本 plan 末尾追加「拓扑实测」小节(serving box / daemon host / 隧道 / 端口 / 版本),后续 Task 据此填真值。

**无代码改动·无 commit。**

---

## Task 1: daemon 新增 `score` action(bge-m3 query↔候选 cosine)

**Files:**
- Modify: `daemon.py`(请求分发处加 `score` 分支 + 一个 `_handle_score` 函数·复用已载 `embedder`)
- Test: `tests/test_daemon_score.py`(新建)

**Contract:**
```
请求:  {"action":"score","query":"<str>","candidates":["<text>", ...]}
响应:  {"ok":true,"scores":[<float cosine>, ...]}   # 顺序对齐 candidates
         {"ok":false,"error":"..."}                  # 候选空/embedder 未载等
```

**Step 1: 写失败测试**

```python
# tests/test_daemon_score.py
import json, daemon  # daemon 模块可 import(顶层无副作用执行)

class _FakeEmbedder:
    # 确定性假向量:按文本是否含 "alpha" 给正交方向,避免真载 bge-m3
    def encode(self, text):
        return [1.0, 0.0] if "alpha" in text else [0.0, 1.0]

def test_score_ranks_by_cosine(monkeypatch):
    monkeypatch.setattr(daemon, "_get_embedder", lambda: _FakeEmbedder())
    req = {"action": "score", "query": "alpha thing",
           "candidates": ["alpha match", "beta other"]}
    resp = daemon._handle_score(req)            # 纯函数·不走 socket
    assert resp["ok"] is True
    assert len(resp["scores"]) == 2
    assert resp["scores"][0] > resp["scores"][1]  # alpha 候选更相关

def test_score_empty_candidates():
    resp = daemon._handle_score({"action": "score", "query": "x", "candidates": []})
    assert resp["ok"] is False
```

> ⚠️ 实现前先读 `daemon.py` 确认 embedder 取用方式(现为 `_BGEWrapper.encode` 经 `embedder` 单例)。若无 `_get_embedder` 取用点,实现时抽一个,测试 monkeypatch 它。cosine 用纯 Python(`sum(a*b)/(‖a‖‖b‖)`)不引依赖。

**Step 2: 跑测试验证失败**
Run: `PYTHONUTF8=1 python -m pytest tests/test_daemon_score.py -v`
Expected: FAIL（`_handle_score` 不存在）

**Step 3: 最小实现**

```python
# daemon.py · 加在 recall handler 附近
def _cosine(a, b):
    import math
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0.0

def _handle_score(req):
    cands = req.get("candidates") or []
    if not cands:
        return {"ok": False, "error": "no candidates"}
    try:
        emb = _get_embedder()                  # 已载 bge-m3 单例
        qv = emb.encode(req.get("query", ""))
        scores = [_cosine(qv, emb.encode(c)) for c in cands]
        return {"ok": True, "scores": scores}
    except Exception as e:
        return {"ok": False, "error": str(e)}
```
并在请求分发处加：`elif action == "score": resp = _handle_score(req)`。

**Step 4: 跑测试验证通过**
Run: `PYTHONUTF8=1 python -m pytest tests/test_daemon_score.py -v`
Expected: PASS（2 passed）

**Step 5: Commit**
```bash
git add daemon.py tests/test_daemon_score.py
git commit -m "feat(daemon): add score action — bge-m3 query↔candidate cosine (serving semantic recall)"
```

---

## Task 2: serving `_daemon_score` 客户端 helper(socket + 优雅降级)

**Files:**
- Modify: `compass_http_v09.py`(加模块级 `_daemon_score(query, candidates) -> Optional[list[float]]`)
- Test: `tests/test_serving_daemon_score.py`(新建)

**Step 1: 写失败测试**

```python
# 注入 fake socket·验:正常返 scores / daemon 不可达返 None(不抛)
import compass_http_v09 as srv

def test_daemon_score_parses(monkeypatch):
    class FakeSock:
        def __init__(s): s.sent=b""
        def settimeout(s,t): pass
        def connect(s,a): pass
        def sendall(s,b): s.sent+=b
        def recv(s,n): return b'{"ok":true,"scores":[0.9,0.1]}\n'
        def close(s): pass
    monkeypatch.setattr(srv.socket, "socket", lambda *a, **k: FakeSock())
    out = srv._daemon_score("q", ["a", "b"])
    assert out == [0.9, 0.1]

def test_daemon_score_unreachable_returns_none(monkeypatch):
    def boom(*a, **k): raise ConnectionError("down")
    monkeypatch.setattr(srv.socket, "socket", boom)
    assert srv._daemon_score("q", ["a"]) is None   # 降级·不抛
```

**Step 2: 跑测试验证失败**
Run: `PYTHONUTF8=1 python -m pytest tests/test_serving_daemon_score.py -v`
Expected: FAIL（`_daemon_score` 不存在）

**Step 3: 最小实现**

```python
# compass_http_v09.py · 模块级（DAEMON_HOST 已有：os.environ.get("COMPASS_DAEMON_HOST","127.0.0.1:9876")）
def _daemon_score(query, candidates, timeout=5.0):
    """发 score 请求给 bge-m3 daemon·返 cosine 分列表·不可达/异常返 None(调用方降级关键词)。"""
    if not candidates:
        return None
    host, _, port = DAEMON_HOST.partition(":")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, int(port or "9876")))
        s.sendall((json.dumps({"action": "score", "query": query,
                               "candidates": candidates}) + "\n").encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            c = s.recv(65536)
            if not c:
                break
            buf += c
        s.close()
        resp = json.loads(buf.decode("utf-8").strip())
        return resp.get("scores") if resp.get("ok") else None
    except Exception:
        return None
```

**Step 4: 跑测试验证通过**
Run: `PYTHONUTF8=1 python -m pytest tests/test_serving_daemon_score.py -v`
Expected: PASS（2 passed）

**Step 5: Commit**
```bash
git add compass_http_v09.py tests/test_serving_daemon_score.py
git commit -m "feat(serving): _daemon_score client — socket to bge-m3 daemon, graceful fallback"
```

---

## Task 3: recall handler 接语义排序(保留关键词降级 + 所有过滤)

**Files:**
- Modify: `compass_http_v09.py:521-556`（`recall` handler）
- Test: `tests/test_recall_semantic.py`(新建)

**关键不变量**:`drift` / `cross_agent` / `agent_id` 过滤行为不变;daemon 返 None 时**完全回退到现有关键词打分**(行为零回归);返回结构(`hits` 字段)不变。

**Step 1: 写失败测试**

```python
import compass_http_v09 as srv
# 用现有测试 DB fixture（若无·建最小 sqlite 注入两条 obs：含 "alpha"/"beta"）。
# 注入 _daemon_score 返已知分·验 hits 顺序按 cosine·且 daemon=None 时回退关键词。

def test_recall_uses_daemon_scores(monkeypatch, seed_two_obs):  # seed_two_obs: fixture
    monkeypatch.setattr(srv, "_daemon_score", lambda q, c: [0.2, 0.95])  # 第2条更相关
    res = srv.recall(q="anything", top_k=2, cross_agent=True, user_id="u_test")
    assert res["hits"][0]["score"] == 0.95            # 按 cosine 排
    assert res["hits"][0]["score"] >= res["hits"][1]["score"]

def test_recall_falls_back_to_keyword_when_daemon_down(monkeypatch, seed_two_obs):
    monkeypatch.setattr(srv, "_daemon_score", lambda q, c: None)
    res = srv.recall(q="alpha", top_k=2, cross_agent=True, user_id="u_test")
    assert res["hits"]                                  # 仍返回(关键词路径)
```

**Step 2: 跑测试验证失败**
Run: `PYTHONUTF8=1 python -m pytest tests/test_recall_semantic.py -v`
Expected: FAIL

**Step 3: 实现（改 540-555 段）**

```python
    # candidate texts（content_plain）· 顺序固定
    cand_texts = [(r["content_plain"] or "") for r in rows]
    sem = _daemon_score(q, cand_texts)        # bge-m3 cosine·None=降级
    hits = []
    for i, r in enumerate(rows):
        content = r["content_plain"] or ""
        if sem is not None:
            score = float(sem[i])             # 语义
        else:
            score = 1.0 if q.lower() in content.lower() else 0.5   # 关键词降级（原行为）
        hits.append({
            "obs_id": r["obs_id"], "agent_id": r["agent_id"], "score": score,
            "ts": r["ts"], "drift": r["drift"], "type": r["type"],
            "content_or_encrypted": json.loads(content) if content else None,
        })
    hits = sorted(hits, key=lambda h: -h["score"])[:top_k]
    return {"user_id": user_id, "query": q, "hits": hits, "ranker": "bge-m3" if sem is not None else "keyword"}
```

**Step 4: 跑测试验证通过 + 回归**
Run: `PYTHONUTF8=1 python -m pytest tests/test_recall_semantic.py tests/test_serving_daemon_score.py -v`
Expected: PASS（全绿）
另跑现有 serving 测试套件确认零回归:`PYTHONUTF8=1 python -m pytest tests/ -k recall -v`

**Step 5: Commit**
```bash
git add compass_http_v09.py tests/test_recall_semantic.py
git commit -m "feat(serving): recall ranks by bge-m3 cosine (keyword fallback preserved) — RSI W2 semantic"
```

---

## Task 4: 端到端语义验证(verification-before-completion · 真证据)

**目标**:证 bge-m3 召回胜过关键词基线(B 用不同措辞召回 A 的 learning)。**本地起 daemon + serving 或对 staging·非生产**。

**Steps:**
1. 构造:同 user 两 agent。agent A `POST /v1/observations` 写 learning（措辞 X·如 "retry with exponential backoff on 429 rate limit"）。
2. agent B `GET /v1/recall?cross_agent=true&q=<措辞 Y 语义近·如 "handle too-many-requests throttling">`。
3. 断言:bge-m3 路径命中 A 的 obs（score 高·`ranker:bge-m3`）;同 query 关键词基线（daemon 停）miss 或排末。
4. 对照:`q` 与 A content 无词面重叠但语义近 → 关键词 0.5 平分排不出·bge-m3 排第一 = 升级价值实证。
5. 记录真 curl 输出 + 两 ranker 对比进收尾 memory。

**无新增生产代码·验证脚本可留 `examples/`。**

---

## Task 5: 协调部署 + 真证据验证

**前提**:Task 0 拓扑已核实。部署 = daemon(加 score action)+ serving(recall 改)双端,**重启会让 recall 短暂离线**(影响所有框)→ 协调窗口(参考 6/20 daemon 瘦身部署:ping soul/V5·MCP 桥 v1.8 自动重连兜底)。

**Steps:**
1. 备份 box 双端文件(`.bak.<date>`)。
2. scp daemon.py → daemon box(同版本核对·**先归一化 CRLF 再 diff 防假分叉**·6/20 踩过)→ restart `compass-daemon.service`。
3. scp compass_http_v09.py → serving box → restart serving service。
4. **验证(真证据·非 systemctl-active)**:
   - daemon:发 `score` 请求 socket 实测返 scores。
   - serving:curl `/v1/recall?cross_agent=true&q=...` 返 `ranker:bge-m3` + 合理排序。
   - 回归:普通 recall/drift 仍正常;nvidia-smi daemon 显存未暴涨。
   - 端到端:Task 4 的 A 写→B 语义召回 在生产/staging 复现。
5. 收尾 memory:登记部署态 + box-vs-repo 对账(systemd/代码)+ ranker 切换实证。

---

## 不做(parking lot · YAGNI)
- 持久 embedding 索引 / 写时预嵌入(line 494 TODO):候选集小(top_k×4)·embed-on-fly 够·量大再做。
- query embedding 缓存:同上。
- 重排序器(cross-encoder)二段:bge-m3 cosine 够 v1·reranker 是后续。
- 不碰 daemon 的文件记忆 recall 路径(那是另一 store·本 plan 只加 score action 复用模型)。

## 关联
memory `session_20260620_C_memory_capsule_serving_recall_keyword_gap_audit`(审计源)· `canonical_memory_capsule_equals_compass_crossagent_mcp_collective_learning`(定义)· `session_20260619_compass_fleet_obs_id_sanitize_fix`(W1 写端·已修)· `session_20260620_crossdialog_convergence_sync_swe_pathB_gpu_unblock`(W2 被 live RSI 用)。
```
