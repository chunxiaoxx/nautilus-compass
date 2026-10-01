# -*- coding: utf-8 -*-
"""知乎:添加话题(人工智能)+尝试发布(底部确认条)。"""
import asyncio
import json
import urllib.request
import base64
import websockets


async def main():
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json"))
    wt = [t for t in tabs if "zhuanlan" in t.get("url", "")][0]
    ws = await websockets.connect(wt["webSocketDebuggerUrl"],
                                  max_size=30 * 1024 * 1024, ping_interval=15)
    mid = 0

    async def send(method, params, timeout=25):
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

    # 1) 找「添加话题」按钮并点
    r = await ev("""(function(){
      var btns = Array.from(document.querySelectorAll('button, [role=button], div'));
      var t = btns.find(function(b){
        return (b.textContent||'').trim().startsWith('添加话题') && b.getBoundingClientRect().width > 0;
      });
      if(!t) return 'no-topic-btn';
      t.click();
      return 'topic-clicked';
    })()""")
    print("topic:", r)
    await asyncio.sleep(2)
    # 2) 搜「人工智能」(弹搜索框)→输入→选第一个候选
    r2 = await ev("""(function(){
      var inp = document.querySelector('input[placeholder*="话题"], input[placeholder*="搜索"]');
      if(!inp) return 'no-search-input';
      var setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
      setter.call(inp, '人工智能');
      inp.dispatchEvent(new Event('input', {bubbles:true}));
      return 'typed';
    })()""")
    print("search:", r2)
    await asyncio.sleep(3)
    # 3) 点第一个候选(列表项含 人工智能)
    r3 = await ev("""(function(){
      var items = Array.from(document.querySelectorAll('li, [class*=option], [class*=item]'));
      var hit = items.find(function(i){
        var t = (i.textContent||'').trim();
        return /^人工智能/.test(t) && t.length < 40 && i.getBoundingClientRect().width > 0;
      });
      if(!hit) return 'no-candidate';
      hit.click();
      return 'selected:' + (hit.textContent||'').trim().slice(0,15);
    })()""")
    print("select:", r3)
    await asyncio.sleep(2)
    shot = await send("Page.captureScreenshot", {"format": "jpeg", "quality": 50})
    open("runtime/marketing/zhihu_topic_added.jpg", "wb").write(
        base64.b64decode(shot["result"]["data"]))
    print("shot saved")
    await ws.close()

asyncio.run(main())
