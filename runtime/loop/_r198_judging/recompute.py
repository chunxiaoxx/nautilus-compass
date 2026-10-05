"""R198 两案统计层独立复算:UMI V4 + G1-full。
输入=本地拉取工件(runtime/loop/_r198_judging/);输出=复算读数 vs 函申报对表。
只读统计层;推理层复算(盲探针/GPU)不在本脚本。"""

import json
import statistics
from pathlib import Path

D = Path(__file__).parent


def load_jsonl(name):
    rows = []
    for line in (D / name).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def umi_case():
    report = json.loads((D / "umi_report.json").read_text(encoding="utf-8"))
    detail = load_jsonl("umi_detail.jsonl")
    print("== UMI V4 ==")
    print("函申报(report.json):", json.dumps(report, ensure_ascii=False)[:600])
    n = len(detail)
    print(f"detail n={n}")
    keys = sorted(detail[0].keys())
    print("detail 字段:", keys)

    def acc(field):
        ok = sum(1 for r in detail if r.get(field))
        return ok, ok / n if n else float("nan")

    # 探明字段名后按实际算;先尝试常见命名
    for cand in ("correct_native", "native_correct", "ok_native"):
        if any(cand in keys for cand in keys) and cand in keys:
            break
    for suffix in ("native", "d128", "d96"):
        for prefix in ("correct_", "ok_", ""):
            k = f"{prefix}{suffix}"
            if k in keys:
                ok, a = acc(k)
                print(f"  {k}: {ok}/{n} = {a:.4f}")
                break
    # 通用兜底:打印首行样本供人工核对
    print("首行样本:", json.dumps(detail[0], ensure_ascii=False)[:400])


def g1_case(arm):
    summary = json.loads((D / f"g1f_{arm}_summary.json").read_text(encoding="utf-8"))
    rows = load_jsonl(f"g1f_{arm}_compare.jsonl")
    print(f"== G1-full {arm} ==")
    print("summary:", json.dumps(summary, ensure_ascii=False)[:500])
    n = len(rows)
    print(f"compare n={n}; 字段:", sorted(rows[0].keys()))
    print("首行样本:", json.dumps(rows[0], ensure_ascii=False)[:400])


if __name__ == "__main__":
    umi_case()
    for arm in "GB":
        g1_case(arm)
