"""区分实验:知乎 write 页 + 纯文本剪贴板 + CDP Ctrl+V。
若纯文本能贴进正文(len>0)→ 知乎不拦粘贴,CF_HTML(HTML Format)通道坏;
若 len=0 → 知乎页层拦截(编辑器/弹窗)。"""
import asyncio
import json
import subprocess
import urllib.request

import websockets

PORT = 9225


async def main():
    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
    t = next((x for x in tabs if x["type"] == "page"
              and "zhihu.com/write" in x.get("url", "")), None)
    if t is None:  # tab 不在 write 页:抓任一非 about 页导航过去(导航后重连)
        t = next(x for x in tabs if x["type"] == "page")
        tmp = await websockets.connect(t["webSocketDebuggerUrl"],
                                       max_size=20 * 1024 * 1024)
        await tmp.send(json.dumps({"id": 1, "method": "Page.navigate",
                                   "params": {"url": "https://zhuanlan.zhihu.com/write"}}))
        await asyncio.sleep(8)
        await tmp.close()
        tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
        t = next(x for x in tabs if x["type"] == "page"
                 and "zhihu.com/write" in x.get("url", ""))
    ws = await websockets.connect(t["webSocketDebuggerUrl"], max_size=20 * 1024 * 1024)
    mid = 0

    async def send(method, params):
        nonlocal mid
        mid += 1
        await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            m = json.loads(await ws.recv())
            if m.get("id") == mid:
                return m

    async def ev(expr):
        r = await send("Runtime.evaluate", {"expression": expr,
                                            "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    await send("Page.bringToFront", {})
    f = await ev('var e=document.querySelector("[contenteditable=true]");'
                 'if(e){e.focus();"focused:"+document.hasFocus()}else{"no-editor"}')
    print("focus:", f)
    await asyncio.sleep(0.5)
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    'Set-Clipboard -Value "PLAINTEXT_PASTE_TEST_98765"'],
                   capture_output=True)
    for t_ in ("keyDown", "keyUp"):
        await send("Input.dispatchKeyEvent",
                   {"type": t_, "key": "v", "code": "KeyV",
                    "windowsVirtualKeyCode": 86, "modifiers": 2})
    await asyncio.sleep(2)
    v = await ev('(document.querySelector("[contenteditable=true]")'
                 '||{textContent:"?"}).textContent.length')
    print("知乎正文纯文本 Ctrl+V 后 len:", v)
    await ws.close()

asyncio.run(main())
