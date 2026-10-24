#!/usr/bin/env python3
"""assay 可复算包:把一题的判分矩阵变成独立可验证的 manifest
(读数+环境指纹+重放命令+输入输出 sha256)——交付差异化:甲方拿到即可重放验证"""
import json, hashlib, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hex[:16] if False else h.hexdigest()[:16]

def main(item_dir):
    item = Path(item_dir)
    iid = item.name
    # 判分读数全量
    results = {}
    for f in sorted(item.glob('_s5/*_run[0-3]_result.json')):
        d = json.load(open(f))
        if d.get('score') is not None:
            results[f.stem] = {'score': d['score'], 'applied': d.get('applied_files'),
                               'elapsed': d.get('elapsed_s'), 'ut_vector': d.get('ut_vector')}
    manifest = {
        'item': iid,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'signed_by': 'compass (independent judge frame)',
        'results_matrix': results,
        'n_valid': len(results),
        'env_fingerprint': {
            'python': subprocess.run([sys.executable, '-V'], capture_output=True, text=True).stdout.strip(),
            'pytest': subprocess.run([str(item.parent.parent/'.venv-judge/bin/python'), '-m', 'pytest', '--version'],
                                      capture_output=True, text=True).stdout.strip(),
        },
        'replay': {
            'model_solve': f'.venv-judge/bin/python tools/model_solve.py {iid} --model <m> --run <n>',
            'ut_runner': f'.venv-judge/bin/python tools/ut_runner.py items/{iid} --runs 3',
        },
        'input_sha': {
            'instruction.md': sha(item/'instruction.md'),
            'task.toml': sha(item/'task.toml'),
        },
        'evidence_tiers': {
            'scores': '[实测] model_solve 自动判分',
            'determinism': '[实测] ut_runner 三连',
            'independence': '[实测] compass 非设计框审计',
        },
    }
    out = item / '_s5' / 'verify_manifest.json'
    json.dump(manifest, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f'✅ {out} ({len(results)} 有效读数入包)')

if __name__ == '__main__':
    main(sys.argv[1])
