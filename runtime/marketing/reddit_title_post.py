# -*- coding: utf-8 -*-
"""Reddit:shadow 内补标题+坐标点发布(9226 CDP)。"""
import asyncio
import json
import urllib.request
import websockets

TITLE = 'We fact-checked an AI performance claim by clicking the ("(proof)") link. There is no link.'


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

    # shadow 内标题框重填
    print("title:", await ev(f"""(function(){{
      var el = null;
      function walk(root){{
        var els = root.querySelectorAll('textarea');
        for (var i=0;i<els.length;i++){{
          if (els[i].getAttribute('placeholder') === '标题' || /标题/.test(els[i].getAttribute('placeholder')||'')) {{ el = els[i]; }}
        }}
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){{ if (kids[j].shadowRoot) walk(kids[j].shadowRoot); }}
      }}
      walk(document);
      if(!el) return 'no-title';
      el.focus();
      el.select && el.select();
      document.execCommand('insertText', false, "{esc(TITLE)}");
      return 'title_len=' + el.value.length;
    }})()"""))
    await asyncio.sleep(2)
    # 发布(坐标)
    await send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 1895, "y": 1335, "button": "left", "clickCount": 1})
    await send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 1895, "y": 1335, "button": "left", "clickCount": 1})
    await asyncio.sleep(12)
    print("after:", await ev("location.href.slice(0,120)"))
    await ws.close()

asyncio.run(main())
