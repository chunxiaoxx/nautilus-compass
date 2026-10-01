# -*- coding: utf-8 -*-
"""Reddit:诊断发布卡点(错误提示/按钮态/必要字段)。"""
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

    async def send(method, params, timeout=12):
        nonlocal mid; mid += 1
        await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        import time; t0 = time.time()
        while time.time() - t0 < timeout:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if m.get("id") == mid:
                return m
        raise TimeoutError(method)

    async def ev(js):
        r = await send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    print(await ev("""(function(){
      var errs = [];
      function walk(root){
        var els = root.querySelectorAll('[class*=error], [class*=Error], [aria-live], [role=alert]');
        for (var i=0;i<els.length;i++){
          var t = (els[i].textContent||'').trim();
          if (t && t.length < 200) errs.push(t.slice(0,120));
        }
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){ if (kids[j].shadowRoot) walk(kids[j].shadowRoot); }
      }
      walk(document);
      var pub = null;
      function walk2(root){
        var els = root.querySelectorAll('button');
        for (var i=0;i<els.length;i++){
          var t = (els[i].textContent||'').trim();
          if (t === '发布' || t === 'Post') pub = els[i];
        }
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){ if (kids[j].shadowRoot) walk2(kids[j].shadowRoot); }
      }
      walk2(document);
      return JSON.stringify({errors: errs.slice(0,6),
        post_btn: pub ? {label: pub.textContent.trim().slice(0,10), disabled: pub.disabled} : 'none'});
    })()"""))
    await ws.close()

asyncio.run(main())
