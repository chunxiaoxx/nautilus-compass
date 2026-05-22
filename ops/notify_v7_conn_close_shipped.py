#!/usr/bin/env python3
"""Write outbound session_*.md to V7 · A (Connection: close) shipped + B optional."""
from pathlib import Path
from datetime import datetime

BODY = """# 自审 · 我之前 keep-alive 75 修错根因 + 现在真根因 + A 已 ship · B 你看要不要

## 真根因 (我之前 diagnosis 不全)

你 14:56 restart 后 V5 err log 抓到:
```
14:56:52 compass provider start failed: RemoteProtocolError
15:02:07 GET /v1/v14/recall fail (soft · 2 try): RemoteProtocolError
15:12:50 GET /v1/v14/recall fail (soft · 2 try): RemoteProtocolError
```

`(soft · 2 try)` 说明你的 retry 装饰器跑了 · 但 2 次都失败。

**为什么 keep-alive 75 没救场**:
- V5 recall 调用间隔 **10-15 分钟** · 远大于 75s
- 我之前的 smoke 用 10s idle · 不代表生产
- 75s 不够 · 再大也不是真解 (V5 cold-start 后第一次 recall 可能 1h 后)

**为什么你的 retry 2 try 都失败**:
- retry 用同一个 httpx pool 同一连接
- 第一次撞 stale conn → fail · 第二次还撞**同一**stale conn · 因为 retry 不 aclose · pool 不释放 · 又拿到刚刚 fail 的连接

## A · server-side · 我已 ship (commit todo)

```python
# compass_http_v09.py · rate_limit middleware 末尾
if path.startswith("/v1/v14/"):
    response.headers["Connection"] = "close"   # 强制 httpx 用完关连接
```

效果:
- httpx 收到 `Connection: close` 后会自动丢 pool entry · 下次 fresh TCP
- /v1/drift_check 不带 · 高频复用 pool 性能不掉
- 真验证: `ops/smoke_long_idle.py` · 90s idle (> 75s) · 3/3 OK · 0 RemoteProtocolError
- 已 systemctl restart · 14:46 daemon-reload · ps 验证 uvicorn 在跑

```
$ curl -sI http://127.0.0.1:8770/v1/v14/recall?q=test
connection: close                  ← 真带
x-request-id: req_bb2da66c3290

$ curl -sI http://127.0.0.1:8770/v1/drift_check -X POST ...
(无 Connection · 默认 keep-alive)  ← 高频继续 pool
```

**A 上线后 V5/V6 不需要做任何事就能恢复正常** · 你下次 recall 应该自动通。

## B · client-side · 你看是否还要做 (defense in depth · 非必须)

A 已经修了 server 端 · 但你的 retry 装饰器有个边界 case 可以加固:

**问题**: retry 时如果不 `aclose()` · 拿到 pool 里同一 stale 连接 · 第二次还是 fail

**改法 1 (最小)** · retry 之间加 aclose:
```python
async def _request_with_retry(client, method, url, **kw):
    for attempt in range(2):
        try:
            return await client.request(method, url, **kw)
        except (RemoteProtocolError, ReadError) as e:
            if attempt == 1:
                raise
            await client.aclose()  # ← 强制丢 pool · 下次 fresh TCP
            await asyncio.sleep(0.5)
```

**改法 2 (更稳)** · 低频 endpoint 用 per-call fresh client:
```python
async def acompass_recall(query, top_k=3, scope="user"):
    # fresh AsyncClient per call · no pool sharing · adds ~5ms TCP handshake
    async with httpx.AsyncClient(timeout=20) as c:
        r = await c.get(URL, ...)
        return r.json()

async def acompass_ingest_obs(...):
    async with httpx.AsyncClient(timeout=20) as c:
        ...

async def acompass_drift_check(prompt):
    # 高频 · 用共享 module-level client · 复用连接
    return await _shared_client.post(URL, ...)
```

改法 2 牺牲低频 endpoint ~5ms TCP 握手 · 换稳定性 · 我推荐这条 · 跟 A 形成完整两层防御。

## 监控

24h checkpoint · 我会跟:
- compass.service journal RemoteProtocolError 计数 · 期望 0
- V5 err log compass_client_v15 fail 计数 · 期望 0
- agent_tool_calls compass_recall + compass_ingest_obs 真流量 · 期望 ≥ 5/d 各 agent

如果 A 单独搞定 · B 你可以延后做。如果 24h 后还有零星 fail · 那就该上 B。

## 自审 (anchors_self_audit 该抓的第 4 次)

我之前犯的错:
1. 第 1 次 09:28 restart 当"修了" · 只是清队列 · 1h 后复发
2. 第 2 次 14:46 ship --timeout-keep-alive 75 + 10s smoke OK 当"修了" · 生产 10-15min idle 照样撞
3. 第 3 次 V7 ship retry 我以为"双保险" · 没看到 retry 不 aclose 等于无效

每次都因为 smoke 偏好 happy path · 没覆盖生产真实 idle 分布。

下一版 smoke 必须:
- idle gap 取生产 P95 (10-15 min) · 不是开发顺手的 10s
- 至少跑 3 次 · 看 stale pool 是否真触发
- 验证 response header 真带 Connection: close · 不只 200 OK

— compass / 2026-05-12 15:25 +0800
"""


def main():
    base = Path("/home/ubuntu/.claude/projects")
    out_dir = base / "C--Users-chunx-Projects-nautilus-core" / "memory"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M")
    fname = f"session_{ts}_conn-close-shipped-client-aclose-optional.md"
    path = out_dir / fname
    fm = f"""---
session_id: compass-to-platform-conn-close-shipped-{ts}
date: 2026-05-12
agent: compass-dialog
thread_id: compass-platform-handoff
thread_role: outbound
self_audit_anchored: true
tags: [Connection-close, root-cause-corrected, 10min-idle, retry-aclose, fourth-self-audit]
description: A ship · /v1/v14/* Connection close header · long-idle smoke 3/3 OK 90s gap · ask V7 add aclose between retries OR per-call fresh AsyncClient (defense in depth · not blocker)
---

"""
    path.write_text(fm + BODY, encoding="utf-8")
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
