import json

def load(p):
    rows = {}
    for line in open(p, encoding='utf-8'):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        rows[r['id']] = r
    return rows

mac = load('/Users/chunxiao.wang/.codex/session_index.jsonl')
lap = load('/tmp/laptop_session_index.jsonl')
merged = dict(lap)
merged.update(mac)  # Mac 现有行优先(最新状态)
out = sorted(merged.values(), key=lambda r: r.get('updated_at', ''))
with open('/Users/chunxiao.wang/.codex/session_index.jsonl', 'w', encoding='utf-8') as f:
    for r in out:
        f.write(json.dumps(r, ensure_ascii=False) + '\n')
print('laptop=%d mac=%d merged=%d' % (len(lap), len(mac), len(out)))
