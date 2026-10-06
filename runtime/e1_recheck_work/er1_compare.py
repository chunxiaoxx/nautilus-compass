#!/usr/bin/env python3
"""ER1 比对器:复考 CSV vs 交卷正本,按 id 五维逐项比对,翻转明细+一致率。
用法: python er1_compare.py <recheck_main.csv> <recheck_ood.csv>
正本: runtime/e1_judge_pack/goldpack_main_J2.csv(主包交卷)+ runtime/e1_judge_pack/goldpack_J2.csv(OOD 交卷)"""
import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent
DIMS = ["dim1", "dim2", "dim3", "pos", "neg"]
GOLD = {"main": HERE.parent / "e1_judge_pack" / "goldpack_main_J2.csv",
        "ood": HERE.parent / "e1_judge_pack" / "goldpack_J2.csv"}


def load_csv(p: Path):
    rows = {}
    with open(p, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows[r["id"]] = r
    return rows


def main() -> int:
    rc_main, rc_ood = sys.argv[1], sys.argv[2]
    for tag, rc_path in (("main", rc_main), ("ood", rc_ood)):
        rc, first = load_csv(Path(rc_path)), load_csv(GOLD[tag])
        common = set(rc) & set(first)
        flips, dim_dist = [], {}
        for iid in sorted(common):
            for d in DIMS:
                if rc[iid][d] != first[iid][d]:
                    flips.append((iid, d, first[iid][d], rc[iid][d]))
                    dim_dist[d] = dim_dist.get(d, 0) + 1
        n = len(common)
        cell_total = n * len(DIMS)
        agree_rate = 1 - len(flips) / cell_total
        print(f"== {tag}: n={n} 逐项单元={cell_total} 翻转={len(flips)} 五维逐项一致率={agree_rate:.4f}")
        print("   按维分布:", dim_dist)
        # 题级翻转(至少一维变的题数)
        q_flipped = len({f[0] for f in flips})
        print(f"   题级翻转(≥1维): {q_flipped}/{n} = {q_flipped/n:.2%}(ER3 门:一致率 ≥97% 即题级翻转 ≤{int(n*0.03)} 题口径近似)")
        for f in flips[:15]:
            print("   flip:", f)
        if len(flips) > 15:
            print(f"   ...共 {len(flips)} 条")
    print("\nER1 语义:每例翻转须归因(greedy 预期零/近零;非确定 kernel 库版本差异=可归因类)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
