#!/usr/bin/env python3
"""30 题合规矩阵:对照 ALI_REQUIREMENTS_SPEC R4/R5/R6 机器可查项逐题打勾"""
import json, re, glob
from pathlib import Path
ITEMS = Path.home()/'Projects/nautilus-v5/.claude/worktrees/codesense-a-fix/codesense/items'
print(f'{"题":8}{"R4领域标签":12}{"R5甲方badpattern":16}{"R6判分读数":10}金标')
print('-' * 60)
for d in sorted(ITEMS.glob('CS-*')):
    tom = d/'task.toml'
    if not tom.exists(): continue
    c = tom.read_text(encoding='utf-8')
    # R5: 甲方 badpattern 痕迹(D01/D05/D08/D09 域码或 F05 机制码)
    r5 = '✓' if re.search(r'D0[1589]\.\d|F05\.\d', c) else '✗'
    r4 = r5  # 同源(域码即领域声明)
    n_s5 = len(list(d.glob('_s5/*_run[0-3]_result.json')))
    r6 = f'{n_s5}读数' if n_s5 else '✗'
    print(f'{d.name:8}{r4:12}{r5:16}{r6:10}')
