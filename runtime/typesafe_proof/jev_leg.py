import os, time, json, urllib.request
key = None
for ln in open(os.path.expanduser('~/.claude/.cache/typesafe_api_key.env'), encoding='utf-8'):
    if '=' in ln and 'TYPESAFE' in ln.upper():
        key = ln.split('=', 1)[1].strip().strip('"').strip("'")
if not key:
    raise SystemExit('key not found in env file')
state = 'Hi, I have been trying to connect my Stripe account for 3 days and the integration keeps failing. I am losing sales. Please help ASAP.'
body = {
    'state': state,
    'model': 'jev-latest',
    'questions': {'urgency': {'type': 'noul', 'instructions': 'Does this message express urgency?'}},
}
req = urllib.request.Request('https://api.typesafe.ai/v1/systemone',
    data=json.dumps(body).encode(), method='POST',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
t0 = time.time()
r = json.load(urllib.request.urlopen(req, timeout=60))
dt = time.time() - t0
print('latency_s:', round(dt, 3))
print('usage:', json.dumps(r.get('usage', {}))[:200])
print('answer:', json.dumps(r.get('answers', r), ensure_ascii=False)[:300])
