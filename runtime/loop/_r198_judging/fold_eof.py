#!/usr/bin/env python3
"""EOF 补跑终态折入:把 sphinx-8475/sympy-13974 的补跑终态覆写进本地 rest report 副本
(首次运行自动备份 *.orig 留痕),配合 round1_merge.py 的 mirror_eof_final.txt 覆盖文件
(补跑后仍归环境层的题集;其余补跑 error 计 patch 格式层)。
用法: python fold_eof.py   # 只折状态;环境层名单写 mirror_eof_final.txt(一行一题,空文件=全格式)"""
import json
from pathlib import Path

HERE = Path(__file__).parent
EOF = {"A": HERE / "a_eof_report.json", "B": HERE / "b_eof_report.json"}
REST = {"A": HERE / "rest_report_a.json", "B": HERE / "b_rest_report_b.json"}
KEYS = ("resolved_ids", "unresolved_ids", "error_ids", "empty_patch_ids")
TARGET = {"sympy__sympy-13974", "sphinx-doc__sphinx-8475"}

for arm in "AB":
    ef = json.loads(EOF[arm].read_text(encoding="utf-8"))
    rp = REST[arm]
    if not (HERE / f"{rp.stem}.orig").exists():
        (HERE / f"{rp.stem}.orig").write_text(rp.read_text(encoding="utf-8"), encoding="utf-8")
        print(f"{arm}: 备份 {rp.stem}.orig")
    rf = json.loads(rp.read_text(encoding="utf-8"))
    for k in KEYS:
        rf[k] = [i for i in rf.get(k, []) if i not in TARGET]
    for k in KEYS:
        for iid in ef.get(k, []):
            if iid in TARGET:
                rf[k].append(iid)
    # 提交数修正:折入后 submitted 不变(30);completed 计数键保持原样由 merge 重算
    rp.write_text(json.dumps(rf, ensure_ascii=False, indent=1), encoding="utf-8")
    moved = {k: [i for i in ef.get(k, []) if i in TARGET] for k in KEYS}
    print(f"{arm}: folded {moved}")
print("done — 环境层名单写 mirror_eof_final.txt 后跑 round1_merge.py")
