#!/usr/bin/env python3
"""创世十家回音监视(R539·10/31 根修): 非自家评论数变化 → watch log,新增回音写 ALERT。

10/31 根修(自回声教训·审计档#5 兄弟件): 原版按 issue.comments 总数>0 报警——
我方跟帖也计数 → EverOS/hindsight 永久重复报警(挂 9-11 天+重复清警两次)。
改为: ①计数排除 chunxiaoxx 作者 ②与 runtime/loop/genesis_state.json 上态比对,
仅"外部评论数增加"时写 ALERT 并更新状态。
"""
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
STATE = Path('runtime/loop/genesis_state.json')
ME = 'chunxiaoxx'

try:
    state = json.loads(STATE.read_text())
except Exception:
    state = {}

out, has_new = [], False
for repo, n in WATCH:
    key = f'{repo}#{n}'
    try:
        r = subprocess.run(
            ['/opt/homebrew/bin/gh', 'api',
             f'repos/{repo}/issues/{n}/comments?per_page=100',
             '--jq', f'[.[] | select(.user.login != "{ME}") | {{a:.user.login,t:.created_at}}]'],
            capture_output=True, text=True, timeout=30)
        foreign = json.loads(r.stdout)
        cnt = len(foreign)
        prev = int(state.get(key, 0))
        last = foreign[-1] if foreign else None
        if cnt > 0:
            tag = ' ⚠️ NEW!' if cnt > prev else ''
            line = f"{key}: 外部评论={cnt}(上态{prev}) 最新[{last['a']} {last['t'][:16]}]{tag}"
        else:
            line = f"{key}: 外部评论=0"
        if cnt > prev:
            has_new = True
        state[key] = cnt
    except Exception as e:
        line = f"{key}: ERR {type(e).__name__}"
    out.append(line)

ts = time.strftime('%m-%d %H:%M')
with open(LOG, 'a', encoding='utf-8') as f:
    f.write(f"[{ts}] " + ' | '.join(out) + '\n')
if has_new:
    Path('runtime/loop/GENESIS_REPLY_ALERT').write_text(
        f"{ts}\n" + '\n'.join(out), encoding='utf-8')
STATE.write_text(json.dumps(state, indent=1))
print('\n'.join(out))
