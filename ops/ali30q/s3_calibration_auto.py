#!/usr/bin/env python3
"""S3 四门标定自动化(compass 2026-10-25)——杠杆2
输入: solution/(金标)+ _s3_variants/(deficient/guessed 变体)
自动: 变体逐一跑 UT → 坑版/变体/金标三态分数矩阵 → 四门标定素材 CSV
人工只复核自动标定结果,不逐门手跑。
用法: python3 s3_calibration_auto.py items/CS-NNN
"""
import json, subprocess, sys
from pathlib import Path

def run_pytest(item_dir, py):
    r = subprocess.run([py, '-m', 'pytest', 'tests/', '-q', '--junitxml=/tmp/cal.xml'],
                       cwd=item_dir, capture_output=True, text=True, timeout=1200)
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse('/tmp/cal.xml').getroot()
        return {'passrate': float(root.attrib.get('passrate', 0)), 'score': round(1 - float(root.attrib.get('failures', 0))/max(int(root.attrib.get('tests',1)),1), 3)}
    except Exception:
        return {'passrate': 0.0, 'score': 0.0}

def main(item_path):
    item = Path(item_path)
    judge_py = item.parent.parent/'.venv-judge/bin/python'
    out = {'item': item.name, 'gates': {}}
    # 坑版(交付态)必须挂
    bug = run_pytest(item, str(judge_py))
    out['gates']['bug_version'] = bug
    # 金标必须全过(判读层红线:GOLD-PASS 才有效)
    sol_dir = item/'solution'
    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(item/'environment/workspace/repo', tmp/'repo', dirs_exist_ok=True)
    for f in sol_dir.rglob('*.py'):
        rel = f.relative_to(sol_dir)
        (tmp/'repo'/rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, tmp/'repo'/rel)
    shutil.copy(item/'pytest.ini', tmp/'pytest.ini') if (item/'pytest.ini').exists() else None
    gold = run_pytest(tmp, str(judge_py))
    out['gates']['golden'] = gold
    # 变体标定素材
    var_dir = item/'_s3_variants'
    variants = {}
    if var_dir.exists():
        for vf in sorted(var_dir.glob('*.py')):
            if vf.name.startswith('__'): continue
            tdir = tmp/'repo'
            shutil.copy2(vf, tdir/ (vf.parent.relative_to(sol_dir.parent) if False else vf.name.replace('_v1','')))
            vr = run_pytest_item_tmp(tdir, judge_py)
            variants[vf.stem] = vr
    out['variants'] = variants
    out_path = item/'_judge'/'s3_calibration.json'
    out_path.parent.mkdir(exist_ok=True)
    json.dump(out, open(out_path, 'w'), ensure_ascii=False, indent=1)
    print(f'✅ 标定素材 {out_path}')

def run_pytest_item_tmp(tdir, py):
    r = subprocess.run([py, '-m', 'pytest', str(tdir), '-q'], capture_output=True, text=True, timeout=600)
    for line in r.stdout.splitlines():
        if 'passed' in line or 'failed' in line: return {'raw': line.strip()}
    return {'raw': r.stdout[-80:]}

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
