#!/usr/bin/env python3
"""出厂门自动检查(13 门 V1 checklist)——每题出包前必跑
判据: 21367 验收标准总表 V1
用法: python3 factory_gate.py items/CS-NNN → PASS/FAIL + 逐门读数
"""
import json, sys, subprocess
from pathlib import Path

def main(item_dir):
    item = Path(item_dir)
    iid = item.name
    gates = []

    # G1 金标自检(solution 必须 UT 全过)
    r = subprocess.run(['/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/.venv-judge/bin/python', '/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/tools/gold_check.py', str(item)],
                       capture_output=True, text=True)
    gold_pass = 'GOLD-PASS' in (r.stdout + r.stderr)
    gates.append(('G1 金标自检', 'PASS' if gold_pass else 'FAIL', 'solution 必须 UT 全过'))

    # G2 坑版必须挂(2026-10-27 复算实装:CS-507 坑版=金标同 hash 满分漏网)
    # 在隔离副本跑 workspace 原样,不写原 item;score<1.0 才有区分度
    import shutil, tempfile
    try:
        with tempfile.TemporaryDirectory() as td:
            ws_copy = Path(td) / item.name
            ws_copy.mkdir()
            for part in ['tests', 'environment', 'solution', 'conftest.py',
                         'pytest.ini', 'task.toml', 'instruction.md']:
                src = item / part
                if src.exists():
                    (shutil.copytree if src.is_dir() else shutil.copy2)(src, ws_copy / part)
            r2 = subprocess.run(['/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/.venv-judge/bin/python',
                                 '/Users/chunxiao.wang/Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/tools/ut_runner.py',
                                 str(ws_copy), '--runs', '3'],
                                capture_output=True, text=True, timeout=1200)
            bug = json.load(open(ws_copy / '_judge' / 'ut_results.json'))
            bs = bug.get('score')
            gates.append(('G2 坑版必须挂', 'PASS' if bs is not None and bs < 1.0 else 'FAIL',
                          f'坑版态 score={bs}(=1.0 即零区分度·题目无效)'))
    except Exception as e:
        gates.append(('G2 坑版必须挂', 'UNVERIFIED', str(e)[:80]))
    # G3 五模型读数齐
    s5 = item/'_s5'
    models = {'qwen3.8max': 0, 'glm5.3': 0, 'kimi-k3': 0, 'opus5.5': 0, 'gpt-6-astra': 0}
    if s5.exists():
        for f in s5.glob('*_run[0-3]_result.json'):
            d = json.load(open(f))
            m = d.get('model', '')
            if d.get('score') is not None and m in models:
                models[m] += 1
    models_ok = all(v >= 4 for v in models.values())
    gates.append(('G3 五模型×4轮', 'PASS' if models_ok else f'FAIL({min(models.values())}/4)',
                  f'{ {k: v for k, v in models.items()} }'))

    # G4 UT≥21
    test_n = len(list(item.glob('tests/test_*.py')))
    import re
    total_fn = 0
    for tf in item.glob('tests/test_*.py'):
        total_fn += len(re.findall(r'def test_', tf.read_text(encoding='utf-8')))
    gates.append(('G4 UT≥21', 'PASS' if total_fn >= 21 else f'FAIL({total_fn})', f'{total_fn} 个 test 函数'))

    # G5 区分度差值
    dom_s = []; sota_s = []
    DOM = {'qwen3.8max', 'glm5.3', 'kimi-k3'}; SOTA = {'opus5.5', 'gpt-6-astra'}
    for m, cnt in models.items():
        scores = []
        for r in range(4):
            p = s5/f'{m}_run{r}_result.json'
            if p.exists():
                d = json.load(open(p))
                if d.get('score') is not None: scores.append(d['score'])
        if scores:
            avg = sum(scores)/len(scores)
            (dom_s if m in DOM else sota_s).append(avg)
    if dom_s and sota_s:
        da, sa = sum(dom_s)/len(dom_s), sum(sota_s)/len(sota_s)
        gap = sa - da
        gates.append(('G5 区分度差值(观察列)', 'INFO',
                      f'SOTA-国内={gap:.3f};交付以 22064 G-SotaGap/G-QwenPoint 为准'))
    else:
        gates.append(('G5 区分度差值(观察列)', 'WARN(数据不全)', ''))

    # G5b/G9 资格战量化门(函 22064)
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from discrimination_jaccard import evaluate as _disc_eval
        disc = _disc_eval(item)
        gates.append(('G-QwenPoint', disc['qwen_point']['status'],
                      disc['qwen_point'].get('reason', '')))
        gates.append(('G-SotaGap', disc['sota_gap']['status'],
                      f"gap={disc['sota_gap'].get('gap')} {disc['sota_gap'].get('reason','')}"))
        gates.append(('G-Sig', disc['signature']['status'],
                      f"div={disc['signature'].get('diversity')} max={disc['signature'].get('max_share')} J={disc['signature'].get('jaccard_ratio')}"))
    except Exception as e:
        gates.append(('G-QwenPoint/G-Sig', 'UNVERIFIED', str(e)[:80]))

    # G6 双口径一致性
    gates.append(('G6 双口径一致', 'INFO', 'verify_pack v1.2 自动列'))

    # G7 泄题扫描
    inst = item/'instruction.md'
    leak = False
    if inst.exists():
        c = inst.read_text(encoding='utf-8').lower()
        for kw in ['badpattern', '陷阱', '正确答案', 'golden', 'exploit']:
            if kw in c: leak = True; break
    gates.append(('G7 泄题扫描', 'FAIL(发现泄题词)' if leak else 'PASS', ''))

    # G8 边界声明
    gates.append(('G8 边界声明', 'INFO', 'expert_design_notes.boundary 由 S2 施工声明'))

    # G10 ut_index 完整性(2026-10-27 复算:5xx 批量空 gating → 一票否决机制空转)
    try:
        import tomllib
        idx = tomllib.load(open(item / 'task.toml', 'rb'))['metadata']['ut_index']
        gating = [e['ut_name'] for e in idx if e.get('gating')]
        tests_src = '\n'.join(p.read_text(encoding='utf-8', errors='replace')
                              for p in item.glob('tests/*.py'))
        missing = [g for g in gating if g not in tests_src]
        ok = len(idx) > 0 and not missing
        gates.append(('G10 ut_index完整', 'PASS' if ok else 'FAIL',
                      f'{len(idx)}条·gating{len(gating)}条' + (f'·tests缺{missing}' if missing else '')))
    except Exception as e:
        gates.append(('G10 ut_index完整', 'FAIL', f'缺失或解析失败: {str(e)[:60]}'))

    # G11 读数时效(2026-10-27 复算:CS-511 用 10-25 旧 tests 读数报 10-27 新判据 → 过期读数)
    try:
        tests_mtime = max(p.stat().st_mtime for p in item.glob('tests/*.py'))
        stale = [p.name for p in s5.glob('qwen*_result.json')
                 if p.stat().st_mtime < tests_mtime]
        gates.append(('G11 读数时效', 'FAIL(读数早于tests改版)' if stale else 'PASS',
                      f'过期读数: {stale}' if stale else ''))
    except Exception as e:
        gates.append(('G11 读数时效', 'UNVERIFIED', str(e)[:60]))

    # G12 超档嫌疑均值口径(2026-10-27 复算:CS-507 二值化40%入带但均值0.952=统计噪声)
    qwen_scores = []
    for r in range(4):
        p = s5 / f'qwen3.8max_run{r}_result.json'
        if p.exists():
            d = json.load(open(p))
            if d.get('score') is not None:
                qwen_scores.append(d['score'])
    if qwen_scores:
        qmean = sum(qwen_scores) / len(qwen_scores)
        gates.append(('G12 qwen均值超档', 'FAIL(均值>0.85)' if qmean > 0.85 else
                      ('WARN(0.7-0.85)' if qmean > 0.7 else 'PASS'),
                      f'均值={qmean:.3f} n={len(qwen_scores)}'))
    else:
        gates.append(('G12 qwen均值超档', 'UNVERIFIED', '无 qwen 读数'))

    all_pass = all(g[1] in ('PASS', 'INFO', 'WARN') for g in gates)
    print(f'══ 出厂门 · {iid} ══')
    for g in gates: print(f'  {g[0]:16} {g[1]}')
    print(f'══ 总判定: {"PASS" if all_pass else "FAIL"} ══')
    return all_pass

if __name__ == '__main__':
    main(sys.argv[1])
