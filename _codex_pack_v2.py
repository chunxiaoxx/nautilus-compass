import tarfile, time, hashlib, json, sys
from pathlib import Path

src = Path(r'C:/Users/chunx/.codex/sessions')
out = Path(r'C:/Users/chunx/nas-outbox/nautilus-migration/04_codex/sessions_codex_full_v2.tar.gz')
out.parent.mkdir(parents=True, exist_ok=True)
tmp = out.with_suffix('.partial')

def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

# 阶段1: 数源文件(先拿到期望值,校验才有锚)
expected = [f for f in sorted(src.rglob('*')) if f.is_file()]
print(f'[stage1] source files = {len(expected)}', flush=True)
if not expected:
    print('[ABORT] empty source'); sys.exit(1)

# 阶段2: 流式打包(低压缩防内存压力;分块落盘)
t0 = time.time()
n = 0
with tarfile.open(tmp, 'w:gz', compresslevel=3) as tf:
    for f in expected:
        tf.add(f, arcname=str(f.relative_to(src)))
        n += 1
        if n % 100 == 0:
            print(f'[stage2] {n}/{len(expected)} files {time.time()-t0:.0f}s', flush=True)
print(f'[stage2] written {n} files', flush=True)

# 阶段3: 完成校验——重新打开数成员数,必须 == expected(上次截断假绿的根因就是缺这步)
with tarfile.open(tmp, 'r:gz') as tf:
    got = sum(1 for _ in tf)
print(f'[stage3] verified members = {got}', flush=True)
if got != len(expected):
    print(f'[ABORT] truncated: {got} != {len(expected)}'); sys.exit(2)

# 阶段4: 原子改名 + 记录元数据
tmp.replace(out)
digest = sha256(out)
meta = {"pkg": "04_codex/sessions_codex_full_v2.tar.gz", "files": got,
        "sha256": digest, "bytes": out.stat().st_size,
        "created": time.strftime('%Y-%m-%dT%H:%M:%S')}
out.with_suffix('.meta.json').write_text(json.dumps(meta, indent=1))
print('[DONE]', json.dumps(meta), flush=True)
