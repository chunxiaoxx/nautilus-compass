# -*- coding: utf-8 -*-
"""知乎 BC1 最终填入:关污染 tab→全新 write 页→标题 setter+正文(焦点验证后 insertText)。"""
import asyncio
import json
import re
import urllib.request
import base64
import websockets

MD = open("runtime/assay_bc1_20260927/BC1_LAUNCH_CN_DRAFT.md", encoding="utf-8").read()
TITLE = "我们给自己的 AI 组织出了场考试:首考 11/18,错的 7 题全在出题方"


def md_to_plain(md):
    lines = []
    for ln in md.splitlines():
        s = ln.rstrip()
        if not s.strip():
            lines.append("")
            continue
        s = re.sub(r"^###\s*", "■ ", s)
        s = re.sub(r"^##\s*", "■ ", s)
        s = re.sub(r"^#\s*", "■ ", s)
        if s.lstrip().startswith('>'):
            continue  # 备稿注记整行不入正文
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1(\2)", s)
        s = re.sub(r"^-{3,}$", "", s)
        lines.append(s)
    out, skip = [], True
    for l in lines:
        if skip:
            if l.startswith("■ ") or not l.strip():
                continue
            skip = False
        out.append(l)
    return "\n".join(out).strip()


async def main():
    body = md_to_plain(MD)
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json"))
    for t in tabs:
        if "/edit" in t.get("url", ""):
            try:
                urllib.request.urlopen(
                    f"http://127.0.0.1:9225/json/close/{t['id']}", timeout=5)
                print("closed", t["url"][-16:])
            except Exception as e:
                print("close err", type(e).__name__)
    req = urllib.request.Request(
        "http://127.0.0.1:9225/json/new?https://zhuanlan.zhihu.com/write", method="PUT")
    json.load(urllib.request.urlopen(req, timeout=10))
    await asyncio.sleep(14)
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json"))
    wt = [t for t in tabs if "zhuanlan" in t.get("url", "")][0]
    print("fresh tab:", wt["url"][-22:])
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

    esc_t = TITLE.replace("\\", "\\\\").replace('"', '\\"')
    print("title:", await ev(f"""(function(){{
      var ta = document.querySelector('textarea[placeholder*="标题"]');
      if(!ta) return 'no-title';
      var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
      setter.call(ta, "{esc_t}");
      ta.dispatchEvent(new Event('input', {{bubbles:true}}));
      return 'ok:' + ta.value.length;
    }})()"""))
    pos = await ev("""(function(){
      var e = document.querySelector('.public-DraftEditor-content[contenteditable=true]') ||
              document.querySelectorAll('[contenteditable=true]')[0];
      if(!e) return null;
      var r = e.getBoundingClientRect();
      return JSON.stringify({x: Math.round(r.x + r.width/2), y: Math.round(r.y + 20)});
    })()""")
    print("editor pos:", pos)
    p = json.loads(pos)
    await send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": p["x"], "y": p["y"]})
    await send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": p["x"], "y": p["y"], "button": "left", "clickCount": 1})
    await send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": p["x"], "y": p["y"], "button": "left", "clickCount": 1})
    await asyncio.sleep(0.8)
    foc = await ev("(document.activeElement||{}).className?.toString().slice(0,36) || (document.activeElement||{}).tagName")
    print("focus:", foc)
    if "DraftEditor" in str(foc) or "contenteditable" in str(foc).lower():
        await send("Input.insertText", {"text": body})
        await asyncio.sleep(3)
        print("verify:", await ev("""(function(){
          var e = document.querySelector('.public-DraftEditor-content[contenteditable=true]');
          var t = (e && e.innerText || '').replace(/\\s+/g,' ');
          return JSON.stringify({len: t.length, head: t.slice(0,40), tail: t.slice(-40)});
        })()"""))
        shot = await send("Page.captureScreenshot", {"format": "jpeg", "quality": 50})
        open("runtime/marketing/zhihu_final_check.jpg", "wb").write(
            base64.b64decode(shot["result"]["data"]))
        print("shot saved")
    else:
        print("FOCUS FAIL — 未插入")
    await ws.close()

asyncio.run(main())
