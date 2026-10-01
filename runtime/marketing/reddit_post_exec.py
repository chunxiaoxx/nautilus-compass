# -*- coding: utf-8 -*-
"""Reddit r/LocalLLaMA 发帖(9226 CDP · execCommand 配方)。
前置:submit 页已开且已登录;标题/正文从稿文件读。"""
import asyncio
import json
import sys
import urllib.request
import websockets

TITLE = "We fact-checked an AI performance claim by clicking the \"(proof)\" link. There is no link."
BODY = open("runtime/marketing/_reddit_body.txt", encoding="utf-8").read().strip()


async def main():
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9226/json"))
    red = [t for t in tabs if t["type"] == "page" and "reddit.com" in t.get("url", "")]
    if not red:
        print("no reddit tab"); sys.exit(2)
    ws = await websockets.connect(red[0]["webSocketDebuggerUrl"], max_size=20 * 1024 * 1024)
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

    def esc(s):
        return (s.replace("\\", "\\\\").replace('"', '\\"')
                 .replace("\n", "\\n").replace("\r", ""))

    # 1) 找标题输入框并填(fallback:textarea/ input 按顺序试)
    print("title_fill:", await ev(f'''(function(){{
      var cands = [].concat(
        Array.from(document.querySelectorAll('textarea[placeholder*="itle"], input[placeholder*="itle"]')),
        Array.from(document.querySelectorAll('textarea')).slice(0,2));
      for (var i=0;i<cands.length;i++){{
        var el = cands[i];
        el.focus();
        document.execCommand('selectAll', false, null);
        document.execCommand('insertText', false, "{esc(TITLE)}");
        return 'filled:' + (el.getAttribute('placeholder')||el.tagName);
      }}
      return 'no-title-input';
    }})()'''))

    # 2) 正文(最大的/第二个 textarea 或 [placeholder*=正文/Text])
    print("body_fill:", await ev(f'''(function(){{
      var cands = Array.from(document.querySelectorAll('textarea'));
      var el = cands.length > 1 ? cands[cands.length-1] : cands[0];
      if(!el) return 'no-textarea';
      el.focus();
      el.select();
      document.execCommand('insertText', false, "{esc(BODY)}");
      return 'filled_len=' + el.value.length;
    }})()'''))
    await ws.close()

asyncio.run(main())
