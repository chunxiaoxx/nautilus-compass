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
    Discord 脚本靠「外部先 nav」绕开;这里内置重连。
    bringToFront 必带:Ctrl+V 的粘贴默认动作要求页面为前台激活 tab
    (insertText 无此要求——标题能填而正文粘贴全灭的根因)。"""
    await cdp.send("Page.navigate", {"url": url})
    await cdp.close()
    await asyncio.sleep(wait)
    await cdp.connect()
    try:
        await cdp.send("Page.bringToFront")
    except RuntimeError:
        pass


async def insert_text(cdp, text):
    return await cdp.send("Input.insertText", {"text": text})


def set_cf_html(fragment):
    """写 Windows 剪贴板 CF_HTML 格式(ctypes;64 位句柄必须显式 c_void_p,
    默认 c_int 截断=野指针)。知乎行内格式三条通道实测定案:
    synthetic ClipboardEvent / execCommand insertHTML / 真剪贴板+Ctrl+V,
    知乎 paste 管线一律剥行内(strong/a),块级(h3/li)保留;裸 URL 文字保留。"""
    import ctypes
    import ctypes.wintypes as w
    head = ("<html><body>\r\n<!--StartFragment-->",
            "<!--EndFragment-->\r\n</body></html>")
    tmpl = ("Version:0.9\r\nStartHTML:{}\r\nEndHTML:{}\r\n"
            "StartFragment:{}\r\nEndFragment:{}\r\n")
    prefix_len = len(tmpl.format(*(["0" * 10] * 4)).encode())
    start_frag = prefix_len + len(head[0].encode())
    end_frag = start_frag + len(fragment.encode())
    end_html = prefix_len + len((head[0] + fragment + head[1]).encode())
    src = tmpl.format(f"{prefix_len:010d}", f"{end_html:010d}",
                      f"{start_frag:010d}", f"{end_frag:010d}")
    src += head[0] + fragment + head[1]
    data = src.encode("utf-8")
    k32, u32 = ctypes.windll.kernel32, ctypes.windll.user32
    k32.GlobalAlloc.restype = ctypes.c_void_p
    k32.GlobalAlloc.argtypes = [w.UINT, ctypes.c_size_t]
    k32.GlobalLock.restype = ctypes.c_void_p
    k32.GlobalLock.argtypes = [ctypes.c_void_p]
    k32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    u32.SetClipboardData.argtypes = [w.UINT, ctypes.c_void_p]
    cf = u32.RegisterClipboardFormatW("HTML Format")
    h = k32.GlobalAlloc(0x0002, len(data) + 1)  # GMEM_MOVEABLE
    p = k32.GlobalLock(h)
    ctypes.memmove(p, data, len(data))
    ctypes.memset(p + len(data), 0, 1)
    k32.GlobalUnlock(h)
    if not u32.OpenClipboard(0):
        raise RuntimeError("OpenClipboard failed")
    try:
        u32.EmptyClipboard()
        if not u32.SetClipboardData(cf, h):
            k32.GlobalFree(h)
            raise RuntimeError("SetClipboardData failed")
    finally:
        u32.CloseClipboard()
    return len(data)


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
        # 知乎 ProseMirror schema 认 strong 不认 b(实弹探针:b=0)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
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


# ---------- 知乎行内格式施加(Draft.js 三步流,2026-09-26 实验定谳) ----------
# Draft.js 不同步 JS 设置的 DOM 选区;唯一有效序列 =
# CDP 点击首字定位光标 → Shift+ArrowRight 键盘扩选(带首字校正)→
# 粗体=真鼠标点工具栏「加粗」(click() 跳过 mousedown 无效;Ctrl+B 被禁);
# 链接=CDP Ctrl+K 弹窗(文本预填选区文字,地址框 insertText URL 后点确认)。

async def _sel_text(cdp, target, from_idx):
    """键盘流选中编辑器中的 target 文字。返回 (ok, end_idx)。
    from_idx = 编辑器全文坐标下界(单调推进):粗体子串会在前文重复出现
    (如裸「11/18」的前文命中点在「首考 11/18」「v1 首考 11/18」内部),
    不带下界会选中已加粗的前文 occurrence → 工具栏点击= Toggle OFF。"""
    pos = await _ev(cdp,
        '(function(minOff){var e=document.querySelector("[contenteditable=true]");'
        'if(!e)return "null";var w=document.createTreeWalker('
        'e,NodeFilter.SHOW_TEXT);var n,off=0;while(n=w.nextNode()){'
        'var t=n.textContent;'
        'var i=t.indexOf(' + json.dumps(target) + ',Math.max(0,minOff-off));'
        'if(i>=0&&off+i>=minOff){var r=document.createRange();r.setStart(n,i);'
        'r.setEnd(n,i+1);(n.parentElement||e).scrollIntoView('
        '{block:"center"});var b=r.getBoundingClientRect();'
        'var pe=n.parentElement;'
        'return JSON.stringify({x:b.x+1,y:b.y+b.height/2,g:off+i,'
        'ab:pe&&pe.closest("span[style*=bold],strong,b")?1:0,'
        'al:pe&&pe.closest("a")?1:0})}'
        'off+=t.length}return "null"})(' + str(from_idx) + ')')
    if not isinstance(pos, str) or not pos.startswith("{"):
        return False, from_idx, 0, 0
    p = json.loads(pos)
    end_idx = p["g"] + len(target)
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": p["x"], "y": p["y"],
        "button": "left", "clickCount": 1})
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": p["x"], "y": p["y"],
        "button": "left", "clickCount": 1})
    await asyncio.sleep(0.7)
    for _ in range(len(target)):
        for t in ("keyDown", "keyUp"):
            await cdp.send("Input.dispatchKeyEvent", {
                "type": t, "key": "ArrowRight", "code": "ArrowRight",
                "windowsVirtualKeyCode": 39, "modifiers": 8})
        await asyncio.sleep(0.03)
    await asyncio.sleep(0.4)
    sel = await _ev(cdp, 'window.getSelection().toString()')
    if sel and sel[0] != target[0]:  # 光标落在首字后 → 选区右移一格
        for t in ("keyDown", "keyUp"):
            await cdp.send("Input.dispatchKeyEvent", {
                "type": t, "key": "ArrowRight", "code": "ArrowRight",
                "windowsVirtualKeyCode": 39, "modifiers": 8})
            await cdp.send("Input.dispatchKeyEvent", {
                "type": t, "key": "ArrowLeft", "code": "ArrowLeft",
                "windowsVirtualKeyCode": 37, "modifiers": 8})
        await asyncio.sleep(0.3)
        sel = await _ev(cdp, 'window.getSelection().toString()')
    ok = sel == target
    # 失败也推进 end_idx:该 target 真位置已确知,防后续级联错位
    return ok, end_idx, p.get("ab", 0), p.get("al", 0)


async def _click_toolbar(cdp, label):
    rect = await _ev(cdp,
        '(function(){var bs=Array.from(document.querySelectorAll('
        '"button,[role=button]")).filter(function(b){return '
        'new RegExp(' + json.dumps(label) + ').test(b.title+" "+'
        '(b.getAttribute("aria-label")||""))});if(!bs.length)return "null";'
        'var r=bs[0].getBoundingClientRect();return JSON.stringify('
        '{x:r.x+r.width/2,y:r.y+r.height/2})})()')
    if not isinstance(rect, str) or not rect.startswith("{"):
        return False
    d = json.loads(rect)
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mousePressed", "x": d["x"], "y": d["y"],
        "button": "left", "clickCount": 1})
    await cdp.send("Input.dispatchMouseEvent", {
        "type": "mouseReleased", "x": d["x"], "y": d["y"],
        "button": "left", "clickCount": 1})
    await asyncio.sleep(0.8)
    return True


async def _apply_bold(cdp):
    return await _click_toolbar(cdp, "加粗")


async def _apply_link(cdp, url):
    for t in ("keyDown", "keyUp"):
        await cdp.send("Input.dispatchKeyEvent", {
            "type": t, "key": "k", "code": "KeyK",
            "windowsVirtualKeyCode": 75, "modifiers": 2})
    await asyncio.sleep(1.2)
    await _ev(cdp,
        '(function(){var i=Array.from(document.querySelectorAll("input"))'
        '.filter(function(x){return x.offsetParent!==null&&'
        '/地址/.test(x.placeholder||"")})[0];if(!i)return "no-input";'
        'i.focus();i.select();return 1})()')
    await cdp.send("Input.insertText", {"text": url})
    await asyncio.sleep(0.5)
    r = await _ev(cdp,
        '(function(){var bs=Array.from(document.querySelectorAll("button"))'
        '.filter(function(b){return b.offsetParent!==null&&'
        '/^(确认|插入链接)$/.test(b.textContent.trim())});'
        'if(!bs.length)return "no-btn";bs[0].click();return "ok"})()')
    await asyncio.sleep(1.2)
    return r == "ok"


def parse_inline_spans(body_md):
    """[(pos, kind, text, url)] 按出现位置排序。粗体来自 **…**,
    链接来自裸 URL(中文稿形态:文字=URL)。"""
    spans = []
    for m in re.finditer(r"\*\*(.+?)\*\*", body_md):
        spans.append((m.start(), "bold", m.group(1), None))
    for m in re.finditer(r"https?://[^\s)】》\]]+", body_md):
        spans.append((m.start(), "link", m.group(0), m.group(0)))
    spans.sort()
    return spans


async def apply_inline_styles(cdp, body_md):
    spans = parse_inline_spans(body_md)
    print(f"inline spans: {len(spans)} "
          f"(bold={sum(1 for s in spans if s[1] == 'bold')}, "
          f"link={sum(1 for s in spans if s[1] == 'link')})")
    ok_n = 0
    from_idx = 0
    for _, kind, text, url in spans:
        ok, from_idx, ab, al = await _sel_text(cdp, text, from_idx)
        if not ok:
            print(f"  [skip] select failed: {kind} {text[:30]}")
            continue
        # 粘贴已保真(strong→styled span)的不重复点——工具栏加粗是 toggle,
        # 点了反而取消;链接同理
        if kind == "bold" and ab:
            print(f"  [keep] already bold: {text[:40]}")
            ok_n += 1
            continue
        if kind == "link" and al:
            print(f"  [keep] already link: {text[:40]}")
            ok_n += 1
            continue
        r = (await _apply_bold(cdp)) if kind == "bold" \
            else (await _apply_link(cdp, url))
        print(f"  [{'ok' if r else 'FAIL'}] {kind}: {text[:40]}")
        ok_n += 1 if r else 0
    return ok_n, len(spans)


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
    body_md = re.sub(r"^#\s+.+\n?", "", md, count=1).strip()
    # 剥头部备稿注记(H1 后紧跟的连续引用块——内部元数据,勿入正文;
    # 9/27 发布事故复盘:四修重构时此逻辑被覆盖,内部注记原样上墙)
    body_md = re.sub(r"\A(?:>[^\n]*\n)+", "", body_md).strip()
    body = md_to_html(body_md)

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
    # 清空正文(重跑防叠加):全选+删除
    await _ev(cdp,
        '(function(){var e=document.querySelector("[contenteditable=true]");'
        'if(!e)return "no-editor";e.focus();return 1})()')
    await asyncio.sleep(0.3)
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "a", "code": "KeyA",
        "windowsVirtualKeyCode": 65, "modifiers": 2})
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": "a", "code": "KeyA",
        "windowsVirtualKeyCode": 65, "modifiers": 2})
    await asyncio.sleep(0.3)
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyDown", "key": "Backspace", "code": "Backspace",
        "windowsVirtualKeyCode": 8})
    await cdp.send("Input.dispatchKeyEvent", {
        "type": "keyUp", "key": "Backspace", "code": "Backspace",
        "windowsVirtualKeyCode": 8})
    await asyncio.sleep(1)

    # 正文:真剪贴板 CF_HTML + CDP Ctrl+V(实测三通道中最稳:块级结构保真)。
    # nav 后 Draft.js 挂载有延迟,首个 Ctrl+V 可能被丢 → 重试循环。
    # 判据门槛=纯文本期望长度(不是 HTML 字节数——旧版拿 6129 字节当尺子,
    # 2386 字永远不达标→重复粘贴正文翻倍);重试前必须清空防叠加。
    expect = len(re.sub(r"<[^>]+>", "", body))
    n = set_cf_html(body)
    print("cf_html bytes:", n, "| expect text len:", expect)
    got = 0
    for attempt in range(3):
        if got:  # 重试前清空(防双份正文)
            await _ev(cdp,
                '(function(){var e=document.querySelector('
                '"[contenteditable=true]");if(e){e.focus();return 1}})()')
            await asyncio.sleep(0.3)
            for t in ("keyDown", "keyUp"):
                await cdp.send("Input.dispatchKeyEvent", {
                    "type": t, "key": "a", "code": "KeyA",
                    "windowsVirtualKeyCode": 65, "modifiers": 2})
            await asyncio.sleep(0.3)
            for t in ("keyDown", "keyUp"):
                await cdp.send("Input.dispatchKeyEvent", {
                    "type": t, "key": "Backspace", "code": "Backspace",
                    "windowsVirtualKeyCode": 8})
            await asyncio.sleep(1)
        fr = await _ev(cdp,
            '(function(){var e=document.querySelector('
            '"[contenteditable=true]");if(!e)return "no-editor";'
            'e.focus();return JSON.stringify({f:document.hasFocus(),'
            'ae:document.activeElement.className.slice(0,40)})})()')
        print(f"focus[{attempt}]:", fr)
        await asyncio.sleep(0.3)
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "keyDown", "key": "v", "code": "KeyV",
            "windowsVirtualKeyCode": 86, "modifiers": 2})
        await cdp.send("Input.dispatchKeyEvent", {
            "type": "keyUp", "key": "v", "code": "KeyV",
            "windowsVirtualKeyCode": 86, "modifiers": 2})
        await asyncio.sleep(2)
        v = await _ev(cdp,
            '(document.querySelector("[contenteditable=true]")||'
            '{textContent:""}).textContent.length')
        got = v if isinstance(v, int) else 0
        print(f"paste attempt {attempt}: len={got}")
        if got >= expect * 0.8:
            break
        await asyncio.sleep(2)
    # 行内格式施加(Draft.js 三步流)
    ok_n, total = await apply_inline_styles(cdp, body_md)
    probe = await _ev(cdp,
        'JSON.stringify({len:(document.querySelector("[contenteditable=true]")||'
        '{textContent:"?"}).textContent.length,'
        'h3:(document.querySelector("[contenteditable=true]")||'
        '{querySelectorAll:function(){return[]}}).querySelectorAll("h3").length,'
        'bold:(document.querySelector("[contenteditable=true]")||'
        '{querySelectorAll:function(){return[]}})'
        '.querySelectorAll("span[style*=bold]").length,'
        'a:(document.querySelector("[contenteditable=true]")||'
        '{querySelectorAll:function(){return[]}}).querySelectorAll("a").length,'
        'url:(document.querySelector("[contenteditable=true]")||'
        '{textContent:""}).textContent.includes("github.com"),'
        'title:(document.querySelector("textarea")||{value:"?"}).value.slice(0,60)})')
    print("after-fill:", probe, f"| inline applied {ok_n}/{total}")
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
