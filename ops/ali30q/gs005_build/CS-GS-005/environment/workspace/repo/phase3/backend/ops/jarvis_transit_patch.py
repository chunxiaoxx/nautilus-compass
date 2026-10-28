#!/usr/bin/env python3
"""贾维斯透传补丁 · 平台代部署(V5 域透明变更,回执 253 部署缺口)。

对 /home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py 做两处精确改动:
① callback 开头保留原始字节(raw)供透传(签名对字节生效,dict 重序列化会破坏)
② im.message 且平台 p2p 会话 → 原始字节透传平台 /feishu/cmd(签名透传,fail-soft)

变更身份:platform 代部署(commit 署名),回滚=git revert 本 commit。
"""
import sys
from pathlib import Path

P = Path("/home/ubuntu/nautilus-v5/fde_capsule/feishu/callback_app.py")
src = P.read_text(encoding="utf-8")

OLD_OPEN = """    @host.post("/api/feishu/callback")
    async def callback(req: Request, bg: BackgroundTasks):
        try:
            body = await req.json()
        except Exception:
            return {}
"""
NEW_OPEN = """    @host.post("/api/feishu/callback")
    async def callback(req: Request, bg: BackgroundTasks):
        raw = await req.body()  # 2026-09-15 jarvis:保留原始字节(签名对字节生效)
        try:
            import json as _json
            body = _json.loads(raw)
        except Exception:
            return {}
"""
assert src.count(OLD_OPEN) == 1, "anchor 1 not unique/found"
src = src.replace(OLD_OPEN, NEW_OPEN)

OLD_CARD = """            logger.info("decision card forwarded=%s resp=%s", forwarded, resp)
            return resp
"""
NEW_CARD = """            logger.info("decision card forwarded=%s resp=%s", forwarded, resp)
            return resp

        # 贾维斯 v0(2026-09-15 · 平台代部署,见 platform-v5-jarvis-deploy-gap-20260915):
        # im.message 且平台 p2p 会话 → 原始字节透传平台 /feishu/cmd(body 不动+签名
        # 透传;dict 重序列化会破坏验签)。fail-soft:透传异常不吞事件,走原逻辑。
        if (isinstance(body, dict)
                and (body.get("header") or {}).get("event_type") == "im.message.receive_v1"
                and (((body.get("event") or {}).get("message")) or {}).get("chat_id")
                == "oc_c9fbb71be60e8d64fb0c854078b05847"):
            try:
                import urllib.request as _rq
                _req = _rq.Request(
                    f"{PLATFORM_BASE}/api/platform/feishu/cmd",
                    data=raw, method="POST",
                    headers={"Content-Type": "application/json",
                             "X-Lark-Signature": req.headers.get("x-lark-signature") or ""})
                with _rq.urlopen(_req, timeout=90) as _resp:
                    logger.info("jarvis transit resp=%s", _resp.status)
                return {"code": 0, "note": "jarvis forwarded"}
            except Exception as e:  # noqa: BLE001 — 透传失败落到原 chat 逻辑
                logger.warning("jarvis transit err: %s", e)
"""
assert src.count(OLD_CARD) == 1, "anchor 2 not unique/found"
src = src.replace(OLD_CARD, NEW_CARD)

P.write_text(src, encoding="utf-8")
print("patched OK", P)
import py_compile
py_compile.compile(str(P), doraise=True)
print("py_compile OK")
