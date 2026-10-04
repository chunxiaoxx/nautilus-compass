#!/usr/bin/env python3
"""calib60 汇总:人类标定 vs 判官读数一致率+Cohen's κ+分歧归因清单。

输入:作答表填毕的 ANSWER_SHEET_filled.md(或 CSV)+ sample_manifest.json(判官读数区)。
门槛(预备档建议,组织方裁):一致率>=80%(κ>=0.6)→判官读数获人类标定背书;
<80%→分歧题逐题归因(判据二义/判官错/材料歧义三类)报告先出再议。
用法:python tools/e1_calib60_kappa.py <filled_sheet.csv>
"""
import csv
import json
import sys
from collections import Counter
from pathlib import Path

BASE = Path("runtime/e1_judge_pack/calib60")


def kappa(a, b):
    """Cohen's κ(两 rater,类别取并集)。"""
    n = len(a)
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    cats = set(a) | set(b)
    pe = sum(Counter(a)[c] * Counter(b)[c] for c in cats) / n / n
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, po


def main(path):
    manifest = json.loads((BASE / "sample_manifest.json").read_text(encoding="utf-8"))
    # 判官读数区从 manifest rows 的判官读数区字段还原
    judge = {}
    for r in manifest["rows"]:
        blob = r["判官读数区_汇总期填"]
        judge[str(r["q"])] = (blob.split("3B_dim2=")[1].split()[0],
                              blob.split("7B_dim2=")[1].split()[0])
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 60:
        print(f"[warn] 作答行数 {len(rows)} != 60")

    dims = {"dim1": "完成度", "dim2": "执行质量", "dim3": "置信", "pos": "正问", "neg": "反问"}
    out = {"n": len(rows)}
    for k, zh in dims.items():
        human = [r[zh].strip() for r in rows]
        for who in ("3B", "7B"):
            if k == "dim2":
                ai = [judge[str(r["q"])][0 if who == "3B" else 1] for r in rows]
                kp, po = kappa(human, ai)
                out[f"{k}_vs_{who}"] = {"agree": po, "kappa": round(kp, 4)}
    print(json.dumps(out, ensure_ascii=False, indent=1))

    # 分歧题清单(dim2 对 7B,标定主对象)
    disagree = [r["q"] for r in rows
                if r["执行质量"].strip() != judge[str(r["q"])][1]]
    print(f"[dim2_vs_7B 分歧题 {len(disagree)}]:", disagree)
    print("[next] 分歧题逐题归因三类(判据二义/判官错/材料歧义),归因报告先出再议")


if __name__ == "__main__":
    main(sys.argv[1])
