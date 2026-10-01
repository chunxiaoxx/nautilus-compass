# -*- coding: utf-8 -*-
"""Reddit apps 页(tab D8499E4D992E):填 create app 表单+提交+读凭证。"""
import asyncio
import json
import urllib.request
import websockets

APP_NAME = "assay-publisher"


async def main():
    tabs = json.load(urllib.request.urlopen("http://127.0.0.1:9226/json"))
    tab = [t for t in tabs if "prefs/apps" in t.get("url", "")][0]
    ws = await websockets.connect(tab["webSocketDebuggerUrl"], max_size=30 * 1024 * 1024,
                                  ping_interval=15)
    mid = 0

    async def ev(js, timeout=15):
        nonlocal mid; mid += 1
        import time; t0 = time.time()
        await ws.send(json.dumps({"id": mid, "method": "Runtime.evaluate",
                                  "params": {"expression": js, "returnByValue": True}}))
        while time.time() - t0 < timeout:
            m = json.loads(await asyncio.wait_for(ws.recv(), timeout=timeout))
            if m.get("id") == mid:
                return m.get("result", {}).get("result", {}).get("value")
        return "TIMEOUT"

    print("fill:", await ev(f"""(function(){{
      var name = document.querySelector('input[name=name], #name');
      if(!name) return 'no-name';
      name.focus(); name.select();
      document.execCommand('insertText', false, '{APP_NAME}');
      var scriptRadio = document.querySelector('input[type=radio][value=script]');
      if(!scriptRadio) return 'no-script-radio';
      scriptRadio.click();
      var inputs = Array.from(document.querySelectorAll('input[type=text], input[type=url], input:not([type])'));
      var red = inputs.find(function(i){{ return (i.id||'') !== 'name' && (i.name||'') !== 'name'; }});
      if(red){{ red.focus(); document.execCommand('selectAll', false, null);
               document.execCommand('insertText', false, 'http://localhost'); }}
      return 'filled redir_field=' + (red ? (red.id||red.name) : null);
    }})()"""))
    await asyncio.sleep(1)
    print("submit:", await ev("""(function(){
      var forms = document.querySelectorAll('form');
      var btn = forms[forms.length-1].querySelector('button[type=submit], input[type=submit], .c-btn');
      if(!btn) return 'no-submit';
      btn.click(); return 'clicked:' + (btn.textContent||btn.value||'').slice(0,15);
    })()"""))
    await asyncio.sleep(10)
    print("after_url:", await ev("location.href.slice(0,60)"))
    cred = await ev("""(function(){
      var t = document.body.innerText;
      var lines = t.split('\\n').map(function(s){return s.trim();}).filter(Boolean);
      var idx = -1;
      for (var i=0;i<lines.length;i++){ if (lines[i] === 'assay-publisher'){ idx = i; break; } }
      var ctx = idx >= 0 ? lines.slice(idx, idx+8) : lines.slice(0,8);
      return JSON.stringify(ctx);
    })()""")
    print("cred_ctx:", str(cred)[:500])
    await ws.close()

asyncio.run(main())
