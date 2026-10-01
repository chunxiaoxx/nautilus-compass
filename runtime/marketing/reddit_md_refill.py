# -*- coding: utf-8 -*-
"""Reddit:切 Markdown 模式+重填正文+找发布钮(9226 CDP)。"""
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
    ws = await websockets.connect(red[0]["webSocketDebuggerUrl"], max_size=30 * 1024 * 1024)
    mid = 0

    async def send(method, params):
        nonlocal mid; mid += 1
        await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            m = json.loads(await ws.recv())
            if m.get("id") == mid:
                return m

    async def ev(js):
        r = await send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")

    print("switch_md:", await ev("""(function(){
      var btns = Array.from(document.querySelectorAll('button'));
      var b = btns.find(function(x){return (x.textContent||'').trim().indexOf('切换到 Markdown')===0;});
      if(!b) return 'no-md-btn';
      b.click(); return 'clicked';
    })()"""))
    await asyncio.sleep(5)
    print("refill:", await ev(f"""(function(){{
      var els = Array.from(document.querySelectorAll('textarea, div[contenteditable=true]'));
      var el = null;
      for (var i=els.length-1;i>=0;i--){{
        var e = els[i];
        var ph = (e.getAttribute('placeholder')||'') + (e.getAttribute('aria-label')||'');
        if (/正文|body|text/i.test(ph) || e.getAttribute('data-lexical-editor')!==null) {{ el = e; break; }}
      }}
      if(!el && els.length) el = els[els.length-1];
      if(!el) return 'no-editor';
      el.focus();
      el.select && el.select();
      document.execCommand('selectAll', false, null);
      document.execCommand('insertText', false, "{esc(BODY)}");
      var len = (el.value || el.textContent || '').length;
      return 'refilled:' + len + '|' + el.tagName;
    }})()"""))
    await asyncio.sleep(2)
    # 找发布钮(全 DOM 深搜,文本含 发布/Post/Submit)
    print("post_btn:", await ev("""(function(){
      var found = [];
      function walk(root){
        var els = root.querySelectorAll('button, [role=button]');
        for (var i=0;i<els.length;i++){
          var t = (els[i].textContent||'').trim();
          if (/^(发布|Post|提交|Submit)/.test(t)) found.push(els[i]);
          if (els[i].shadowRoot) walk(els[i].shadowRoot);
        }
        var kids = root.querySelectorAll('*');
        for (var j=0;j<kids.length;j++){ if (kids[j].shadowRoot) walk(kids[j].shadowRoot, undefined); }
      }
      walk(document);
      if(!found.length) return 'no-post-btn:' + found.length;
      var b = found[found.length-1];
      return 'FOUND label=' + b.textContent.trim().slice(0,12) + ' disabled=' + b.disabled + ' tag=' + b.tagName;
    })()"""))
    await ws.close()

asyncio.run(main())
