#!/usr/bin/env python3
"""deep_memory 试点 · 步骤2+3:嵌入(8400 HTTP)+ sqlite-vec 入库"""
import json, os, sqlite3, time
import sqlite_vec

BASE = os.path.dirname(__file__)
IN = os.path.join(BASE, 'blocks_compass.jsonl')
DB = os.path.join(BASE, 'deep_memory_compass.db')
EMBED_URL = 'http://127.0.0.1:8400/embed'
BATCH = 64

def embed(texts):
    import urllib.request
    req = urllib.request.Request(EMBED_URL, data=json.dumps({'texts': texts}).encode(),
                                 headers={'Content-Type': 'application/json'})
    r = json.loads(urllib.request.urlopen(req, timeout=120).read())
    return r['embeddings']

def main():
    blocks = [json.loads(l) for l in open(IN, encoding='utf-8')]
    print(f'blocks: {len(blocks)}')
    if os.path.exists(DB): os.remove(DB)
    con = sqlite3.connect(DB)
    con.enable_load_extension(True)
    sqlite_vec.load(con)
    con.execute('''CREATE VIRTUAL TABLE blocks USING vec0(
        id TEXT PRIMARY KEY,
        sid TEXT, grade TEXT, ts TEXT,
        embedding float[1024])''')
    t0 = time.time()
    n_err = 0
    for i in range(0, len(blocks), BATCH):
        batch = blocks[i:i+BATCH]
        try:
            vecs = embed([b['text'] for b in batch])
        except Exception as e:
            n_err += len(batch); print(f'batch {i}: ERR {e}'); continue
        rows = [(b['id'], b['sid'], b['grade'], b['ts'],
                 json.dumps(v, separators=(',',':'))) for b, v in zip(batch, vecs)]
        con.executemany('INSERT INTO blocks(id, sid, grade, ts, embedding) VALUES(?,?,?,?, vec_f32(?))', rows)
        if (i // BATCH) % 10 == 0:
            print(f'  {i+len(batch)}/{len(blocks)} ({time.time()-t0:.0f}s)', flush=True)
    con.commit()
    n = con.execute('SELECT count(*) FROM blocks').fetchone()[0]
    print(f'入库 {n} 块 | 失败 {n_err} | 耗时 {time.time()-t0:.0f}s | 库体积 {os.path.getsize(DB)//1048576}MB')

if __name__ == '__main__':
    main()
