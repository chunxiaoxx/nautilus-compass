# -*- coding: utf-8 -*-
"""Reddit:markdown 编辑器重填+坐标点击发布(9226 CDP)。"""
import asyncio
import json
import urllib.request
import websockets

BODY = open("runtime/marketing/_reddit_body.txt", encoding="utf-8").read().strip()


def esc(s):
    return (s.replace("\\", "\\\\").replace('"', '\\"')
             .replace("\n", "\\n").replace("\r", ""))


async def main():
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9226/json"))
    red = [t for t in tabs if t["type"] == "page" and "reddit.com" in t.get("url", "")]
    ws = await websockets.connect(red[0]["webSocketDebuggerUrl"],
                                  max_size=30 * 1024 * 1024, ping_interval=20)
    mid = 0

    async def send(method, params, timeout=15):
        nonlocal mid; mid += 1
        await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        import time
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if m.get("id") == mid:
                return m
        raise TimeoutError(method)

    async def ev(js):
        r = await send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    # 1) markdown 编辑器(rte-surface textarea 或含 placeholder 的 div contenteditable)
    res = await ev(f"""(function(){{
      var el = document.querySelector('textarea[rte-surface], text-area[rte-surface]');
      if (!el) {{
        var cds = Array.from(document.querySelectorAll('div[contenteditable=true]'));
        el = cds[cds.length-1];
      }}
      if (!el) return 'no-editor';
      el.focus();
      el.select && el.select();
      document.execCommand('selectAll', false, null);
      var ok = document.execCommand('insertText', false, "{esc(BODY)}");
      var len = (el.value !== undefined ? el.value : el.textContent).length;
      return 'filled ok=' + ok + ' len=' + len + ' tag=' + el.tagName;
    }})()""")
    print("fill:", res)
    if not str(res).startswith("filled") or "len=0" in str(res):
        print("FILL FAIL — abort"); await ws.close(); return
    await asyncio.sleep(2)
    # 2) 坐标点击发布钮(截图原图坐标 ~1895,1335;viewport=截图分辨率)
    await send("Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": 1895, "y": 1335,
        "button": "left", "clickCount": 1})
    await send("Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": 1895, "y": 1335,
        "button": "left", "clickCount": 1})
    await asyncio.sleep(12)
    print("after:", await ev("location.href.slice(0,120)"))
    await ws.close()

asyncio.run(main())
