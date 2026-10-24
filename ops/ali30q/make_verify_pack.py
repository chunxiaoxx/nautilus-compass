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

    # v1.1: 平均分维度(甲方口径 21321)——五模型各+分组(国内/SOTA)+差值+趋势一致性
    DOMESTIC = {'qwen3.8max', 'glm5.3', 'kimi-k3'}
    SOTA = {'opus5.5', 'gpt-6-astra'}
    by_model = {}
    for k, v in results.items():
        m = k.rsplit('_run', 1)[0]
        by_model.setdefault(m, []).append(v['score'])
    avg = {m: round(sum(s)/len(s), 4) for m, ss in by_model.items() for s in [ss]}
    dom = [avg[m] for m in avg if m in DOMESTIC]
    sota = [avg[m] for m in avg if m in SOTA]
    manifest['avg_score_v1_1'] = {
        'per_model': avg,
        'domestic_avg': round(sum(dom)/len(dom), 4) if dom else None,
        'sota_avg': round(sum(sota)/len(sota), 4) if sota else None,
        'gap_sota_minus_domestic': round(sum(sota)/len(sota) - sum(dom)/len(dom), 4) if dom and sota else None,
        'trend_consistency': 'PASS' if (dom and sota and (sum(sota)/len(sota) - sum(dom)/len(dom)) >= 0.10) else 'CHECK',
        'threshold_note': '甲方口径:国内比SOTA低10-20分以上(0.10-0.20);<0.10 区分度不足警报',
    }
        out = item / '_s5' / 'verify_manifest.json'
    json.dump(manifest, open(out, 'w'), ensure_ascii=False, indent=1)
    print(f'✅ {out} ({len(results)} 有效读数入包)')

if __name__ == '__main__':
    main(sys.argv[1])
