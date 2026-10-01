# -*- coding: utf-8 -*-
"""Reddit Script App 创建(9226 CDP,用户已登录)——create app 表单→提交→读 client_id/secret。"""
import asyncio
import json
import urllib.request
import websockets

APP_NAME = "assay-publisher"


async def get_ws(substr="reddit"):
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9226/json"))
    page = [t for t in tabs if t["type"] == "page" and substr in t.get("url", "")]
    if not page:
        raise SystemExit(f"no {substr} tab")
    return websockets.connect(page[0]["webSocketDebuggerUrl"], max_size=30 * 1024 * 1024,
                              ping_interval=20)


async def main():
    # 1) 导航到 apps 页
    async with await get_ws() as ws:
        mid = 0

        async def send(method, params, timeout=20):
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

        await send("Page.navigate", {"url": "https://www.reddit.com/prefs/apps"})
        await asyncio.sleep(10)
        print("url:", await ev("location.href.slice(0,60)"))

    # navigate 后重连
    await asyncio.sleep(3)
    async with await get_ws() as ws:
        mid = 0

        async def send(method, params, timeout=20):
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

        # 2) 看页面结构:是否已有 app 或 create 表单
        state = await ev("""(function(){
          var form = document.querySelector('form');
          var nameInput = document.querySelector('input[name=name], #name');
          var appList = document.body.innerText.includes('developed applications') ||
                        document.body.innerText.includes('create another');
          return JSON.stringify({hasForm: !!form, hasName: !!nameInput,
                                 body_head: document.body.innerText.slice(0,200)});
        })()""")
        print("state:", state)

        # 3) 填表(老版 Reddit prefs 是普通 HTML form)
        res = await ev(f"""(function(){{
          var name = document.querySelector('input[name=name], #name');
          if(!name) return 'no-name-field';
          name.focus();
          name.value = '';
          document.execCommand('selectAll', false, null);
          document.execCommand('insertText', false, "{APP_NAME}");
          // 选 script 类型
          var scriptRadio = document.querySelector('input[type=radio][value=script]');
          if(scriptRadio) scriptRadio.click();
          // redirect uri
          var reds = Array.from(document.querySelectorAll('input'));
          var red = reds.find(function(i){{ return /redirect|uri/i.test(i.name||'') || /redirect/i.test(i.placeholder||''); }});
          if(red){{ red.focus(); document.execCommand('selectAll', false, null);
                   document.execCommand('insertText', false, 'http://localhost'); }}
          return 'filled name=' + !!name + ' script=' + !!scriptRadio + ' redir=' + !!red;
        }})()""")
        print("fill:", res)
        await asyncio.sleep(2)

        # 4) 提交
        sub = await ev("""(function(){
          var btn = document.querySelector('button[type=submit], input[type=submit]');
          if(!btn) return 'no-submit';
          btn.click(); return 'submitted:' + (btn.value||btn.textContent||'').slice(0,20);
        })()""")
        print("submit:", sub)
        await asyncio.sleep(10)
        print("after:", await ev("location.href.slice(0,70)"))
        # 5) 读凭证
        cred = await ev("""(function(){
          var t = document.body.innerText;
          // client id:app 名下方的一串;secret:点 show 前不可见——抓页面上的 id 形态
          var m = t.match(/[a-zA-Z0-9_-]{20,25}\\n/);
          var secBtn = Array.from(document.querySelectorAll('a, button')).find(function(b){
            return /show|edit/i.test((b.textContent||'') + (b.href||'')); });
          return JSON.stringify({candidate_id: m ? m[0].trim() : null,
                                 has_secret_btn: !!secBtn,
                                 body_snip: t.slice(0, 300)});
        })()""")
        print("cred:", str(cred)[:600])

asyncio.run(main())
