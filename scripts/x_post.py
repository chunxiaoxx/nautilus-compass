# -*- coding: utf-8 -*-
"""X.com 发帖(9226 CDP)· 2026-09-30 execCommand 配方实证成功。

用法:python x_post.py <text_file>
前置:x.com 已登录(tab 在 Chrome 9226 中)

## 核心发现(2026-09-30 实战定案):
X.com 的 compose box 是 Draft.js 编辑器:
- CDP Input.insertText → 文字丢失(React state 不更新)
- document.execCommand("insertText") → **唯一有效**(经浏览器编辑管线,Draft.js 拦截)
- 编辑器选择器: [data-testid="tweetTextarea_0"]
- Post 按钮: [data-testid="tweetButtonInline"](compose/post 页;9/30 晚实证 tweetButton 不存在,
  inline 才是发帖钮;发后跳 graduated-access 过渡页属正常,验证走 profile 首条)

## 发帖流程:
1. Page.navigate → x.com/compose/post
2. 等 8s(页面加载)
3. JS: 找编辑器 → focus → 全选清空 → execCommand("insertText", false, text)
4. 验证 textContent.length > 10
5. JS: 找 [data-testid="tweetButton"] → .click()
"""
import asyncio, json, sys, urllib.request
import websockets

PORT = 9226

async def main():
    text = open(sys.argv[1], encoding="utf-8").read().strip()
    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json"))
    x_tab = [t for t in tabs if t["type"] == "page" and "x.com" in t.get("url", "")][0]
    ws = await websockets.connect(x_tab["webSocketDebuggerUrl"], max_size=20*1024*1024)
    mid = 0
    
    async def send(method, params):
        nonlocal mid
        mid += 1
        await ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            m = json.loads(await ws.recv())
            if m.get("id") == mid:
                return m
    
    async def ev(js):
        r = await send("Runtime.evaluate", {"expression": js, "returnByValue": True})
        return r.get("result", {}).get("result", {}).get("value")
    
    await send("Page.navigate", {"url": "https://x.com/compose/post"})
    await asyncio.sleep(8)
    
    result = await ev('''(function(){
        var el = document.querySelector('[data-testid="tweetTextarea_0"]');
        if (!el) return "no-editor";
        el.focus();
        var sel = window.getSelection();
        var range = document.createRange();
        range.selectNodeContents(el);
        sel.removeAllRanges();
        sel.addRange(range);
        document.execCommand("insertText", false, ''' + json.dumps(text) + ''');
        return JSON.stringify({len: el.textContent.length, head: el.textContent.slice(0,50)});
    })()''')
    
    d = json.loads(result) if isinstance(result, str) and result.startswith("{") else {}
    if d.get("len", 0) > 10:
        post_result = await ev('''(function(){
            var btn = document.querySelector('[data-testid="tweetButtonInline"]') || document.querySelector('[data-testid="tweetButton"]');
            if (!btn) return "no-btn";
            btn.click();
            return "posted";
        })()''')
        print(f"POSTED: {post_result} | content: {d['head']}...")
    else:
        print(f"FAILED: text not in editor ({result})")
    
    await ws.close()

if __name__ == "__main__":
    asyncio.run(main())
