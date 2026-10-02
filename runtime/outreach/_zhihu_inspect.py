"""知乎 write 页现场观测:全部 contenteditable 元素+粘贴事件层打点+截图。
目的:区分『检测错位(假阴性)』vs『粘贴真没进』。"""
import asyncio
import base64
import json
import subprocess
import urllib.request

import websockets

PORT = 9225


async def main():
    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
    t = next((x for x in tabs if x["type"] == "page"
              and "zhihu.com/write" in x.get("url", "")), None)
    if t is None:
        print("write tab 不在;当前 tabs:", [x.get("url", "")[:60] for x in tabs if x["type"] == "page"])
        return
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
    await asyncio.sleep(1)
    info = await ev(
        'JSON.stringify(Array.from(document.querySelectorAll("[contenteditable=true]"))'
        '.map(function(e,i){return {i:i, cls:e.className.slice(0,50), '
        'len:e.textContent.length, '
        'txt:e.textContent.slice(0,40), '
        'rect:(function(){var r=e.getBoundingClientRect();'
        'return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)]})()}}))')
    print("contenteditable 全列:", info)
    # 挂 paste 事件监听(下一轮粘贴时打点到 window.__pasteLog)
    await ev(
        'window.__pasteLog=[];'
        'document.addEventListener("paste", function(ev){'
        'window.__pasteLog.push({t:Date.now(), '
        'target:ev.target.className.slice(0,40), '
        'textLen:(ev.clipboardData||{}).getData?ev.clipboardData.getData("text/plain").length:-1,'
        'htmlLen:(ev.clipboardData||{}).getData?ev.clipboardData.getData("text/html").length:-1})}, true)')
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    'Set-Clipboard -Value "PROBE_TXT_ABCDEF"'], capture_output=True)
    await ev('var e=document.querySelector("[contenteditable=true]");if(e){e.focus();document.hasFocus()}')
    await asyncio.sleep(0.3)
    for t_ in ("keyDown", "keyUp"):
        await send("Input.dispatchKeyEvent",
                   {"type": t_, "key": "v", "code": "KeyV",
                    "windowsVirtualKeyCode": 86, "modifiers": 2})
    await asyncio.sleep(2)
    log = await ev("JSON.stringify(window.__pasteLog)")
    after = await ev(
        'JSON.stringify(Array.from(document.querySelectorAll("[contenteditable=true]"))'
        '.map(function(e){return e.textContent.length}))')
    print("paste 事件日志:", log)
    print("粘贴后各 contenteditable len:", after)
    r = await send("Page.captureScreenshot", {"format": "png"})
    open("runtime/zhihu_inspect_20261003.png", "wb").write(
        base64.b64decode(r["result"]["data"]))
    print("截图: runtime/zhihu_inspect_20261003.png")
    await ws.close()

asyncio.run(main())
