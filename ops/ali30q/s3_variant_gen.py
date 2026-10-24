#!/usr/bin/env python3
"""阿里30题·S3 校准四门变体生成器(v1 · compass 2026-10-24)
规格:21220/21179——deficient(删修复一半)/guessed(接口乱改)两类变异
用法: s3_variant_gen.py <solution.py> [--out dir]  → deficient_X.py / guessed_X.py + diff 清单
每题 S2 完工即跑,四门标定素材分钟级量产。
"""
import argparse, difflib, ast, re
from pathlib import Path

def parse_blocks(src):
    """按顶层函数/方法切块(变异操作的最小单元)"""
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    blocks = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            blocks.append((node.name, node.lineno, node.end_lineno))
    return lines, blocks

def deficient_variant(lines, blocks, keep_ratio=0.5):
    """删修复一半:保留前 keep_ratio 的修复块,删除其余(典型:只修释放不修引用环/反之)"""
    tgt = [b for b in blocks if len(blocks) > 1]
    n_del = max(1, int(len(tgt) * (1 - keep_ratio)))
    del_set = {b[0] for b in tgt[len(tgt)-n_del:]}  # 删靠后的块(常是补丁的第二半)
    out, skipping = [], False
    for i, l in enumerate(lines, 1):
        if any(b[1] == i for b in tgt if b[0] in del_set):
            skipping = True; out.append(l.split('(')[0] + '(…)pass  # deficient: 删修复一半\n'); continue
        if skipping and l.strip() and not l.startswith((' ', '\t', ')')):
            skipping = False
        if not skipping:
            out.append(l)
    return ''.join(out), list(del_set)

def guessed_variant(src):
    """接口乱改:常见误修模式——try/except 吞掉该传播的异常 / 置 None 变 del / 修复调用点却留旧引用"""
    v = src
    subs = [
        # guessed-1: 以为要显式置空,实制造新引用
        (r'del (\w+)', r'\1 = None  # guessed: del→置None(留引用)'),
        # guessed-2: 加 try 兜底吞异常(改变语义)
        (r'(\n(\s+)raise\b)', r'\1\2try: pass\n\2except Exception: pass  # guessed: 吞异常'),
        # guessed-3: gc.collect 洒地式调用(误判根因)
        (r'(\n(\s+)def __del__)', r'\n\2import gc as _gc\1'),
    ]
    applied = []
    for pat, rep in subs:
        new = re.sub(pat, rep, v, count=1)
        if new != v:
            v = new; applied.append(pat[:30])
    return v, applied

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('solution')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    src = Path(a.solution).read_text(encoding='utf-8')
    outdir = Path(a.out or Path(a.solution).parent / '_s3_variants')
    outdir.mkdir(exist_ok=True)
    lines, blocks = parse_blocks(src)
    dv, deld = deficient_variant(lines, blocks)
    gv, gsubs = guessed_variant(src)
    (outdir / 'deficient_v1.py').write_text(dv, encoding='utf-8')
    (outdir / 'guessed_v1.py').write_text(gv, encoding='utf-8')
    diff_d = ''.join(difflib.unified_diff(src.splitlines(True), dv.splitlines(True), 'solution', 'deficient'))
    diff_g = ''.join(difflib.unified_diff(src.splitlines(True), gv.splitlines(True), 'solution', 'guessed'))
    (outdir / 'diffs.md').write_text('# S3 变体审计痕\n## deficient 删除块: ' + ', '.join(deld) + '\n```\n' + diff_d + '\n```\n## guessed 应用模式: ' + ', '.join(gsubs) + '\n```\n' + diff_g + '\n```\n', encoding='utf-8')
    print(f'✅ {outdir}/deficient_v1.py + guessed_v1.py + diffs.md(审计痕)')

if __name__ == '__main__':
    main()
