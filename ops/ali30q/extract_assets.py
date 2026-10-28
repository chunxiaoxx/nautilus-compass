#!/usr/bin/env python3
"""从 _s5 判分结果自动提取真实答卷片段 → tests/assets/(甲方 §2.6 model_failure_modes)
用法: python3 extract_assets.py [items_root]
"""
import json, shutil, sys
from pathlib import Path

I = Path(sys.argv[1] if len(sys.argv) > 1 else 
         '/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items')
OUT_LOG = []

for d in sorted(I.glob('CS-*')):
    if not d.is_dir(): continue
    iid = d.name
    s5 = d/'_s5'
    if not s5.exists(): continue
    
    # 建目录
    assets = d/'tests'/'assets'
    assets.mkdir(parents=True, exist_ok=True)
    
    # 从所有 result.json 提取有 score 的答卷片段
    n = 0
    for rf in sorted(s5.glob('*_run[0-3]_result.json')):
        try:
            r = json.load(open(rf))
        except: continue
        if r.get('score') is None: continue  # 只要有分就算
        model = r.get('model', 'unknown')
        run = r.get('run', 0)
        raw = r.get('raw_head', '')
        if not raw: continue
        # 写真实答卷片段
        out = assets / f'{model}_run{run}_answer.json'
        json.dump({'model': model, 'run': run, 'raw': raw, 'source': str(rf)},
                  open(out, 'w'), ensure_ascii=False, indent=1)
        n += 1
    
    # 也从 ut_results.json 提取判分明细
    jf = d/'_judge'/'ut_results.json'
    if jf.exists():
        try:
            j = json.load(open(jf))
            shutil.copy2(jf, assets/'ut_results.json')
        except: pass
    
    # 从 tests/ 复制现有测试文件作为题目上下文证据
    # 不拷 test 文件(防 pytest 重跑冲突)
    
    if n > 0:
        OUT_LOG.append(f'✅ {iid}: {n} 答卷片段 → tests/assets/')
    else:
        OUT_LOG.append(f'🟡 {iid}: 无有效答卷可提取')

for l in OUT_LOG: print(l)
print(f'\n总计: {sum(1 for l in OUT_LOG if l.startswith("✅"))} 题补齐 assets')
