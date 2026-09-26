# -*- coding: utf-8 -*-
"""Discord 发帖(9224 CDP)· 2026-09-27 Chrome154 实证成功配方(v3 回写)。

用法:python post_discord.py <channel_url> <text_file>
前置:tab 已在目标频道(先 python cdp_tool.py nav <url>)——本脚本不再
navigate:nav 会废掉旧 execution context,后续 evaluate 持续 EXC:Uncaught。

9/24 Chrome153 配方(v1)失效根因与修复(全记录见
runtime/assay_bc1_20260927/DISCORD_POST_RECORD.md):
1. placeholder DIV 现也带 slateTextArea 类,v1 选择器抓到 placeholder
   (isContentEditable=false)→ focus 漂移 → Input.insertText 落空;
   且 residue<=25 的 break 把「没插进去」(占位符恰 20 字)误判为已发送。
   → 选择器改 div[role=textbox][class*=slateTextArea],插入后按目标长度验长。
2. JS dispatchEvent Enter 在 154 失效;唯一有效提交通道 =
   CDP Input.dispatchKeyEvent {type:"keyDown", key:"Enter", text:"\\r"} + keyUp。
3. 读回比对须剥 markdown 符号(** 渲染后消失,裸 textContent 必假阴性)。
4. JS 片段一律普通字符串拼接(f-string {{}} 转义连翻车两次)。
"""
import asyncio
import json
import sys
import urllib.request

import websockets

PORT = 9224
SEL = 'div[role=textbox][class*=slateTextArea]'
MD_CHARS = "*#`>"


def page_ws():
    data = json.load(urllib.request.urlopen(
        f"http://127.0.0.1:{PORT}/json", timeout=5))
    for t in data:
        if t["type"] == "page" and "discord" in t.get("url", ""):
            return t["webSocketDebuggerUrl"]
    raise SystemExit("no discord page")


def plain(s):
    return "".join(c for c in s if c not in MD_CHARS)


async def main():
    channel_url, text_file = sys.argv[1], sys.argv[2]
    text = open(text_file, encoding="utf-8").read().strip()
    probe = plain(text)[:40]

    async with websockets.connect(page_ws(), max_size=20 * 1024 * 1024) as ws:
        mid = 0

        async def send(method, params=None):
            nonlocal mid
            mid += 1
            await ws.send(json.dumps({"id": mid, "method": method,
                                      "params": params or {}}))
            while True:
                m = json.loads(await ws.recv())
                if m.get("id") == mid:
                    if "error" in m:
                        raise RuntimeError(m["error"].get("message"))
                    return m.get("result", {})

        async def ev(expr):
            r = await send("Runtime.evaluate",
                           {"expression": expr, "returnByValue": True})
            if "exceptionDetails" in r:
                return "EXC:" + json.dumps(
                    r["exceptionDetails"], ensure_ascii=False)[:300]
            return r.get("result", {}).get("value")

        async def ed():
            v = await ev(
                '(function(){try{var e=document.querySelector("' + SEL + '");'
                'if(!e)return JSON.stringify({"err":"no-editor"});'
                'e.focus();return JSON.stringify({"len":e.textContent.length,'
                '"focus":document.activeElement===e,'
                '"head":e.textContent.slice(0,50),'
                '"tail":e.textContent.slice(-40)})}catch(x)'
                '{return JSON.stringify({"exc":x.message})}})()')
            if not isinstance(v, str):
                return {"err": f"eval-returned:{v!r}"}
            try:
                return json.loads(v)
            except ValueError:
                return {"err": f"non-json:{v[:80]}"}

        cur = await ev('location.pathname')
        if channel_url.rstrip("/").split("/")[-1] not in (cur or ""):
            print(f"RED: wrong channel (at {cur}); cdp_tool.py nav first, abort")
            return

        # 就绪轮询(context/React 稳定)
        ready = False
        for _ in range(8):
            d = await ed()
            if "exc" not in d and "err" not in d:
                ready = True
                break
            await asyncio.sleep(2)
        print("ready:", ready, d)
        if not ready:
            print("RED: page/evaluate not ready, abort")
            return

        # 清残留(草稿持久化;阈值<=2,不放水)
        for i in range(3):
            d = await ed()
            print(f"clear[{i}]:", d)
            if d.get("len", 99) <= 2:
                break
            await send("Input.dispatchKeyEvent", {
                "type": "keyDown", "key": "a", "code": "KeyA",
                "windowsVirtualKeyCode": 65, "modifiers": 2})
            await send("Input.dispatchKeyEvent", {
                "type": "keyUp", "key": "a", "code": "KeyA",
                "windowsVirtualKeyCode": 65, "modifiers": 2})
            await asyncio.sleep(0.3)
            await send("Input.dispatchKeyEvent", {
                "type": "keyDown", "key": "Backspace", "code": "Backspace",
                "windowsVirtualKeyCode": 8})
            await send("Input.dispatchKeyEvent", {
                "type": "keyUp", "key": "Backspace", "code": "Backspace",
                "windowsVirtualKeyCode": 8})
            await asyncio.sleep(0.8)

        # 插文(唯一有效文本通道;focus 已验证)
        await send("Input.insertText", {"text": text})
        await asyncio.sleep(1.5)
        d = await ed()
        print("after-insert:", d)
        if d.get("len", 0) < len(text) * 0.9:
            print("RED: insert incomplete, abort (no Enter)")
            return

        # 提交:CDP Enter 带 text="\r"(Chrome154 唯一有效)
        await send("Input.dispatchKeyEvent", {
            "type": "keyDown", "key": "Enter", "code": "Enter",
            "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13,
            "text": "\r"})
        await send("Input.dispatchKeyEvent", {
            "type": "keyUp", "key": "Enter", "code": "Enter",
            "windowsVirtualKeyCode": 13})

        # 三拍读回(比对剥 markdown)
        posted = None
        for t in (1, 3, 6):
            await asyncio.sleep(t if t == 1 else t - sum(
                x for x in (1, 3) if x < t))
            last = await ev(
                '(function(){var ls=document.querySelectorAll('
                '"li[id^=chat-messages]");var l=ls[ls.length-1];'
                'if(!l)return JSON.stringify({error:"none"});'
                'var p=l.id.split("-");var msgId=p[p.length-1];'
                'return JSON.stringify({msgId:msgId,'
                'link:location.origin+location.pathname+"/"+msgId,'
                'head:l.textContent.slice(0,100)})})()')
            print(f"read[{t}s]:", last)
            try:
                j = json.loads(last)
                if probe in plain(j.get("head", "")):
                    posted = j
                    break
            except (ValueError, AttributeError):
                pass
        d = await ed()
        print("final editor:", d)
        print("VERDICT:", "GREEN " + json.dumps(posted) if posted
              else "RED (not on wall)")


asyncio.run(main())
