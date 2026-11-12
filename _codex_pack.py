import tarfile, time
from pathlib import Path
out = Path(r'C:/Users/chunx/nas-outbox/nautilus-migration/04_codex/sessions_codex_full.tar')
src = Path(r'C:/Users/chunx/.codex/sessions')
n = 0
with tarfile.open(out, 'w:gz', compresslevel=4) as tf:
    for f in sorted(src.rglob('*')):
        if f.is_file():
            tf.add(f, arcname=str(f.relative_to(src)))
            n += 1
            if n % 200 == 0:
                print(f'{n} files', flush=True)
print('CODEX PACK DONE', n, 'files', flush=True)
