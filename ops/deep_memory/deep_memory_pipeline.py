#!/usr/bin/env python3
"""deep_memory 全量管线(试点泛化版):任意框 → 提取→分块→嵌入→入库
用法: python deep_memory_pipeline.py --dir <projects子目录名> [--min-size 3000]
产出: deep_memory_<框名>.db + blocks_<框名>.jsonl
嵌入失败可重跑(跳过库中已有 id)。
"""
import json, glob, os, hashlib, sqlite3, time, sys, argparse, urllib.request

def session_text(path):
    msgs, user_real = [], 0
    try:
        with open(path, encoding='utf-8', errors='replace') as f:
            for line in f:
                try: j = json.loads(line)
                except Exception: continue
                t = j.get('type')
                if t not in ('user', 'assistant'): continue
                m = j.get('message') or {}
                c = m.get('content')
                ts = (j.get('timestamp') or '')[:19]
                txt = c.strip() if isinstance(c, str) else ''
                if not txt and isinstance(c, list):
                    txt = '\n'.join(i.get('text','') for i in c
                                    if isinstance(i, dict) and i.get('type') == 'text').strip()
                if not txt or txt.startswith('<') or txt.startswith('Caveat:'): continue
                if 'tool_result' in txt[:40]: continue
                if t == 'user':
                    head = txt[:60]
                    if '蒸馏器' in head: continue
                    user_real += 1
                msgs.append((t, txt, ts))
    except Exception:
        return 0, []
    return user_real, msgs

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True, help='~/.claude/projects 下的目录名')
    ap.add_argument('--min-size', type=int, default=3000, help='跳过 <N bytes 空壳会话')
    a = ap.parse_args()
    P = os.path.expanduser(f'~/.claude/projects/{a.dir}')
    tag = a.dir.split('-Projects-')[-1] or 'home'
    OUT = os.path.join(os.path.dirname(__file__), f'blocks_{tag}.jsonl')
    DB = os.path.join(os.path.dirname(__file__), f'deep_memory_{tag}.db')
    CHUNK, OVERLAP, MIN_B = 1200, 120, 60

    blocks, seen = [], set()
    stats = {'high': 0, 'mid': 0, 'low': 0, 'sessions': 0, 'skipped_shell': 0}
    for f in sorted(glob.glob(f'{P}/*.jsonl')):
        sz = os.path.getsize(f)
        if sz < a.min_size:
            stats['skipped_shell'] += 1; continue
        user_real, msgs = session_text(f)
        if not msgs: stats['skipped_shell'] += 1; continue
        stats['sessions'] += 1
        g = 'high' if (sz > 30000 and user_real >= 1) else ('mid' if sz > 8000 else 'low')
        stats[g] += 1
        sid = os.path.basename(f)[:8]
        buf, start_ts = [], None
        def flush():
            text = '\n'.join(buf).strip()
            if len(text) < MIN_B: return
            i = 0
            while i < len(text):
                chunk = text[i:i+CHUNK]
                if len(chunk) >= MIN_B:
                    ch = hashlib.md5(chunk.encode()).hexdigest()
                    if ch not in seen:
                        seen.add(ch)
                        blocks.append({'id': ch, 'sid': sid, 'grade': g, 'ts': start_ts or '', 'text': chunk})
                i += CHUNK - OVERLAP
        for t, txt, ts in msgs:
            if start_ts is None and ts: start_ts = ts
            buf.append(f'[{"用户" if t=="user" else "助手"}] {txt}')
            if sum(len(x) for x in buf) > CHUNK*2:
                flush(); buf = [buf[-1]] if len(buf) > 1 else []
        flush()
    with open(OUT, 'w', encoding='utf-8') as out:
        for b in blocks: out.write(json.dumps(b, ensure_ascii=False) + '\n')
    print(f'[{tag}] 会话 {stats["sessions"]}(跳空壳 {stats["skipped_shell"]})| blocks {len(blocks)} | {stats}')

    # 嵌入+入库(可重入:跳过已有 id)
    import sqlite_vec
    if not os.path.exists(DB):
        con = sqlite3.connect(DB); con.enable_load_extension(True); sqlite_vec.load(con)
        con.execute('''CREATE VIRTUAL TABLE blocks USING vec0(
            id TEXT PRIMARY KEY, sid TEXT, grade TEXT, ts TEXT, embedding float[1024])''')
        con.commit()
    con = sqlite3.connect(DB); con.enable_load_extension(True); sqlite_vec.load(con)
    have = {r[0] for r in con.execute('SELECT id FROM blocks')}
    todo = [b for b in blocks if b['id'] not in have]
    print(f'待嵌入 {len(todo)}(库中已有 {len(have)})')
    t0, n_err = time.time(), 0
    BATCH = 64
    for i in range(0, len(todo), BATCH):
        batch = todo[i:i+BATCH]
        try:
            req = urllib.request.Request('http://127.0.0.1:8400/embed',
                data=json.dumps({'texts': [b['text'] for b in batch]}).encode(),
                headers={'Content-Type': 'application/json'})
            vecs = json.loads(urllib.request.urlopen(req, timeout=180).read())['embeddings']
        except Exception as e:
            n_err += len(batch); print(f'  batch{i}: {str(e)[:60]}', flush=True); continue
        con.executemany('INSERT INTO blocks(id,sid,grade,ts,embedding) VALUES(?,?,?,?,vec_f32(?))',
            [(b['id'], b['sid'], b['grade'], b['ts'], json.dumps(v, separators=(',',':')))
             for b, v in zip(batch, vecs)])
        con.commit()
        if (i//BATCH) % 20 == 0:
            print(f'  {i+len(batch)}/{len(todo)} ({time.time()-t0:.0f}s)', flush=True)
    n = con.execute('SELECT count(*) FROM blocks').fetchone()[0]
    print(f'✅ [{tag}] 入库 {n} | 失败 {n_err} | {os.path.getsize(DB)//1048576}MB')

if __name__ == '__main__':
    main()
