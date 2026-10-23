#!/usr/bin/env python3
"""deep_memory 试点 · 验收探针:20 题打分(判据 3/4/5)"""
import json, os, sqlite3, time, urllib.request
import sqlite_vec

BASE = os.path.dirname(__file__)
DB = os.path.join(BASE, 'deep_memory_compass.db')

def embed(texts):
    req = urllib.request.Request('http://127.0.0.1:8400/embed',
        data=json.dumps({'texts': texts}).encode(), headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=60).read())['embeddings']

def deep_recall(q, k=5):
    v = embed([q])[0]
    con = sqlite3.connect(DB)
    con.enable_load_extension(True); sqlite_vec.load(con)
    t0 = time.time()
    rows = con.execute('''SELECT id, sid, grade, distance FROM blocks WHERE embedding MATCH ?
        AND k = ? ORDER BY distance''', (json.dumps(v), k)).fetchall()
    return rows, (time.time()-t0)

def main():
    global SRC
    SRC = {json.loads(l)['id']: json.loads(l)['text'] for l in open(os.path.join(BASE, 'blocks_compass.jsonl'), encoding='utf-8')}
    probes = json.load(open(os.path.join(BASE, 'probe_20q.json')))
    hit, first_high, lat = 0, 0, []
    print(f'{"#":>2} {"首命中grade":10} {"距离":>7} {"耗时":>5}  问题')
    for i, p in enumerate(probes, 1):
        rows, dt = deep_recall(p['q'])
        lat.append(dt)
        top_grade = rows[0][2] if rows else '-'
        if top_grade == 'high': first_high += 1
        # 命中判定:top5 任一块文本含 expect 关键词(text 从 jsonl 源反查)
        ok = False
        if rows:
            for r in rows:
                txt = SRC.get(r[0])
                if txt and p['expect'].split('/')[0].strip().lower() in txt.lower():
                    ok = True; break
        hit += ok
        print(f'{i:>2} {top_grade:10} {rows[0][3] if rows else 0:>7.3f} {dt:>4.1f}s  {p["q"][:30]} {"✓" if ok else "✗"}')
    print(f'\n命中率: {hit}/20 (门≥16) | 首命中high: {first_high}/20 (门≥14) | P50时延: {sorted(lat)[10]:.2f}s (门≤3s)')

if __name__ == '__main__':
    main()
