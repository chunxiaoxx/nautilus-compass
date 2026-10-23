#!/usr/bin/env python3
"""deep_memory 试点 · 语义判分重测:k3-256k 逐题判 top1/top5 与问题的相关性
独立于关键词法;判分器只看问题+块文本,输出 RELEVANT/NOT。
"""
import json, os, time, urllib.request
import sqlite3, sqlite_vec

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'deep_memory_compass.db')
API = os.environ.get('ANTHROPIC_BASE_URL', '').rstrip('/')
KEY = os.environ.get('ANTHROPIC_AUTH_TOKEN') or os.environ.get('ANTHROPIC_API_KEY', '')

def embed(t):
    req = urllib.request.Request('http://127.0.0.1:8400/embed',
        data=json.dumps({'texts': t}).encode(), headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())['embeddings']

def llm_judge(q, blocks):
    body = f"问题: {q}\n\n以下是从历史工作会话中检索出的{len(blocks)}个文本块。逐块判断:该块内容是否包含回答该问题所需的实质相关信息?\n只输出 JSON 数组,如 [1,0,1,0,0](1=相关,0=不相关),不要其他文字。\n\n"
    for i, b in enumerate(blocks):
        body += f"--- 块{i+1} ---\n{b[:800]}\n\n"
    payload = {'model': 'k3-256k', 'max_tokens': 8000,
               'thinking': {'type': 'disabled'},
               'messages': [{'role': 'user', 'content': body}]}
    r = None
    for attempt in range(5):
        req = urllib.request.Request(API + '/v1/messages',
            data=json.dumps(payload).encode(),
            headers={'x-api-key': KEY, 'Authorization': f'Bearer {KEY}',
                     'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'})
        try:
            r = json.loads(urllib.request.urlopen(req, timeout=240).read()); break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 20 * (attempt + 1); print(f'  429 退避 {wait}s', flush=True); time.sleep(wait)
            else: raise
    if r is None: return [0]*3
    txt = ''
    for c in r.get('content', []):
        if c.get('type') == 'text': txt += c.get('text', '')
    import re
    m = re.search(r'\[[01, ]+\]', txt)
    return [int(x) for x in m.group()[1:-1].split(',')] if m else []

def deep_recall(q, k=5):
    v = embed([q])[0]
    con = sqlite3.connect(DB); con.enable_load_extension(True); sqlite_vec.load(con)
    return con.execute('SELECT id, grade, distance FROM blocks WHERE embedding MATCH ? AND k=? ORDER BY distance',
                       (json.dumps(v), k)).fetchall()

def main():
    SRC = {json.loads(l)['id']: json.loads(l)['text'] for l in open(os.path.join(BASE, 'blocks_compass.jsonl'), encoding='utf-8')}
    probes = json.load(open(os.path.join(BASE, 'probe_20q.json')))
    hit = 0; details = []
    for i, p in enumerate(probes, 1):
        rows = deep_recall(p['q'])
        blocks = [SRC.get(r[0], '')[:600] for r in rows[:3]]
        try:
            marks = llm_judge(p['q'], blocks)
        except Exception as e:
            print(f'{i} 判分ERR {str(e)[:60]}'); marks = [0]*5
        top_relevant = bool(marks and marks[0])
        any_relevant = any(marks)
        hit += any_relevant
        details.append({'q': p['q'], 'marks': marks, 'any': any_relevant})
        print(f'{i:>2} {"✓" if any_relevant else "✗"} marks={marks} {p["q"][:32]}')
        time.sleep(1)
    print(f'\n【语义判分重测】any-top5 命中: {hit}/20 (门≥16) | 详情落 verdict 文件')
    json.dump(details, open(os.path.join(BASE, 'semantic_rescore_20261023.json'), 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
