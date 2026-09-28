import sys, time, json
import importlib.metadata as _im
_orig_v = _im.version
_im.version = lambda name: "0.0.0-local" if name == "system-one-adapter" else _orig_v(name)
sys.path.insert(0, 'system-one-adapter-python/src')
from system_one_adapter import SystemOneAdapterClient, Noul
from system_one_adapter.providers.openai import OpenAIProvider
import system_one_adapter._client as _C
_orig_x = _C._extract_json
def _strip_think(s):
    import re as _re
    return _orig_x(_re.sub(r'<think>.*?</think>', '', str(s), flags=_re.S).strip())
_C._extract_json = _strip_think
import system_one_adapter.providers.openai as _OP
def _rf(schema, *, structured):
    if structured:
        return {"type": "json_schema", "json_schema": {"name": "evaluation", "schema": schema, "strict": True}}
    return {"type": "json_object"}
_OP._response_format = _rf

key = None
for ln in open(r'C:/Users/chunx/nautilus-v5/.env', encoding='utf-8'):
    if ln.startswith('MINIMAX_API_KEY='):
        key = ln.split('=', 1)[1].strip()

prov = OpenAIProvider('MiniMax-M2.7', base_url='https://api.minimaxi.com/v1', api_key=key)
client = SystemOneAdapterClient(structured_outputs=False, llm_answer_mode='probabilities', normalize_probabilities=True)
state = 'Hi, I have been trying to connect my Stripe account for 3 days and the integration keeps failing. I am losing sales. Please help ASAP.'
qs = {'urgency': Noul(instructions='Does this message express urgency?')}
t0 = time.time()
r = client.system_one(state, questions=qs, model=prov)
dt = time.time() - t0
ans = getattr(r, 'answers', None) or r
print('latency_s:', round(dt, 3))
print('answer:', json.dumps(ans, default=lambda o: getattr(o, '__dict__', str(o)), ensure_ascii=False)[:400])
