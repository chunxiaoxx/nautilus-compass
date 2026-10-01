# -*- coding: utf-8 -*-
"""Reddit 自动发布·页内同源 fetch 方案(已登录 tab,零 recaptcha)。
用法:python tools/reddit_publish_inpage.py <body_file> [subreddit] [title]
原理:在登录态 tab 里 fetch('/api/submit'),浏览器自带 cookie/modhash。"""
import asyncio
import json
import sys
import urllib.request
import websockets

TITLE = ('We fact-checked an AI performance claim by clicking the "(proof)" link. '
         'There is no link.')
SUB = "LocalLLaMA"


async def main():
    body_file = sys.argv[1] if len(sys.argv) > 1 else "runtime/marketing/_reddit_body.txt"
    body = open(body_file, encoding="utf-8").read().strip()

    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9226/json"))
    red = [t for t in tabs if t["type"] == "page" and "reddit.com" in t.get("url", "")]
    if not red:
        raise SystemExit("no reddit tab (open reddit.com in 9226 first)")
    ws = await websockets.connect(red[0]["webSocketDebuggerUrl"], max_size=30 * 1024 * 1024,
                                  ping_interval=15)
    mid = 0

    async def ev(js, timeout=30):
        nonlocal mid; mid += 1
        import time; t0 = time.time()
        await ws.send(json.dumps({"id": mid, "method": "Runtime.evaluate",
                                  "params": {"expression": js,
                                             "awaitPromise": True,
                                             "returnByValue": True}}))
        while time.time() - t0 < timeout:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if m.get("id") == mid:
                return m.get("result", {}).get("result", {}).get("value")
        return "TIMEOUT"

    payload = json.dumps({"api_type": "json", "sr": SUB, "kind": "self",
                          "title": TITLE, "text": body})
    res = await ev(f"""fetch('/api/submit', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/x-www-form-urlencoded'}},
        body: new URLSearchParams({json.dumps({"api_type":"json","sr":SUB,"kind":"self","title":TITLE,"text":body})}).toString(),
        credentials: 'same-origin'
      }}).then(function(r){{ return r.text(); }}).catch(function(e){{ return 'FETCH_ERR:' + e; }})""")
    print("api_result:", str(res)[:500])
    await ws.close()

asyncio.run(main())
