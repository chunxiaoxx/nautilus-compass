# -*- coding: utf-8 -*-
"""中文平台 CDP 发布器 · 知乎/小红书/什么值得买 · 2026-09-26 立。

复用 Discord 配方(post_discord.py Chrome154 实弹 GREEN)泛化:
- 每平台独立 Chrome profile + 独立 CDP 端口(discord 9224 / zhihu 9225 /
  xhs 9226 / smzdm 9227),登录态持久化,一次扫码长期有效
- Chrome154 配方:Input.insertText 插文 / CDP Enter text="\\r" 提交 /
  普通字符串拼 JS(f-string 大括号转义是坑)/ nav 后必须重连 ws(context 会废)
- 粘贴富文本走 ClipboardEvent+DataTransfer(Discord 实测通道 C 有效)

用法:
  python cn_publisher.py zhihu <md_file> [--publish]   # 默认 dry-run
  python cn_publisher.py zhihu login-check              # 登录态判据
  python cn_publisher.py xhs|smzdm login-check          # 骨架已留

风控纪律:发布间隔人速;失败即停不重试轰炸;首帖用户在场。
"""
import argparse
import asyncio
import json
import re
import subprocess
import sys
import urllib.request

import websockets

PROFILES = {
    "zhihu": {"port": 9225, "name": "知乎",
              "profile": r"C:\Users\chunx\AppData\Local\Temp\zhihu-chrome-profile",
              "check_url": "https://www.zhihu.com/creator",
              "signin_marker": "/signin"},
    "xhs": {"port": 9226, "name": "小红书",
            "profile": r"C:\Users\chunx\AppData\Local\Temp\xhs-chrome-profile",
            "check_url": "https://creator.xiaohongshu.com",
            "signin_marker": "login"},
    "smzdm": {"port": 9227, "name": "什么值得买",
              "profile": r"C:\Users\chunx\AppData\Local\Temp\smzdm-chrome-profile",
              "check_url": "https://post.smzdm.com",
              "signin_marker": "login"},
}
CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"


def launch(platform):
    p = PROFILES[platform]
    subprocess.Popen([CHROME, f"--remote-debugging-port={p['port']}",
                      f"--user-data-dir={p['profile']}", p["check_url"]])


class Cdp:
    """每平台会话。nav() 内置重连(nav 废旧 context,Chrome154 实测)。"""

    def __init__(self, port):
        self.port = port
        self.ws = None

    def _page_ws(self):
        data = json.load(urllib.request.urlopen(
            f"http://127.0.0.1:{self.port}/json", timeout=5))
        pages = [t for t in data if t["type"] == "page"]
        for t in pages:  # 优先本平台域名页
            dom = self._dom
            if dom and dom in t.get("url", ""):
                return t["webSocketDebuggerUrl"]
        return pages[0]["webSocketDebuggerUrl"] if pages else None

    _dom = None

    async def connect(self):
        ws_url = self._page_ws()
        if not ws_url:
            raise SystemExit("no page target (chrome 没开?)")
        self.ws = await websockets.connect(ws_url, max_size=20 * 1024 * 1024)
        self.mid = 0

    async def close(self):
        if self.ws:
            await self.ws.close()
            self.ws = None

    async def send(self, method, params=None):
        self.mid += 1
        await self.ws.send(json.dumps(
            {"id": self.mid, "method": method, "params": params or {}}))
        while True:
            m = json.loads(await self.ws.recv())
            if m.get("id") == self.mid:
                if "error" in m:
                    raise RuntimeError(m["error"].get("message"))
                return m.get("result", {})


async def _ev(cdp, expr):
    r = await cdp.send("Runtime.evaluate",
                       {"expression": expr, "returnByValue": True})
    if "exceptionDetails" in r:
        return "EXC:" + json.dumps(
            r["exceptionDetails"], ensure_ascii=False)[:200]
    return r.get("result", {}).get("value")


async def nav(cdp, url, wait=6):
    """nav 后重连 ws —— navigate 会废掉旧 execution context(Chrome154 实测)。
    Discord 脚本靠「外部先 nav」绕开;这里内置重连。"""
    await cdp.send("Page.navigate", {"url": url})
    await cdp.close()
    await asyncio.sleep(wait)
    await cdp.connect()


async def insert_text(cdp, text):
    return await cdp.send("Input.insertText", {"text": text})


async def press_enter(cdp):
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "Enter", "code": "Enter",
        "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13,
        "text": "\r"})
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": "Enter", "code": "Enter",
        "windowsVirtualKeyCode": 13})


async def shot(cdp, path):
    res = await cdp.send("Page.captureScreenshot", {"format": "png"})
    with open(path, "wb") as f:
        f.write(__import__("base64").b64decode(res["data"]))
    print("saved", path)


# ---------- markdown → HTML(知乎富文本粘贴用,简易集) ----------

def md_to_html(md):
    """覆盖:一/二/三级标题、粗体、行内代码、链接、无序列表、
    引用、段落、表格(降级文本,知乎编辑器对粘贴表格支持不稳)。
    结构解析在转义前(转义会毁 > 引用标记)。"""
    out, in_list, in_quote = [], False, False

    def inline(s):
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
        return s

    def close_list():
        nonlocal in_list
        if in_list:
            out.append("</ul>")
            in_list = False

    def close_quote():
        nonlocal in_quote
        if in_quote:
            out.append("</blockquote>")
            in_quote = False

    for raw in md.splitlines():
        raw = raw.rstrip()
        m = re.match(r"^(#{1,3})\s+(.*)", raw)
        if m:
            close_list()
            close_quote()
            h = min(len(m.group(1)) + 1, 4)  # h1 留给标题框,h2 起
            out.append(f"<h{h}>{inline(m.group(2))}</h{h}>")
            continue
        if re.match(r"^\s*[-*]\s+", raw):
            close_quote()
            if not in_list:
                out.append("<ul>")
                in_list = True
            item = re.sub(r"^\s*[-*]\s+", "", raw)
            out.append(f"<li>{inline(item)}</li>")
            continue
        close_list()
        if raw.startswith(">"):
            if not in_quote:
                out.append("<blockquote>")
                in_quote = True
            out.append(f"<p>{inline(raw.lstrip('> '))}</p>")
            continue
        close_quote()
        if raw.startswith("|"):
            out.append(f"<p>{inline(raw)}</p>")  # 表格降级文本
            continue
        if raw.strip():
            out.append(f"<p>{inline(raw)}</p>")
    close_list()
    close_quote()
    return "".join(out)


# ---------- 平台适配 ----------

async def zhihu_login_check(cdp):
    await nav(cdp, "https://www.zhihu.com/creator", wait=8)
    v = await _ev(cdp, 'JSON.stringify({url:location.href})')
    d = json.loads(v) if isinstance(v, str) else {}
    ok = "/signin" not in d.get("url", "") and "creator" in d.get("url", "")
    print("zhihu login:", "GREEN" if ok else "RED(未登录,需扫码)", v)
    return ok


async def zhihu_publish(cdp, md, publish):
    title = re.match(r"^#\s+(.+)", md)
    title = title.group(1).strip() if title else md.splitlines()[0][:40]
    body = md_to_html(re.sub(r"^#\s+.+\n?", "", md, count=1))

    await nav(cdp, "https://zhuanlan.zhihu.com/write", wait=8)
    # 标题框(placeholder「请输入标题(2 到 100 个字符)」)
    r = await _ev(cdp,
        'JSON.stringify({t:!!document.querySelector("textarea[placeholder*=标题],textarea"),'
        'e:!!document.querySelector("[contenteditable=true]")})')
    print("editor probe:", r)
    # 标题
    await _ev(cdp,
        '(function(){var t=document.querySelector("textarea[placeholder*=标题],textarea");'
        'if(t){t.focus();return "ok"}})()')
    await insert_text(cdp, title)
    await asyncio.sleep(1)
    # 正文:富文本粘贴(剪贴板事件带 text/html,Discord 通道 C 同款)
    v = await _ev(cdp,
        '(function(){var e=document.querySelector("[contenteditable=true]");'
        'if(!e)return "no-editor";e.focus();'
        'var dt=new DataTransfer();'
        'dt.setData("text/html",' + json.dumps(body) + ');'
        'dt.setData("text/plain",' + json.dumps(re.sub(r"<[^>]+>", "", md)) + ');'
        'e.dispatchEvent(new ClipboardEvent("paste",{clipboardData:dt,'
        'bubbles:true,cancelable:true}));return "pasted"})()')
    print("paste:", v)
    await asyncio.sleep(2)
    probe = await _ev(cdp,
        'JSON.stringify({len:(document.querySelector("[contenteditable=true]")||'
        '{textContent:"?"}).textContent.length,'
        'title:(document.querySelector("textarea")||{value:"?"}).value.slice(0,60)})')
    print("after-fill:", probe)
    await shot(cdp, "runtime/zhihu_dryrun.png")
    if not publish:
        print("DRY-RUN: 已填好未发布(截图 runtime/zhihu_dryrun.png),"
              "人工确认后加 --publish 重跑")
        return
    btn = await _ev(cdp,
        '(function(){var b=Array.from(document.querySelectorAll("button"))'
        '.find(x=>/发布/.test(x.textContent));if(!b)return "no-btn";'
        'b.click();return "clicked"})()')
    print("publish btn:", btn)
    await asyncio.sleep(6)
    v = await _ev(cdp, 'JSON.stringify({url:location.href})')
    print("final:", v)
    await shot(cdp, "runtime/zhihu_published.png")


ADAPTERS = {"zhihu": (zhihu_login_check, zhihu_publish)}


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("platform", choices=list(PROFILES))
    ap.add_argument("arg2", nargs="?", help="md 文件 或 login-check")
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args()
    p = PROFILES[a.platform]
    cdp = Cdp(p["port"])
    cdp._dom = {"zhihu": "zhihu.com", "xhs": "xiaohongshu",
                "smzdm": "smzdm"}[a.platform]
    try:
        await cdp.connect()
    except SystemExit:
        launch(a.platform)
        await asyncio.sleep(10)
        await cdp.connect()
    check, pub = ADAPTERS.get(a.platform, (None, None))
    if a.arg2 == "login-check" or not pub:
        if a.platform == "zhihu":
            ok = await zhihu_login_check(cdp)
            sys.exit(0 if ok else 1)
        print(f"{a.platform}: 骨架已留,适配待续(端口 {p['port']} profile "
              f"{p['profile']})")
        return
    md = open(a.arg2, encoding="utf-8").read()
    if not await zhihu_login_check(cdp):
        sys.exit(1)
    await zhihu_publish(cdp, md, a.publish)


if __name__ == "__main__":
    asyncio.run(main())
