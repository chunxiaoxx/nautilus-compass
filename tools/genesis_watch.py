#!/usr/bin/env python3
"""创世十家回音监视(R539): 五 issue 评论数/状态变化 → 追加 watch log,有回音写 ALERT。"""
import json, subprocess, time
from pathlib import Path

WATCH = [
    ('EverMind-AI/EverOS', 504),
    ('vectorize-io/hindsight', 5584),
    ('mem0ai/mem0', 7641),
    ('letta-ai/letta', 3453),
    ('topoteretes/cognee', 5883),
]
LOG = Path('runtime/loop/watch_genesis.log')
out = []
has_reply = False
for repo, n in WATCH:
    try:
        r = subprocess.run(['gh','api',f'repos/{repo}/issues/{n}',
                            '--jq','[.comments,.state,.updated_at]'],
                           capture_output=True, text=True, timeout=30)
        cmt, state, updated = json.loads(r.stdout)
        d = {'comments': cmt, 'state': state, 'updated_at': updated}
        line = f"{repo}#{n}: comments={d['comments']} state={d['state']} updated={d['updated_at'][:16]}"
        if d['comments'] > 0:
            has_reply = True
            line = '⚠️ REPLY! ' + line
    except Exception as e:
        line = f"{repo}#{n}: ERR {type(e).__name__}"
    out.append(line)
ts = time.strftime('%m-%d %H:%M')
with open(LOG, 'a', encoding='utf-8') as f:
    f.write(f"[{ts}] " + ' | '.join(out) + '\n')
if has_reply:
    Path('runtime/loop/GENESIS_REPLY_ALERT').write_text(f"{ts}\n" + '\n'.join(out), encoding='utf-8')
print('\n'.join(out))
