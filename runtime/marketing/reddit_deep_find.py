# -*- coding: utf-8 -*-
"""深搜(含 shadow root)全部可编辑元素,打印定位信息。"""
import asyncio
import json
import urllib.request
import websockets


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

    print(await ev("""(function(){
      var out = [];
      function walk(root, path){
        var els = root.querySelectorAll('textarea, [contenteditable=true], [rte-surface]');
        for (var i=0;i<els.length;i++){
          var e = els[i];
          out.push(path + '>' + e.tagName + '|ph=' + (e.getAttribute('placeholder')||'').slice(0,20)
                   + '|rte=' + (e.getAttribute('rte-surface')||'')
                   + '|len=' + ((e.value!==undefined?e.value:e.textContent)||'').length
                   + '|rect=' + JSON.stringify((e.getBoundingClientRect&&{x:Math.round(e.getBoundingClientRect().x),y:Math.round(e.getBoundingClientRect().y)})||null));
        }
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){
          if (kids[j].shadowRoot) walk(kids[j].shadowRoot, path + '/' + kids[j].tagName);
        }
      }
      walk(document, '');
      return JSON.stringify(out, null, 1);
    })()"""))
    await ws.close()

asyncio.run(main())
