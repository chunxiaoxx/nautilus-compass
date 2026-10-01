# -*- coding: utf-8 -*-
"""Reddit 发帖一把梭:fresh reload→Markdown→shadow 深搜填标题/正文→发布→验证。"""
import asyncio
import base64
import json
import urllib.request
import websockets

TITLE = 'We fact-checked an AI performance claim by clicking the ("(proof)") link. There is no link.'
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

    async def send(method, params, timeout=20):
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

    # 0) fresh reload(navigate 会重建 target→导航后重取 ws)
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9226/json"))
    red = [t for t in tabs if t["type"] == "page" and "reddit.com" in t.get("url", "")]
    await send("Page.navigate", {"url": "https://www.reddit.com/r/LocalLLaMA/submit/?type=TEXT"})
    await asyncio.sleep(3)
    await ws.close()
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9226/json"))
    red = [t for t in tabs if t["type"] == "page" and "reddit.com" in t.get("url", "")]
    ws = await websockets.connect(red[0]["webSocketDebuggerUrl"],
                                  max_size=30 * 1024 * 1024, ping_interval=20)
    mid = 0
    await asyncio.sleep(12)
    print("url:", await ev("location.href.slice(0,70)"))

    # 1) 先切 Markdown(填之前,内容保留)
    print("md:", await ev("""(function(){
      function find(root, pred){
        var els = root.querySelectorAll('button');
        for (var i=0;i<els.length;i++){
          if (pred(els[i])) return els[i];
        }
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){
          if (kids[j].shadowRoot){ var r = find(kids[j].shadowRoot, pred); if (r) return r; }
        }
        return null;
      }
      var b = find(document, function(x){
        var t=(x.textContent||'').trim();
        return t.indexOf('切换到 Markdown')===0 || t.indexOf('Switch to Markdown')===0;
      });
      if (!b) return 'no-md-btn';
      b.click(); return 'md-clicked';
    })()"""))
    await asyncio.sleep(6)

    # 2) shadow 深搜填标题+正文(placeholder 精确匹配,只挑可见实例)
    print("fill:", await ev(f"""(function(){{
      var title=null, body=null;
      function walk(root){{
        var els = root.querySelectorAll('textarea');
        for (var i=0;i<els.length;i++){{
          var e = els[i]; var ph = e.getAttribute('placeholder')||'';
          var r = e.getBoundingClientRect();
          if (r.width === 0) continue;
          if (/标题|Title/.test(ph) && !title) title = e;
          if (/正文|Text/.test(ph) && !body) body = e;
        }}
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){{ if (kids[j].shadowRoot) walk(kids[j].shadowRoot); }}
      }}
      walk(document);
      if (!title || !body) return 'missing t=' + !!title + ' b=' + !!body;
      title.focus(); title.select && title.select();
      document.execCommand('insertText', false, "{esc(TITLE)}");
      body.focus(); body.select && body.select();
      document.execCommand('insertText', false, "{esc(BODY)}");
      return 't=' + title.value.length + ' b=' + body.value.length;
    }})()"""))
    await asyncio.sleep(3)

    # 3) 发布(shadow 深搜按钮精确文本,found 多个取最后=主操作钮)
    print("post:", await ev("""(function(){
      var found = [];
      function walk(root){
        var els = root.querySelectorAll('button');
        for (var i=0;i<els.length;i++){
          var t = (els[i].textContent||'').trim();
          if (t === '发布' || t === 'Post') {
            var r = els[i].getBoundingClientRect();
            if (r.width > 0) found.push(els[i]);
          }
        }
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){ if (kids[j].shadowRoot) walk(kids[j].shadowRoot); }
      }
      walk(document);
      if (!found.length) return 'no-btn';
      var b = found[found.length-1];
      if (b.disabled) return 'btn-disabled';
      b.click();
      return 'clicked';
    })()"""))
    await asyncio.sleep(14)
    print("after:", await ev("location.href.slice(0,120)"))

    # 4) 未跳转→截图收兵
    href = await ev("location.href")
    if "/submit" in str(href):
        try:
            r = await send("Page.captureScreenshot", {"format": "jpeg", "quality": 55}, timeout=20)
            open("runtime/marketing/reddit_oneshot_fail.jpg", "wb").write(
                base64.b64decode(r["result"]["data"]))
            print("fail-shot saved")
        except Exception as e:
            print("shot err:", type(e).__name__)
    await ws.close()

asyncio.run(main())
