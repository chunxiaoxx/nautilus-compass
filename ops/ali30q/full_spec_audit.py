#!/usr/bin/env python3
"""甲方 1012 完整规格逐题审计(A-F 六节 40+ 条目)——判据验证持续工作"""
import os, re, json, sys
from pathlib import Path

I = Path('/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items')
ITEMS = sorted(I.glob('CS-*'))

def audit_item(d):
    iid = d.name
    tom = d/'task.toml'
    c = tom.read_text(encoding='utf-8') if tom.exists() else ''
    inst = d/'instruction.md'
    ic = inst.read_text(errors='replace') if inst.exists() else ''
    
    # 五件套
    parts = sum(1 for s in ['task.toml','instruction.md','tests','solution','environment'] if (d/s).exists())
    
    # UT
    ut_files = list(d.glob('tests/test_*.py'))
    ut = sum(len(re.findall(r'def test_', tf.read_text(errors='replace'))) for tf in ut_files)
    
    # 知识树
    kp = 'knowledge_path' in c
    
    # 三对号
    bp = bool(re.search(r'D0[1589]\.\d', c))
    
    # conftest
    cf = (d/'conftest.py').exists()
    
    # 内嵌挑战
    ch = bool(re.search(r'结论|草稿|前提|reviewer', ic[:2000]))
    
    # 泄题
    leak_words = ['golden','exploit','badpattern','陷阱名','正确答案','参考答案']
    no_leak = not any(w in ic.lower() for w in leak_words)
    
    # 反例程序
    ce = any(d.glob('counterexamples/*.py')) or any(d.glob('environment/workspace/repo/counterexamples/*.py'))
    
    # focus_points
    fp = 'focus_points' in c
    
    # code_origin + license
    co = 'code_origin' in c
    
    # score.py(甲方要求判分入口)
    score = (d/'tests'/'score.py').exists()
    
    # calibration/四件套
    cal = (d/'tests'/'calibration').exists()
    
    # 七考察点(固定③⑤+选1-3)
    fp7 = 'focus_points' in c and ('反幻觉' in c or '③' in c)
    
    # tests/assets/ 真实答卷
    assets = (d/'tests'/'assets').exists() and any((d/'tests'/'assets').iterdir())
    
    # 五模型读数
    models = set()
    if (d/'_s5').exists():
        for f in (d/'_s5').glob('*_run[0-3]_result.json'):
            try:
                r = json.load(open(f))
                if r.get('score') is not None: models.add(r['model'])
            except: pass
    m5 = len(models) >= 5
    
    # 金标自检
    jf = d/'_judge'/'ut_results.json'
    gold = False
    if jf.exists():
        try:
            j = json.load(open(jf))
            gold = j.get('score') == 1.0
        except: pass
    
    score = sum([parts==5, ut>=21, kp, bp, cf, ch, no_leak, ce, fp, co, score, cal, fp7, assets, m5, gold])
    return {
        'item': iid, 'score': score, 'max': 16,
        'five': parts==5, 'ut': ut, 'ut_ok': ut>=21, 'kp': kp, 'bp': bp, 'cf': cf,
        'ch': ch, 'no_leak': no_leak, 'ce': ce, 'fp': fp, 'co': co,
        'score_py': score, 'cal': cal, 'fp7': fp7, 'assets': assets,
        'm5': m5, 'gold': gold,
        'models': sorted(models)
    }

# 审计全部
all_results = []
for d in ITEMS:
    if not d.is_dir(): continue
    r = audit_item(d)
    all_results.append(r)

# 排序
all_results.sort(key=lambda x: -x['score'])

print(f'{"题":8} {"分数":>4} {"五件":>4} {"UT":>4} {"知识":>4} {"标签":>4} {"conf":>4} {"挑战":>4} {"不泄":>4} {"反例":>4} {"FP":>3} {"CO":>3} {"score":>5} {"校准":>4} {"FP7":>3} {"assets":>6} {"5模":>4} {"金标":>4}')
print('-' * 110)
for r in all_results:
    marks = {k: ('✓' if v else '✗') for k, v in r.items() if isinstance(v, bool)}
    print(f'{r["item"]:8} {r["score"]:>4} '
          f'{"✓" if r["five"] else "✗":>4} '
          f'{r["ut"]:>4} '
          f'{"✓" if r["ut_ok"] else "✗":>4} '
          f'{"✓" if r["kp"] else "✗":>4} '
          f'{"✓" if r["bp"] else "✗":>4} '
          f'{"✓" if r["cf"] else "✗":>4} '
          f'{"✓" if r["ch"] else "✗":>4} '
          f'{"✓" if r["no_leak"] else "✗":>4} '
          f'{"✓" if r["ce"] else "✗":>4} '
          f'{"✓" if r["fp"] else "✗":>3} '
          f'{"✓" if r["co"] else "✗":>3} '
          f'{"✓" if r["score_py"] else "✗":>5} '
          f'{"✓" if r["cal"] else "✗":>4} '
          f'{"✓" if r["fp7"] else "✗":>3} '
          f'{"✓" if r["assets"] else "✗":>6} '
          f'{r["m5"]:>4} '
          f'{"✅" if r["gold"] else "—":>4}')

# 分级统计
tiers = {'full': [], 'near': [], 'part': [], 'low': []}
for r in all_results:
    s = r['score']
    if s >= 14: tiers['full'].append(r)
    elif s >= 10: tiers['near'].append(r)
    elif s >= 6: tiers['part'].append(r)
    else: tiers['low'].append(r)

print(f'\n═══ 分级统计 ═══')
print(f'高质量(≥14/16): {len(tiers["full"])} 题')
print(f'中质量(10-13): {len(tiers["near"])} 题')
print(f'低质量(6-9): {len(tiers["part"])} 题')
print(f'不合格(<6): {len(tiers["low"])} 题')

json.dump(all_results, open('/Users/chunxiao.wang/Projects/nautilus-compass/ops/ali30q/full_spec_audit.json', 'w'), ensure_ascii=False, indent=1)
print('✅ 审计结果落盘 ops/ali30q/full_spec_audit.json')
