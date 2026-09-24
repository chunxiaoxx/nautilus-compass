# -*- coding: utf-8 -*-
"""CDP tool for the 9224 Discord chrome. Usage:
python cdp_tool.py shot [out.png]
python cdp_tool.py eval "<js expr>"
python cdp_tool.py nav <url>
python cdp_tool.py lastid            # 读当前频道最新消息 id+文本+直链(发帖后立即存档!)

已知限制(2026-09-24 实测,Chrome 153):
- Input.dispatchMouseEvent(type=mouseWheel) 无响应(其他 Input 事件正常)——无法程序化翻历史
- 键盘 PageUp 事件被接受但不触发 Discord 滚动
→ 翻历史不可行;值守靠「发帖后 lastid 存直链 → nav 直达」;盯帖快查用徽标/提及按钮法。
"""
import asyncio
import base64
import json
import sys
import urllib.request

import websockets

PORT = 9224

JS_LAST = ('(function(){var ls=document.querySelectorAll("li[id^=chat-messages]");'
           'var l=ls[ls.length-1];if(!l)return JSON.stringify({error:"no-msg"});'
           'var parts=l.id.split("-");var msgId=parts[parts.length-1];'
           'return JSON.stringify({msgId:msgId,'
           'link:location.origin+location.pathname+"/"+msgId,'
           'text:l.textContent.slice(0,300)})})()')


def page_ws():
    data = json.load(urllib.request.urlopen(
        f"http://127.0.0.1:{PORT}/json", timeout=5))
    for t in data:
        if t["type"] == "page" and "discord" in t.get("url", ""):
            return t["webSocketDebuggerUrl"]
    for t in data:
        if t["type"] == "page":
            return t["webSocketDebuggerUrl"]
    raise SystemExit("no page target")


async def main():
    cmd = sys.argv[1]
    ws_url = page_ws()
    async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as ws:
        mid = 0

        async def send(method, params=None):
            nonlocal mid
            mid += 1
            await ws.send(json.dumps({"id": mid, "method": method,
                                      "params": params or {}}))
            while True:
                m = json.loads(await ws.recv())
                if m.get("id") == mid:
                    if "error" in m:
                        raise RuntimeError(m["error"]["message"])
                    return m.get("result", {})

        if cmd == "shot":
            res = await send("Page.captureScreenshot", {"format": "png"})
            out = sys.argv[2] if len(sys.argv) > 2 else "cdp_shot.png"
            with open(out, "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print("saved", out)
        elif cmd == "eval":
            res = await send("Runtime.evaluate",
                             {"expression": sys.argv[2], "returnByValue": True})
            print(json.dumps(res.get("result", {}).get("value"),
                             ensure_ascii=False)[:3000])
        elif cmd == "nav":
            await send("Page.navigate", {"url": sys.argv[2]})
            print("navigated")
        elif cmd == "lastid":
            res = await send("Runtime.evaluate",
                             {"expression": JS_LAST, "returnByValue": True})
            print(res.get("result", {}).get("value"))
        else:
            print("unknown cmd:", cmd)


asyncio.run(main())
