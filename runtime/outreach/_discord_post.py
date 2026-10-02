"""Discord 判官招募短讯(9226 CDP;9/27 配方:role=textbox 定位+insertText+Enter 发送)。"""
import asyncio
import base64
import json
import urllib.request

import websockets

PORT = 9226
TEXT = ('We pay people to say "insufficient evidence" — recruiting human '
        'gold-standard judges for AI grader calibration. Three-state verdicts '
        '(pass/fail/insufficient), pre-registered criteria, every verdict '
        'independently recomputed with ed25519-signed receipts. ¥65/seat+. '
        'Apply: https://github.com/Nautilus-agent/compass/issues/2')


async def main():
    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
    t = next(x for x in tabs if x["type"] == "page"
             and "discord.com/channels" in x.get("url", ""))
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
    box = await ev('var b=document.querySelector("div[role=textbox]");'
                   'if(b){b.focus();"ok"}else{"no-box"}')
    print("input box:", box)
    if box != "ok":
        return
    await send("Input.insertText", {"text": TEXT})
    await asyncio.sleep(1)
    await send("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "Enter", "code": "Enter",
        "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13, "text": "\r"})
    await send("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": "Enter", "code": "Enter",
        "windowsVirtualKeyCode": 13})
    await asyncio.sleep(3)
    last = await ev(
        '(document.querySelector("[id^=message-content]")||{textContent:""})'
        '.textContent.slice(0, 60)')
    print("频道最新消息头:", last)
    r = await send("Page.captureScreenshot", {"format": "png"})
    open("runtime/discord_judge_20261003.png", "wb").write(
        base64.b64decode(r["result"]["data"]))
    print("截图: runtime/discord_judge_20261003.png")
    await ws.close()

asyncio.run(main())
