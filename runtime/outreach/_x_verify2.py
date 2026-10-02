"""X 验证(新 tab 直取 profile 首条推文,避开挂起的旧 tab)。"""
import asyncio
import json
import urllib.request

import websockets

PORT = 9226


async def main():
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/json/new?https://x.com/chunxiaoxx",
        method="PUT")
    tab = json.load(urllib.request.urlopen(req, timeout=15))
    ws = await websockets.connect(tab["webSocketDebuggerUrl"],
                                  max_size=20 * 1024 * 1024)
    mid = 0

    async def ev(expr):
        nonlocal mid
        mid += 1
        await ws.send(json.dumps({"id": mid, "method": "Runtime.evaluate",
                                  "params": {"expression": expr,
                                             "returnByValue": True}}))
        while True:
            m = json.loads(await ws.recv())
            if m.get("id") == mid:
                return m.get("result", {}).get("result", {}).get("value")

    for wait in (10, 8, 8):  # 三段等 X 虚拟列表渲染
        await asyncio.sleep(wait)
        n = await ev('document.querySelectorAll("article").length')
        if isinstance(n, int) and n > 0:
            first = await ev(
                '(document.querySelector("article")||{innerText:""})'
                '.innerText.replace(/\\n/g," | ").slice(0, 200)')
            print("article 数:", n)
            print("首条:", first)
            break
        print(f"等待… article={n}")
    else:
        print("三段等待后仍无 article")
    # 关闭验证 tab
    mid += 1
    await ws.send(json.dumps({"id": mid, "method": "Target.closeTarget",
                              "params": {"targetId": tab["id"]}}))
    await ws.close()

asyncio.run(main())
