#!/usr/bin/env python3
"""deep_memory 试点 · 步骤1:提取+分块(compass 框)
从 1336 jsonl 提取真实对话文本,打会话等级标,512-token 级分块,输出 blocks.jsonl
判据: PREREG_DEEP_MEMORY_PILOT_20261023.md
"""
import json, glob, os, re, hashlib, sys

P = os.path.expanduser('~/.claude/projects/-Users-chunxiao-wang-Projects-nautilus-compass')
OUT = os.path.join(os.path.dirname(__file__), 'blocks_compass.jsonl')
CHUNK_CHARS = 1200        # ≈512 token(中英混合)
OVERLAP = 120
MIN_BLOCK = 60            # 太短的块丢弃

def session_text(path):
    """解析单会话 → (真实用户消息数, [ (role, text, ts) ])"""
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
                if isinstance(c, str):
                    txt = c
                elif isinstance(c, list):
                    parts = []
                    for item in c:
                        if isinstance(item, dict) and item.get('type') == 'text':
                            parts.append(item.get('text', ''))
                    txt = '\n'.join(parts)
                else:
                    continue
                txt = txt.strip()
                if not txt: continue
                # 跳过噪音
                if txt.startswith('<') or txt.startswith('Caveat:'): continue
                if 'tool_result' in txt[:40] or txt.startswith('{'): continue
                if t == 'user':
                    # 蒸馏 worker/系统注入识别
                    head = txt[:60]
                    if '蒸馏器' in head or 'independent grader' in head.lower() and len(txt) > 4000:
                        continue
                    user_real += 1
                msgs.append((t, txt, ts))
    except Exception:
        return 0, []
    return user_real, msgs

def grade_of(sz, user_real):
    if sz > 30_000 and user_real >= 1: return 'high'   # 正史
    if sz > 8_000: return 'mid'                        # 有内容的值守/测试
    return 'low'                                       # 碎片

def main():
    files = sorted(glob.glob(f'{P}/*.jsonl'))
    n_blocks, seen = 0, set()
    stats = {'high': 0, 'mid': 0, 'low': 0, 'sessions': 0}
    with open(OUT, 'w', encoding='utf-8') as out:
        for f in files:
            sz = os.path.getsize(f)
            user_real, msgs = session_text(f)
            if not msgs: continue
            stats['sessions'] += 1
            g = grade_of(sz, user_real)
            stats[g] += 1
            sid = os.path.basename(f)[:8]
            # 会话拼接后滑窗分块
            buf, start_ts = [], None
            def flush():
                nonlocal n_blocks
                text = '\n'.join(buf).strip()
                if len(text) < MIN_BLOCK: return
                h = hashlib.md5(text.encode()).hexdigest()
                if h in seen: return
                seen.add(h)
                # 滑窗
                i = 0
                while i < len(text):
                    chunk = text[i:i+CHUNK_CHARS]
                    if len(chunk) >= MIN_BLOCK:
                        ch = hashlib.md5(chunk.encode()).hexdigest()
                        if ch not in seen:
                            seen.add(ch)
                            out.write(json.dumps({'id': ch, 'sid': sid, 'grade': g,
                                                  'ts': start_ts or '', 'text': chunk},
                                                 ensure_ascii=False) + '\n')
                            n_blocks += 1
                    i += CHUNK_CHARS - OVERLAP
            for t, txt, ts in msgs:
                if start_ts is None and ts: start_ts = ts
                buf.append(f'[{ "用户" if t=="user" else "助手" }] {txt}')
                if sum(len(x) for x in buf) > CHUNK_CHARS * 2:
                    flush(); buf = [buf[-1]] if len(buf) > 1 else []
            flush()
    print(f"会话 {stats['sessions']} | blocks {n_blocks} | 等级分布 {stats}")

if __name__ == '__main__':
    main()
