import os, time, json, statistics, urllib.request, re

key_ts = None
for ln in open(os.path.expanduser('~/.claude/.cache/typesafe_api_key.env'), encoding='utf-8'):
    if '=' in ln and 'TYPESAFE' in ln.upper():
        key_ts = ln.split('=', 1)[1].strip().strip('"').strip("'")
key_mm = None
for ln in open(r'C:/Users/chunx/nautilus-v5/.env', encoding='utf-8'):
    if ln.startswith('MINIMAX_API_KEY='):
        key_mm = ln.split('=', 1)[1].strip()
key_glm = None
for ln in open(os.path.expanduser('~/.arkcli/config.yaml'), encoding='utf-8'):
    m = re.match(r'\s*api_key:\s*(\S+)', ln)
    if m and len(m.group(1)) > 20:
        key_glm = m.group(1); break
assert key_glm, 'glm key not found in arkcli config'

import importlib.metadata as _im
_o = _im.version; _im.version = lambda n: '0.0.0' if n == 'system-one-adapter' else _o(n)
import sys
sys.path.insert(0, 'system-one-adapter-python/src')
from system_one_adapter import SystemOneAdapterClient, Noul, Choice, Score
from system_one_adapter.providers.openai import OpenAIProvider
import system_one_adapter._client as _C, system_one_adapter.providers.openai as _OP
import re as _re
_ox = _C._extract_json
_C._extract_json = lambda s: _ox(_re.sub(r'<think>.*?</think>', '', str(s), flags=_re.S).strip())
_OP._response_format = lambda schema, *, structured: {"type": "json_object"}
MM = {}
_orig_res = _OP._result
def _res_hook(r):
    pr = _orig_res(r); MM['in']=pr.input_tokens; MM['out']=pr.output_tokens; return pr
_OP._result = _res_hook
client = SystemOneAdapterClient(structured_outputs=False, llm_answer_mode='probabilities', normalize_probabilities=True)

S = 'Hi, I have been trying to connect my Stripe account for 3 days and the integration keeps failing. I am losing sales. Please help ASAP.'
CRIT = {'support': 'General customer support questions', 'engineering': 'Technical and integration issues', 'billing': 'Payments, invoices and subscription'}
LEVELS = ['low', 'medium', 'high', 'critical']
def qs_ad(): return {
  'urgency': Noul(instructions='Does this message express urgency?'),
  'team': Choice(instructions='Which team should handle this?', criteria=CRIT),
  'severity': Score(instructions='How severe is this issue?', criteria=LEVELS),
}
N = 8

def jev_once():
    q = {'urgency': {'type':'noul','instructions':'Does this message express urgency?'},
         'team': {'type':'choice','instructions':'Which team should handle this?','criteria':CRIT},
         'severity': {'type':'score','instructions':'How severe is this issue?','criteria':LEVELS}}
    req = urllib.request.Request('https://api.typesafe.ai/v1/systemone',
        data=json.dumps({'state': S, 'model': 'jev-latest', 'questions': q}).encode(), method='POST',
        headers={'Authorization': f'Bearer {key_ts}', 'Content-Type': 'application/json'})
    t0=time.time(); r=json.load(urllib.request.urlopen(req, timeout=60)); u=r.get('usage',{})
    return time.time()-t0, u.get('input_tokens',0) or 0, u.get('output_tokens',0) or 0

def make_mm(model):
    prov = OpenAIProvider(model, base_url='https://api.minimaxi.com/v1', api_key=key_mm)
    def f():
        t0=time.time(); client.system_one(S, questions=qs_ad(), model=prov)
        return time.time()-t0, MM.get('in') or 0, MM.get('out') or 0
    return f

def make_glm(model):
    prov = OpenAIProvider(model, base_url='https://ark.cn-beijing.volces.com/api/coding/v3', api_key=key_glm)
    def f():
        t0=time.time(); client.system_one(S, questions=qs_ad(), model=prov)
        return time.time()-t0, MM.get('in') or 0, MM.get('out') or 0
    return f

LEGS = [('Jev', jev_once),
        ('MiniMax-M2.7', make_mm('MiniMax-M2.7')),
        ('MiniMax-M2.7-hs', make_mm('MiniMax-M2.7-highspeed')),
        ('glm-5.3-flash', make_glm('glm-5.3-flash'))]
res = {}
for name, fn in LEGS:
    lat, ti, to = [], [], []
    for i in range(N):
        try:
            dt, a, b = fn(); lat.append(dt); ti.append(a); to.append(b)
        except Exception as e:
            print(f'{name} #{i+1} FAIL {str(e)[:90]}')
        time.sleep(0.3)
    if lat:
        res[name] = dict(n=len(lat), med=round(statistics.median(lat),2),
                         p25=round(sorted(lat)[len(lat)//4],2), p75=round(sorted(lat)[3*len(lat)//4],2),
                         tok_in=statistics.median(ti), tok_out=statistics.median(to))
        print(name, res[name])
jev = res.get('Jev', {}).get('med', 0)
for k, v in res.items():
    if k != 'Jev' and jev:
        print(f'ratio vs Jev: {k} = {v["med"]/jev:.1f}x')
json.dump(res, open('bench_multi_results.json','w',encoding='utf-8'), indent=1)
