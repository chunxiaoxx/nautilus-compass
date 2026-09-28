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
_o = _im.version
_im.version = lambda n: '0.0.0' if n == 'system-one-adapter' else _o(n)
import sys
sys.path.insert(0, 'system-one-adapter-python/src')
from system_one_adapter import SystemOneAdapterClient, Noul, Choice, Score
from system_one_adapter.providers.openai import OpenAIProvider
import system_one_adapter._client as _C
import system_one_adapter.providers.openai as _OP
import re as _re
_ox = _C._extract_json
_C._extract_json = lambda s: _ox(_re.sub(r'<think>.*?</think>', '', str(s), flags=_re.S).strip())
_orf = _OP._response_format
_OP._response_format = lambda schema, *, structured: {"type": "json_object"}
MM_TOK = {}
_orig_res = _OP._result
def _res_hook(response):
    pr = _orig_res(response)
    MM_TOK['in'] = pr.input_tokens; MM_TOK['out'] = pr.output_tokens
    return pr
_OP._result = _res_hook

prov = OpenAIProvider('MiniMax-M2.7', base_url='https://api.minimaxi.com/v1', api_key=key_mm)
client = SystemOneAdapterClient(structured_outputs=False, llm_answer_mode='probabilities', normalize_probabilities=True)

S_A = 'Hi, I have been trying to connect my Stripe account for 3 days and the integration keeps failing. I am losing sales. Please help ASAP.'
S_C = ('Our production database cluster has been intermittently dropping connections since Thursday 3am UTC. '
  'Application logs show connection pool exhaustion on two of five nodes. We run Postgres 16 on managed instances '
  'with a pgbouncer layer. Failover happened once at 4:15am but the issue persisted. Our on-call engineer restarted '
  'pgbouncer twice with temporary relief. Customer-facing error rate peaked at 2.3%. We have a support ticket open '
  'with the cloud provider but no response yet. This is blocking our Friday release and the leadership is asking '
  'for a status update every hour.')

def qs_A_api(): return {'urgency': {'type': 'noul', 'instructions': 'Does this message express urgency?'}}
def qs_B_api(): return {
  'urgency': {'type': 'noul', 'instructions': 'Does this message express urgency?'},
  'team': {'type': 'choice', 'instructions': 'Which team should handle this?',
           'options': ['support', 'engineering', 'billing']},
  'severity': {'type': 'score', 'instructions': 'How severe is this issue?',
               'levels': ['low', 'medium', 'high', 'critical']},
}
def qs_A_ad(): return {'urgency': Noul(instructions='Does this message express urgency?')}
def qs_B_ad(): return {
  'urgency': Noul(instructions='Does this message express urgency?'),
  'team': Choice(instructions='Which team should handle this?', options=['support', 'engineering', 'billing']),
  'severity': Score(instructions='How severe is this issue?', levels=['low', 'medium', 'high', 'critical']),
}

SUITES = [
  ('A 单问短state', S_A, qs_A_api, qs_A_ad),
  ('B 三问混合', S_A, qs_B_api, qs_B_ad),
  ('C 长state单问', S_C, qs_A_api, qs_A_ad),
]
N = 8

def jev_once(state, qs):
    body = {'state': state, 'model': 'jev-latest', 'questions': qs}
    req = urllib.request.Request('https://api.typesafe.ai/v1/systemone',
        data=json.dumps(body).encode(), method='POST',
        headers={'Authorization': f'Bearer {key_ts}', 'Content-Type': 'application/json'})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=60))
    u = r.get('usage', {})
    return time.time() - t0, u.get('input_tokens', 0) or 0, u.get('output_tokens', 0) or 0, r.get('answers', {})

def mm_once(state, qs):
    t0 = time.time()
    r = client.system_one(state, questions=qs, model=prov)
    dt = time.time() - t0
    a = json.loads(json.dumps(getattr(r, 'answers', {}), default=lambda o: getattr(o, '__dict__', str(o))))
    return dt, MM_TOK.get('in') or 0, MM_TOK.get('out') or 0, a

report = {}
for name, state, q_api, q_ad in SUITES:
    out = {}
    for leg, fn, q in (('jev', jev_once, q_api), ('mm', mm_once, q_ad)):
        lat, tin, tout, answers = [], [], [], []
        for i in range(N):
            try:
                dt, ti, to, ans = fn(state, q())
                lat.append(dt); tin.append(ti); tout.append(to)
                if i == 0: answers = [ans]
            except Exception as e:
                print(f'{name}/{leg} #{i+1} FAIL: {str(e)[:70]}')
            time.sleep(0.3)
        if lat:
            out[leg] = dict(n=len(lat), med=round(statistics.median(lat),2),
                            p25=round(sorted(lat)[max(0,len(lat)//4)],2),
                            p75=round(sorted(lat)[min(len(lat)-1,3*len(lat)//4)],2),
                            tok_in=statistics.median(tin), tok_out=statistics.median(tout))
    report[name] = out
    j, m = out.get('jev', {}), out.get('mm', {})
    if j and m:
        print(f'== {name}: Jev {j["med"]}s (p25-75 {j["p25"]}-{j["p75"]}, tok {j["tok_in"]}+{j["tok_out"]}) '
              f'vs MM {m["med"]}s (p25-75 {m["p25"]}-{m["p75"]}, tok {m["tok_in"]}+{m["tok_out"]}) '
              f'→ ratio {m["med"]/j["med"]:.1f}x')

json.dump(report, open('bench_v2_results.json','w',encoding='utf-8'), indent=1)
print('saved bench_v2_results.json')
