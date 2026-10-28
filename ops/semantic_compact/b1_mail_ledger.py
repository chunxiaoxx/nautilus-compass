#!/usr/bin/env python3
"""语义压实 B1:outreach 67 函 → 函件台账(glm-5.3-flash)
判据:SEMANTIC_COMPACT_PREREG_20261024.md J1-J4
产出:docs/ledgers/MAIL_LEDGER_raw.md(台账行)+ 高价值函收录标记
"""
import os, json, glob, time, urllib.request

BASE = os.environ.get('ANTHROPIC_BASE_URL', '').rstrip('/')
KEY = os.environ.get('ANTHROPIC_AUTH_TOKEN') or ''
MODEL = 'glm-5.3-flash'
OUT = 'docs/ledgers/MAIL_LEDGER_raw.md'
FILES = sorted(glob.glob('runtime/outreach/*.md'))

PROMPT = """你是函件台账压缩员。以下是组织外发函件存档(可能一批多个)。对每一函输出一行台账(markdown 表格行),格式严格:
| 函件文件名 | trace/主题 | 事由(≤25字) | 结果/状态(≤20字) | 死线处置(≤15字) | 关键坐标(档内提到的文件/commit/判据档路径,≤2个) |

判定规则:
- 高价值标记:函内含"用户拍板/纪律条款/对外承诺/定谳/拍板"任一词 → 该行末加 【高价值,收录全文】
- 普通函只出一行,不抄正文
- 一批多函按序输出全部行,不要遗漏任何一个

函件开始
"""

def llm(text, retries=4):
    payload = {'model': MODEL, 'max_tokens': 6000,
               'messages': [{'role':'user','content': PROMPT + text[:24000] + '\n函件结束'}]}
    for a in range(retries):
        req = urllib.request.Request(BASE + '/v1/messages', data=json.dumps(payload).encode(),
            headers={'x-api-key': KEY, 'Authorization': f'Bearer {KEY}',
                     'anthropic-version':'2023-06-01','Content-Type':'application/json'})
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=240).read())
            return ''.join(c.get('text','') for c in r.get('content',[]) if c.get('type')=='text')
        except urllib.error.HTTPError as e:
            if e.code in (429, 524, 503):
                wait = 15*(a+1); print(f'  退避{wait}s', flush=True); time.sleep(wait)
            else: raise
    return ''

def main():
    lines = ['# 函件台账(B1 语义压实 · glm-5.3-flash · 2026-10-24)', '',
             '| 函件 | trace/主题 | 事由 | 结果/状态 | 死线处置 | 关键坐标 |', '|---|---|---|---|---|---|']
    batch, done = [], 0
    for f in FILES:
        batch.append(f'═══ 文件: {os.path.basename(f)} ═══\n' + open(f, encoding='utf-8', errors='replace').read()[:3500])
        if len(batch) == 6 or f == FILES[-1]:
            out = llm('\n\n'.join(batch))
            rows = [l for l in out.splitlines() if l.strip().startswith('|') and '---' not in l]
            # 跳过模型自己复制的表头
            rows = [r for r in rows if '函件' not in r[:6] or 'trace' in r]
            lines.extend(rows)
            done += len(batch); print(f'{done}/{len(FILES)} 批出 {len(rows)} 行', flush=True)
            batch = []
            time.sleep(2)
    open(OUT, 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    n = sum(1 for l in lines if l.startswith('| ') and '---' not in l and 'trace' not in l)
    print(f'✅ 台账落盘 {OUT} | 数据行 {n}(J1 判据: 需≥{len(FILES)})')

if __name__ == '__main__':
    main()
