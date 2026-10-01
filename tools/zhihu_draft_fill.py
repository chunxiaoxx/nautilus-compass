# -*- coding: utf-8 -*-
"""知乎 BC1 填入(Draft.js 兼容:标题 React 受控 setter+正文 CDP Input.insertText 系统级输入)。"""
import asyncio
import json
import re
import sys
import urllib.request
import websockets

TITLE = "我们给自己的 AI 组织出了场考试:首考 11/18,错的 7 题全在出题方"
MD = open("runtime/assay_bc1_20260927/BC1_LAUNCH_CN_DRAFT.md", encoding="utf-8").read()


def md_to_plain(md: str) -> str:
    """纯文本版(保链接 URL 文本,粗体转普通文本,标题加【】)。"""
    lines = []
    for ln in md.splitlines():
        s = ln.rstrip()
        if not s.strip():
            lines.append("")
            continue
        s = re.sub(r"^###\s*", "■ ", s)
        s = re.sub(r"^##\s*", "■ ", s)
        s = re.sub(r"^#\s*", "■ ", s)
        s = re.sub(r">\s*", "", s)
        s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1(\2)", s)
        s = re.sub(r"^-{3,}$", "", s)
        s = re.sub(r"^---$", "", s)
        lines.append(s)
    # 去头(稿元数据块:第一个 --- 前的)
    txt = "\n".join(lines)
    return txt.strip()


async def main():
    body = md_to_plain(MD)
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9225/json"))
    wt = ([x for x in tabs if "/write" in x.get("url", "")] or tabs)[0]
    ws = await websockets.connect(wt["webSocketDebuggerUrl"], max_size=30 * 1024 * 1024,
                                  ping_interval=15)
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

    # 1) 标题(React 受控:native setter + input 事件)
    esc_t = TITLE.replace("\\", "\\\\").replace('"', '\\"')
    print("title:", await ev(f"""(function(){{
      var ta = document.querySelector('textarea[placeholder*="标题"]');
      if (!ta) return 'no-title';
      var setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
      setter.call(ta, "{esc_t}");
      ta.dispatchEvent(new Event('input', {{bubbles: true}}));
      return 'ok:' + ta.value.length;
    }})()"""))
    await asyncio.sleep(1)

    # 2) 正文:focus 真编辑器(x=233,y=278 那个 Draft div)→点击聚焦→CDP insertText
    await send("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": 500, "y": 330})
    await send("Input.dispatchMouseEvent", {"type": "mousePressed", "x": 500, "y": 330, "button": "left", "clickCount": 1})
    await send("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": 500, "y": 330, "button": "left", "clickCount": 1})
    await asyncio.sleep(1)
    # 清旧(全选删)再插
    await send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "a", "code": "KeyA", "windowsVirtualKeyCode": 65, "modifiers": 2})
    await send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "a", "code": "KeyA", "windowsVirtualKeyCode": 65, "modifiers": 2})
    await send("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
    await send("Input.dispatchKeyEvent", {"type": "keyUp", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
    await asyncio.sleep(0.5)
    await send("Input.insertText", {"text": body})
    await asyncio.sleep(3)
    # 3) 验证:Draft 状态真容(innerText of editor)
    print("verify:", await ev("""(function(){
      var e = document.querySelector('.public-DraftEditor-content, [contenteditable=true]');
      var t = (e && e.innerText || '').replace(/\\s+/g, ' ');
      return JSON.stringify({len: t.length, head: t.slice(0, 60), tail: t.slice(-40)});
    })()"""))
    await ws.close()

asyncio.run(main())
