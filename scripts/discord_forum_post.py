# -*- coding: utf-8 -*-
"""Discord 论坛频道发帖(9224 CDP)· 2026-09-28 实战配方固化。

用法:python discord_forum_post.py <forum_channel_url> <title> <text_file>
普通文本频道请用 post_discord.py;本脚本专攻论坛频道(forum channel)。

## 今晚实战踩坑全录(背书信上墙之战,10+ 轮换来的,勿删):

1. **论坛频道没有底部输入框**——消息插进"给 #xx 发消息"框是无效的
   (role=textbox 且 aria-label 以"给#"开头=频道框,非发帖框)。
2. **开帖唯一稳定通道 = Shift+N**(CDP keyDown n+modifiers:1)。
   "+New Post" 按钮在新 UI 中不存在(DOM 搜不到)。
3. **弹窗会被 Discord 异步重渲染关闭**(随机,约 30% 概率)——每次
   DOM 查询后要重验弹窗在不在,不在就 Shift+N 重开;草稿会保留。
4. **clickTrapContainer trapClicks 遮罩**会盖住输入区吃掉点击——
   发帖前先 display:none 掉全部 [class*=clickTrapContainer]。
5. **标题框不是 <input> 是 role=textbox**(DOM 里 input 查询拿不到);
   定位法=按 y 排序取第一个可见 role=textbox,或坐标直击
   (视口 1037x739 下标题框中心约 (517,117),正文区在其下)。
6. **发布按钮**坐标直击 (965,660);文案"发布/Post" 的 button 查询
   可能拿错(bs[bs.length-1] 不可靠),坐标法稳。
7. **读回验证**:发布后 URL 应变 /channels/<guild>/<thread_id>;
   页面文本含帖子标题=上墙。直链是 JS 路由,卡片无 a 标签,
   定位=列表顶卡/按标题搜索。

前置:Chrome 9224 已开(拉起配方=chrome --remote-debugging-port=9224
--user-data-dir=%LOCALAPPDATA%/Temp/discord-chrome-profile
--proxy-server=socks5://127.0.0.1:10808 <url>;登录态随 profile 持久)。
"""
import asyncio
import json
import subprocess
import sys
import urllib.request

import websockets

PORT = 9224
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"
PROFILE = r"C:/Users/chunx/AppData/Local/Temp/discord-chrome-profile"


def page_ws():
    data = json.load(urllib.request.urlopen(
        f"http://127.0.0.1:{PORT}/json", timeout=5))
    for t in data:
        if t["type"] == "page" and "discord" in t.get("url", ""):
            return t["webSocketDebuggerUrl"]
    raise SystemExit("no discord page (chrome 没开?)")


async def ensure_chrome(url):
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/version", timeout=3)
        return
    except Exception:
        subprocess.Popen([CHROME, f"--remote-debugging-port={PORT}",
                          f"--user-data-dir={PROFILE}",
                          "--proxy-server=socks5://127.0.0.1:10808", url])
        await asyncio.sleep(14)


class C:
    def __init__(self):
        self.ws = None
        self.mid = 0

    async def conn(self):
        self.ws = await websockets.connect(page_ws(), max_size=20 * 1024 * 1024)

    async def ev(self, js):
        self.mid += 1
        await self.ws.send(json.dumps({"id": self.mid, "method": "Runtime.evaluate",
                                       "params": {"expression": js, "returnByValue": True}}))
        while True:
            m = json.loads(await self.ws.recv())
            if m.get("id") == self.mid:
                return m.get("result", {}).get("result", {}).get("value")

    async def click(self, x, y):
        for t in ("mousePressed", "mouseReleased"):
            await self.ws.send(json.dumps({"id": 0, "method": "Input.dispatchMouseEvent",
                                           "params": {"type": t, "x": x, "y": y,
                                                      "button": "left", "clickCount": 1}}))
            await asyncio.sleep(0.1)

    async def key(self, k, code, vk, mods=0):
        for t in ("keyDown", "keyUp"):
            await self.ws.send(json.dumps({"id": 0, "method": "Input.dispatchKeyEvent",
                                           "params": {"type": t, "key": k, "code": code,
                                                      "windowsVirtualKeyCode": vk,
                                                      "modifiers": mods}}))

    async def ins(self, text):
        await self.ws.send(json.dumps({"id": 0, "method": "Input.insertText",
                                       "params": {"text": text}}))


async def modal_alive(c):
    """弹窗在=存在两个可见 role=textbox(标题+正文)且正文框有内容或高度>100。"""
    r = await c.ev('''(function(){var es=Array.from(document.querySelectorAll(
        "div[role=textbox]")).filter(function(x){return x.getBoundingClientRect().width>0});
        return JSON.stringify(es.length)})()''')
    try:
        return int(json.loads(r)) >= 2
    except Exception:
        return False


async def main():
    channel_url, title, text_file = sys.argv[1], sys.argv[2], sys.argv[3]
    body = open(text_file, encoding="utf-8").read()
    await ensure_chrome(channel_url)
    c = C()
    await c.conn()
    # 等频道渲染
    await asyncio.sleep(6)

    for attempt in range(3):  # 弹窗重开循环(坑 3)
        # 清遮罩(坑 4)
        await c.ev('(function(){var n=0;document.querySelectorAll("[class*=clickTrapContainer],[class*=trapClicks]").forEach(function(e){e.style.display="none";n++});return n})()')
        # 开帖(坑 2)
        await c.key("n", "KeyN", 78, mods=1)
        await asyncio.sleep(3)
        if not await modal_alive(c):
            print(f"attempt {attempt}: modal not open, retrying")
            continue
        # 正文(大框,按 y 排序第二个)
        r = await c.ev('''(function(){var es=Array.from(document.querySelectorAll(
            "div[role=textbox]")).filter(function(x){return x.getBoundingClientRect().width>0});
            es.sort(function(a,b){return a.getBoundingClientRect().y-b.getBoundingClientRect().y});
            if(es.length<2)return "no";var b=es[1].getBoundingClientRect();
            return JSON.stringify({x:Math.round(b.x+10),y:Math.round(b.y+20)})})()''')
        if not (isinstance(r, str) and r.startswith("{")):
            continue
        p = json.loads(r)
        await c.click(p["x"], p["y"])
        await asyncio.sleep(0.6)
        await c.ins(body)
        await asyncio.sleep(1)
        # 标题(第一个,坐标直击坑 5)
        await c.click(517, 117)
        await asyncio.sleep(0.6)
        await c.ins(title)
        await asyncio.sleep(1)
        # 验证标题进框
        v = await c.ev('''(function(){var es=Array.from(document.querySelectorAll(
            "div[role=textbox]")).filter(function(x){return x.getBoundingClientRect().width>0});
            es.sort(function(a,b){return a.getBoundingClientRect().y-b.getBoundingClientRect().y});
            return JSON.stringify({t:es[0]?es[0].textContent.slice(0,40):"",bl:es[1]?es[1].textContent.length:0})})()''')
        ok = False
        try:
            d = json.loads(v)
            ok = title[:30] in d.get("t", "") and d.get("bl", 0) >= len(body) * 0.8
        except Exception:
            pass
        if not ok:
            print(f"attempt {attempt}: fill verify fail {v}, retrying")
            continue
        # 发布(坑 6)
        await c.click(965, 660)
        await asyncio.sleep(7)
        url = await c.ev("location.href")
        posted = await c.ev(
            '(document.body.innerText.indexOf(' + json.dumps(title[:40]) + ')>=0)')
        print("url:", url, "| posted:", posted)
        if posted:
            print("VERDICT: GREEN (on wall)")
            return
        print("VERDICT: RED")
        return
    print("VERDICT: RED (modal never stable)")


if __name__ == "__main__":
    asyncio.run(main())
