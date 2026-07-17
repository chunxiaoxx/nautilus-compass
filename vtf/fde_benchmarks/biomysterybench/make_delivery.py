#!/usr/bin/env python3
"""BioMysteryBench 投递打包器 · 把各题目录合并成买方格式的单一投递包。

买方格式 = 一个 problems.csv(N 行)+ data/<ID>.zip(每行一个)。
🔴 只打包 problems.csv + data/*.zip;**answer_key.json / _source_manifest.json 绝不进买方包**
(泄露答案/溯源 = 废掉 benchmark)。溯源与验证证据另写内部 DELIVERY_NOTES。

用法:
  python make_delivery.py --src _P1_out _P2_out _SEQ_out --out _DELIVERY
  python bmb_validator.py _DELIVERY/problems.csv --data-dir _DELIVERY/data   # 复验买方门
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path

REQUIRED_COLS = ("id", "question", "answer_rubric", "allowed_domains", "human_solvable")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", nargs="+", type=Path, required=True, help="各题产出目录")
    ap.add_argument("--out", type=Path, default=Path("_DELIVERY"))
    args = ap.parse_args()

    # 只清生成物(data/*.zip),保留同目录的 DELIVERY_NOTES.md / 网页等手写交付件
    (args.out / "data").mkdir(parents=True, exist_ok=True)
    for old in (args.out / "data").glob("*.zip"):
        old.unlink()

    rows, provenance = [], []
    for src in args.src:
        csv_path = src / "problems.csv"
        if not csv_path.exists():
            print(f"  ! 跳过 {src}(无 problems.csv)")
            continue
        with open(csv_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                rid = row["id"].strip()
                zip_src = src / "data" / f"{rid}.zip"
                if not zip_src.exists():
                    print(f"  ! {rid} 缺 data/{rid}.zip,跳过")
                    continue
                shutil.copy2(zip_src, args.out / "data" / f"{rid}.zip")
                rows.append(row)
                # 内部溯源(不进买方包)
                ak = src / "answer_key.json"
                prov = {"id": rid, "src": str(src)}
                if ak.exists():
                    prov["answer_key"] = json.loads(ak.read_text(encoding="utf-8"))
                provenance.append(prov)
                print(f"  ✓ {rid}  ({zip_src.stat().st_size} B)")

    # 买方 problems.csv(合并)
    with open(args.out / "problems.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REQUIRED_COLS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in REQUIRED_COLS})

    # 内部溯源(单独文件,提醒不投递)
    (args.out / "_INTERNAL_provenance.json").write_text(
        json.dumps({"note": "内部溯源+答案,勿投递买方", "problems": provenance},
                   ensure_ascii=False, indent=2), encoding="utf-8")

    # 断言买方包不含任何答案键文件
    leak = list(args.out.rglob("answer_key.json")) + list(args.out.rglob("_source_manifest.json"))
    assert not leak, f"🔴 买方包混入答案/溯源文件:{leak}"

    print(f"\n✅ 投递包:{len(rows)} 题 → {args.out}/")
    print(f"   买方投递 = problems.csv + data/*.zip(勿含 _INTERNAL_*)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
