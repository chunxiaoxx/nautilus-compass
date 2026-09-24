# -*- coding: utf-8 -*-
"""Discord 发帖(9224 CDP)· 2026-09-24 实证成功配方(Chrome153)。

用法:python post_discord.py <channel_url> <text_file>

配方(按效排序,实测于 discord-chrome-profile / Chrome 153.0.8010.53):
1. 插文 = CDP Input.insertText({text}) —— 唯一有效的文本通道
   (execCommand insertText 被 Slate 拦;dispatchKeyEvent 字符事件不落地)
2. 提交 = JS 层 dispatchEvent KeyboardEvent("keydown",{key:Enter,keyCode:13,
   bubbles:true}) —— Slate/React 不查 isTrusted,实测发送成功
   (CDP Input.dispatchKeyEvent Enter 无效!mouseWheel 也无效;
   OS 层 SendKeys 因 Windows 前台锁进不去)
3. 发后验证 = 残留长度 + lastid 读回消息头
"""
import asyncio
import json
import sys
import urllib.request

import websockets

PORT = 9224


def page_ws():
    data = json.load(urllib.request.urlopen(
        f"http://127.0.0.1:{PORT}/json", timeout=5))
    for t in data:
        if t["type"] == "page" and "discord" in t.get("url", ""):
            return t["webSocketDebuggerUrl"]
    raise SystemExit("no discord page")


async def main():
    channel_url, text_file = sys.argv[1], sys.argv[2]
    text = open(text_file, encoding="utf-8").read().strip()

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
            return r.get("result", {}).get("value")

        await send("Page.navigate", {"url": channel_url})
        await asyncio.sleep(5)

        focused = await ev(
            '(function(){var e=document.querySelector("[class*=slateTextArea]");'
            'if(!e)return "no-editor";e.focus();return "focused"})()')
        print("focus:", focused)

        # 插文:CDP 原生 Input.insertText(execCommand 被 Slate 拦,实测无效)
        await send("Input.insertText", {"text": text})
        await asyncio.sleep(1.0)
        residue = await ev(
            '(document.querySelector("[class*=slateTextArea]")||{textContent:"?"})'
            '.textContent.length')
        print("inserted(Input.insertText) | editor len:", residue)

        # 提交 = JS 层 dispatchEvent(成功配方,见文件头)
        for attempt in range(3):
            await ev(
                '(function(){var e=document.querySelector("[class*=slateTextArea]");'
                'if(!e)return "no-editor";e.focus();'
                'e.dispatchEvent(new KeyboardEvent("keydown",{key:"Enter",'
                'code:"Enter",keyCode:13,which:13,bubbles:true,'
                'cancelable:true}));return "sent"})()')
            await asyncio.sleep(2.5)
            residue = await ev(
                '(document.querySelector("[class*=slateTextArea]")||'
                '{textContent:"?"}).textContent.length')
            print(f"attempt {attempt}: residue len = {residue}")
            if not residue or residue <= 25:  # 占位符≈20,发送后残长很小
                break

        # 读回最新消息确认
        last = await ev(
            '(function(){var ls=document.querySelectorAll("li[id^=chat-messages]");'
            'var l=ls[ls.length-1];if(!l)return JSON.stringify({error:"none"});'
            'var p=l.id.split("-");var msgId=p[p.length-1];'
            'return JSON.stringify({msgId:msgId,'
            'link:location.origin+location.pathname+"/"+msgId,'
            'head:l.textContent.slice(0,120)})})()')
        print("last:", last)


asyncio.run(main())
