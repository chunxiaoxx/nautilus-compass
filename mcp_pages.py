"""MVP-4 pages: /signup and /console (vanilla HTML+JS, zero CDN deps).

The console stores the JWT in localStorage, lists tokens, and creates/revokes
them via the MVP-3 JSON API. Server-rendered shell only; all state changes go
through fetch() so the API stays the single source of truth.
"""
from __future__ import annotations

_COMMON = """
<style>
 body{font-family:system-ui,sans-serif;max-width:560px;margin:48px auto;padding:0 16px}
 input,button{font-size:15px;padding:8px;margin:4px 0;width:100%;box-sizing:border-box}
 button{cursor:pointer} .row{display:flex;gap:8px} .muted{color:#666;font-size:13px}
 .ok{color:#0a7d38}.err{color:#b3261e;white-space:pre-wrap} table{width:100%;font-size:14px}
 td,th{padding:4px 6px;text-align:left;border-bottom:1px solid #ddd}
</style>"""

SIGNUP_PAGE = f"""<!doctype html><html><head><meta charset="utf-8">
<title>compass · signup</title>{_COMMON}</head><body>
<h2>Create your compass account</h2>
<form onsubmit="return doSignup(event)">
 <input id="email" type="email" placeholder="email" required>
 <input id="pw" type="password" placeholder="passphrase (min 8 chars)" minlength="8" required>
 <button>Sign up</button>
</form>
<p class="muted">Already registered? <a href="/console">Log in on the console</a>.</p>
<pre id="msg"></pre>
<script>
async function doSignup(ev) {{
  ev.preventDefault();
  const r = await fetch('/signup', {{method:'POST',
    headers:{{'content-type':'application/json'}},
    body: JSON.stringify({{email: email.value, passphrase: pw.value}})}});
  const j = await r.json();
  if (r.ok) {{ msg.className='ok'; msg.textContent='Account created. You can now log in on the console.'; }}
  else {{ msg.className='err'; msg.textContent=j.error || r.status; }}
  return false;
}}
</script></body></html>"""

CONSOLE_PAGE = f"""<!doctype html><html><head><meta charset="utf-8">
<title>compass · console</title>{_COMMON}</head><body>
<h2>compass console</h2>
<div id="auth">
 <form onsubmit="return doLogin(event)">
  <input id="email" type="email" placeholder="email" required>
  <input id="pw" type="password" placeholder="passphrase" required>
  <button>Log in</button>
 </form>
 <p class="muted">No account? <a href="/signup">Sign up</a>.</p>
</div>
<div id="panel" hidden>
 <p class="ok" id="who"></p>
 <div class="row">
  <input id="tokname" placeholder="token name (e.g. laptop-ci)">
  <button onclick="mkToken()">New token</button>
 </div>
 <pre id="newtok" class="ok"></pre>
 <p class="muted">Copy the token now — it is shown only once.</p>
 <table id="toks"><tr><th>name</th><th>prefix</th><th>scopes</th><th>status</th><th></th></tr></table>
 <p><button onclick="logout()">Log out</button></p>
</div>
<pre id="msg" class="err"></pre>
<script>
const H = () => ({{'Authorization':'Bearer '+localStorage.cmp_jwt,
                  'content-type':'application/json'}});
async function doLogin(ev) {{
  ev.preventDefault();
  const r = await fetch('/login', {{method:'POST',
    headers:{{'content-type':'application/json'}},
    body: JSON.stringify({{email: email.value, passphrase: pw.value}})}});
  if (!r.ok) {{ msg.textContent = (await r.json()).error; return false; }}
  localStorage.cmp_jwt = (await r.json()).token;
  boot(); return false;
}}
function logout() {{ delete localStorage.cmp_jwt; location.reload(); }}
async function mkToken() {{
  const r = await fetch('/tokens', {{method:'POST', headers:H(),
    body: JSON.stringify({{name: tokname.value || 'unnamed'}})}});
  if (!r.ok) {{ msg.textContent = 'create failed: ' + r.status; return; }}
  const j = await r.json();
  newtok.textContent = j.token; load();
}}
async function revoke(id) {{
  const r = await fetch('/tokens/' + id, {{method:'DELETE', headers:H()}});
  if (!r.ok) msg.textContent = 'revoke failed: ' + r.status;
  load();
}}
async function load() {{
  const r = await fetch('/tokens', {{headers: H()}});
  if (r.status === 401) {{ logout(); return; }}
  const rows = (await r.json()).tokens;
  const t = document.getElementById('toks');
  t.innerHTML = '<tr><th>name</th><th>prefix</th><th>scopes</th><th>status</th><th></th></tr>';
  for (const k of rows) {{
    const tr = t.insertRow();
    tr.insertCell().textContent = k.name;
    tr.insertCell().textContent = k.prefix + '…';
    tr.insertCell().textContent = k.scopes;
    tr.insertCell().textContent = k.revoked ? 'revoked' : 'active';
    const c = tr.insertCell();
    if (!k.revoked) {{
      const b = document.createElement('button');
      b.textContent = 'revoke'; b.onclick = () => revoke(k.token_id);
      c.appendChild(b);
    }}
  }}
}}
function boot() {{
  if (!localStorage.cmp_jwt) return;
  auth.hidden = true; panel.hidden = false; load();
}}
boot();
</script></body></html>"""


def signup_page() -> str:
    return SIGNUP_PAGE


def console_page() -> str:
    return CONSOLE_PAGE
