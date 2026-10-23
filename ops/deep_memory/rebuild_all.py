#!/usr/bin/env python3
"""从已有 blocks_*.jsonl 重建 db(跳过提取,只嵌入+入库)"""
import json, os, sqlite3, glob, time, urllib.request
import sqlite_vec

BASE = os.path.dirname(os.path.abspath(__file__))
BATCH = 64

def embed(texts):
    req = urllib.request.Request('http://127.0.0.1:8400/embed',
        data=json.dumps({'texts': texts}).encode(), headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())['embeddings']

def main():
    for jl in sorted(glob.glob(os.path.join(BASE, 'blocks_*.jsonl'))):
        tag = os.path.basename(jl)[7:-6]
        db = os.path.join(BASE, f'deep_memory_{tag}.db')
        blocks = [json.loads(l) for l in open(jl, encoding='utf-8')]
        if os.path.exists(db): os.remove(db)
        con = sqlite3.connect(db); con.enable_load_extension(True); sqlite_vec.load(con)
        con.execute('''CREATE VIRTUAL TABLE blocks USING vec0(
            id TEXT PRIMARY KEY, sid TEXT, grade TEXT, ts TEXT, embedding float[1024])''')
        t0, n_err = time.time(), 0
        for i in range(0, len(blocks), BATCH):
            batch = blocks[i:i+BATCH]
            try:
                vecs = embed([b['text'] for b in batch])
            except Exception as e:
                n_err += len(batch); print(f'  [{tag}] batch{i} {str(e)[:50]}', flush=True); continue
            con.executemany('INSERT INTO blocks(id,sid,grade,ts,embedding) VALUES(?,?,?,?,vec_f32(?))',
                [(b['id'], b['sid'], b['grade'], b['ts'], json.dumps(v, separators=(',',':')))
                 for b, v in zip(batch, vecs)])
            con.commit()
            if (i//BATCH) % 30 == 0:
                print(f'  [{tag}] {i+len(batch)}/{len(blocks)} ({time.time()-t0:.0f}s)', flush=True)
        n = con.execute('SELECT count(*) FROM blocks').fetchone()[0]
        print(f'✅ [{tag}] {n} 块 失败{n_err} {os.path.getsize(db)//1048576}MB ({time.time()-t0:.0f}s)', flush=True)

if __name__ == '__main__':
    main()
