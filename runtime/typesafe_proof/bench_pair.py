import os, time, json, statistics, urllib.request

key_ts = None
for ln in open(os.path.expanduser('~/.claude/.cache/typesafe_api_key.env'), encoding='utf-8'):
    if '=' in ln and 'TYPESAFE' in ln.upper():
        key_ts = ln.split('=', 1)[1].strip().strip('"').strip("'")
key_mm = None
for ln in open(r'C:/Users/chunx/nautilus-v5/.env', encoding='utf-8'):
    if ln.startswith('MINIMAX_API_KEY='):
        key_mm = ln.split('=', 1)[1].strip()

state = 'Hi, I have been trying to connect my Stripe account for 3 days and the integration keeps failing. I am losing sales. Please help ASAP.'
qs_api = {'urgency': {'type': 'noul', 'instructions': 'Does this message express urgency?'}}
N = 5

def jev_once():
    body = {'state': state, 'model': 'jev-latest', 'questions': qs_api}
    req = urllib.request.Request('https://api.typesafe.ai/v1/systemone',
        data=json.dumps(body).encode(), method='POST',
        headers={'Authorization': f'Bearer {key_ts}', 'Content-Type': 'application/json'})
    t0 = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=60))
    u = r.get('usage', {})
    return time.time() - t0, u.get('input_tokens', 0), u.get('output_tokens', 0), r.get('answers', {}).get('urgency', {}).get('noul')

import importlib.metadata as _im
_o = _im.version
_im.version = lambda n: '0.0.0' if n == 'system-one-adapter' else _o(n)
import sys
sys.path.insert(0, 'system-one-adapter-python/src')
from system_one_adapter import SystemOneAdapterClient, Noul
from system_one_adapter.providers.openai import OpenAIProvider
import system_one_adapter._client as _C
import re as _re
_ox = _C._extract_json
_C._extract_json = lambda s: _ox(_re.sub(r'<think>.*?</think>', '', str(s), flags=_re.S).strip())
import system_one_adapter.providers.openai as _OP
_OP._response_format = lambda schema, *, structured: {"type": "json_object"}

prov = OpenAIProvider('MiniMax-M2.7', base_url='https://api.minimaxi.com/v1', api_key=key_mm)
client = SystemOneAdapterClient(structured_outputs=False, llm_answer_mode='probabilities', normalize_probabilities=True)

def mm_once():
    t0 = time.time()
    r = client.system_one(state, questions={'urgency': Noul(instructions='Does this message express urgency?')}, model=prov)
    dt = time.time() - t0
    a = getattr(r, 'answers', None)
    noul = None
    try: noul = a['urgency'].noul
    except Exception: noul = json.loads(json.dumps(a, default=lambda o: getattr(o, '__dict__', str(o)))).get('urgency', {}).get('noul')
    return dt, 0, 0, noul

for name, fn in (('Jev', jev_once), ('MiniMax-M2.7', mm_once)):
    lat, nouls = [], []
    for i in range(N):
        try:
            dt, it, ot, noul = fn()
            lat.append(dt); nouls.append(noul)
            print(f'{name} #{i+1}: {dt:.2f}s noul={noul}' + (f' tokens={it}+{ot}' if it else ''))
        except Exception as e:
            print(f'{name} #{i+1}: FAIL {str(e)[:80]}')
        time.sleep(0.5)
    if lat:
        print(f'== {name}: median {statistics.median(lat):.2f}s  noul_mean {statistics.mean([n for n in nouls if n is not None]):.3f}')
