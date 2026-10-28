"""中心环 Q3 监控:V5 ALE records → A 类燃料率 → 对照首证阈值(2026-06-22)。

北极星 forcing function 的下一个可能溶解点 = **A 类率未知**。qwen3.7-max(strong)
与 doubao 都是强模型,ALE 连续打分下 strong 未必领先 doubao ≥margin → A 类率可能
低 → 40 题一批产不出 distill_train 要的 min_n=20 条 → 蒸馏首证缺燃料。

用法:V5 records 落盘后立刻跑(别乐观假设燃料够):
    python scripts/fuel_rate_report.py --records /path/ale_fuel_records.jsonl
exit 0 = 够首证(a≥min_n) · exit 2 = 不够(扩题/调margin/换producer·别先装训练env)。

复用 services.distill_mint_runner.ingest_fuel_records(已测·不重写分拣口径)。
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.distill_mint_runner import fuel_rate  # noqa: E402


def read_jsonl(path: str) -> list[dict]:
    """读 V5 6-key records jsonl(不去重·records 非 sample·无 meta.task_id)。"""
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln:
                rows.append(json.loads(ln))
    return rows


def format_report(r: dict) -> str:
    verdict = (f"[ENOUGH] 够首证 (A={r['a_bucket']} >= min_n={r['min_n']})"
               if r["enough_for_poc"] else
               f"[SHORT] 不够首证 (A={r['a_bucket']} / min_n={r['min_n']}) "
               f"-> 扩题池 / 调 margin / 换 producer · 别先装训练 env")
    lines = [
        f"records 总数 : {r['total']}",
        f"A 类(燃料) : {r['a_bucket']}  ({r['a_rate']:.0%})",
        f"饱和拒      : {r['rejected']}",
        f"B 类(强未解): {r['b_bucket']}",
        f"errored     : {r['errored']}",
        f"判定        : {verdict}",
    ]
    if r["a_task_ids"]:
        lines.append(f"A 类 task_id: {', '.join(r['a_task_ids'][:30])}")
    return "\n".join(lines)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ALE 燃料 A 类率监控(中心环 Q3)")
    ap.add_argument("--records", required=True, help="V5 6-key records jsonl 路径")
    ap.add_argument("--kind", default="ale", choices=["ale", "swe"])
    ap.add_argument("--margin", type=float, default=0.2, help="ALE 相对 gap 门")
    ap.add_argument("--min-n", type=int, default=20, help="首证阈值(distill_train)")
    a = ap.parse_args(argv)
    if not os.path.exists(a.records):
        print(f"[fuel-rate] records 不存在: {a.records}")
        return 1
    r = fuel_rate(read_jsonl(a.records), kind=a.kind, margin=a.margin, min_n=a.min_n)
    print(format_report(r))
    return 0 if r["enough_for_poc"] else 2


if __name__ == "__main__":
    sys.exit(main())
