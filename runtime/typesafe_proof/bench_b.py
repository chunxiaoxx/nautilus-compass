import os, time, json, statistics, urllib.request
key_ts = None
for ln in open(os.path.expanduser('~/.claude/.cache/typesafe_api_key.env'), encoding='utf-8'):
    if '=' in ln and 'TYPESAFE' in ln.upper():
        key_ts = ln.split('=', 1)[1].strip().strip('"').strip("'")
key_mm = None
for ln in open(r'C:/Users/chunx/nautilus-v5/.env', encoding='utf-8'):
    if ln.startswith('MINIMAX_API_KEY='):
        key_mm = ln.split('=', 1)[1].strip()
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
def _res_hook(response):
    pr = _orig_res(response); MM['in']=pr.input_tokens; MM['out']=pr.output_tokens; return pr
_OP._result = _res_hook
prov = OpenAIProvider('MiniMax-M2.7', base_url='https://api.minimaxi.com/v1', api_key=key_mm)
client = SystemOneAdapterClient(structured_outputs=False, llm_answer_mode='probabilities', normalize_probabilities=True)

S = 'Hi, I have been trying to connect my Stripe account for 3 days and the integration keeps failing. I am losing sales. Please help ASAP.'
CRIT_MAP = {'support': 'General customer support questions', 'engineering': 'Technical and integration issues', 'billing': 'Payments, invoices and subscription'}
LEVELS = ['low', 'medium', 'high', 'critical']
def qs_api(): return {
  'urgency': {'type': 'noul', 'instructions': 'Does this message express urgency?'},
  'team': {'type': 'choice', 'instructions': 'Which team should handle this?', 'criteria': CRIT_MAP},
  'severity': {'type': 'score', 'instructions': 'How severe is this issue?', 'criteria': LEVELS},
}
def qs_ad(): return {
  'urgency': Noul(instructions='Does this message express urgency?'),
  'team': Choice(instructions='Which team should handle this?', criteria=CRIT_MAP),
  'severity': Score(instructions='How severe is this issue?', criteria=LEVELS),
}
N = 8
def jev_once():
    req = urllib.request.Request('https://api.typesafe.ai/v1/systemone',
        data=json.dumps({'state': S, 'model': 'jev-latest', 'questions': qs_api()}).encode(), method='POST',
        headers={'Authorization': f'Bearer {key_ts}', 'Content-Type': 'application/json'})
    t0=time.time(); r=json.load(urllib.request.urlopen(req, timeout=60)); u=r.get('usage',{})
    return time.time()-t0, u.get('input_tokens',0) or 0, u.get('output_tokens',0) or 0, r.get('answers',{})
def mm_once():
    t0=time.time(); r=client.system_one(S, questions=qs_ad(), model=prov)
    a=json.loads(json.dumps(getattr(r,'answers',{}), default=lambda o:getattr(o,'__dict__',str(o))))
    return time.time()-t0, MM.get('in') or 0, MM.get('out') or 0, a
res={}
for leg, fn in (('jev', jev_once), ('mm', mm_once)):
    lat, ti, to, first = [], [], [], None
    for i in range(N):
        try:
            dt,a,b,ans = fn(); lat.append(dt); ti.append(a); to.append(b)
            if i==0: first=ans
        except Exception as e: print(f'{leg} #{i+1} FAIL {str(e)[:80]}')
        time.sleep(0.3)
    if lat:
        res[leg]=dict(med=round(statistics.median(lat),2), tok_in=statistics.median(ti), tok_out=statistics.median(to), first=first)
j,m=res.get('jev',{}),res.get('mm',{})
if j and m:
    print(f"B 三问混合: Jev {j['med']}s (tok {j['tok_in']}+{j['tok_out']}) vs MM {m['med']}s (tok {m['tok_in']}+{m['tok_out']}) -> {m['med']/j['med']:.1f}x")
    print('Jev answers:', json.dumps(j['first'], ensure_ascii=False)[:300])
    print('MM  answers:', json.dumps(m['first'], ensure_ascii=False)[:300])
json.dump(res, open('bench_b_results.json','w',encoding='utf-8'), indent=1)
