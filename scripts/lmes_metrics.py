"""LongMemEval-S 检索三指标计算器(P@1 / P@5 / MRR)。

从 eval_longmemeval_accuracy.py 的 per-question jsonl(RETRIEVAL_ONLY 模式,
含 top_session_ids 字段)计算检索指标,与 evidence
docs/evidence/headhead_mem0_full500_20260826.json 的 S500_FINAL_v3_4type_dateanchor
(P@1 0.890 / P@5 0.978 / MRR 0.929)同口径。

口径:每题 answer_session_ids 可多值;
  P@k = top-k 内含任一答案 session 记 1,取均值;
  MRR = 1 / 首个命中排名,取均值。

用法:
  python scripts/lmes_metrics.py <per_question.jsonl> --dataset <longmem_s.json>
  # --dataset 缺省时退化为二值近似(仅 truth_in_top,精度有限,不推荐)
"""
import json
import sys
from collections import defaultdict


def parse_args(argv: list) -> tuple:
    if len(argv) < 2:
        print(__doc__)
        sys.exit(1)
    jsonl_path, dataset_path = argv[1], ""
    if "--dataset" in argv:
        i = argv.index("--dataset")
        dataset_path = argv[i + 1] if i + 1 < len(argv) else ""
    return jsonl_path, dataset_path


def main() -> None:
    jsonl_path, dataset_path = parse_args(sys.argv)
    rows = [json.loads(line) for line in open(jsonl_path, encoding="utf-8") if line.strip()]

    answers_by_qid: dict = {}
    if dataset_path:
        data = json.load(open(dataset_path, encoding="utf-8"))
        answers_by_qid = {d["question_id"]: set(d.get("answer_session_ids") or []) for d in data}
    if not answers_by_qid:
        print("[warn] 未提供 --dataset,退化为二值近似(truth_in_top),MRR/P@1 精度有限")

    agg = defaultdict(lambda: {"n": 0, "p1": 0.0, "p5": 0.0, "mrr": 0.0})
    for r in rows:
        top = r.get("top_session_ids") or []
        ans = answers_by_qid.get(r.get("question_id"))
        if ans:
            ranks = [i + 1 for i, s in enumerate(top) if s in ans]
            p1 = 1.0 if ranks and ranks[0] == 1 else 0.0
            p5 = 1.0 if ranks and ranks[0] <= 5 else 0.0
            mrr = 1.0 / ranks[0] if ranks else 0.0
        else:
            hit = 1.0 if r.get("truth_in_top") else 0.0
            p1, p5, mrr = hit, hit, hit
        t = agg[r.get("question_type", "?")]
        t["n"] += 1
        t["p1"] += p1
        t["p5"] += p5
        t["mrr"] += mrr

    n = len(rows)
    if not n:
        print("[error] 空文件:", jsonl_path)
        sys.exit(1)
    tot = agg.get("_overall")
    p1 = sum(t["p1"] for t in agg.values()) / n
    p5 = sum(t["p5"] for t in agg.values()) / n
    mrr = sum(t["mrr"] for t in agg.values()) / n
    print(f"n = {n}")
    print(f"P@1  = {p1:.3f}   (official 0.890)")
    print(f"P@5  = {p5:.3f}   (official 0.978)")
    print(f"MRR  = {mrr:.3f}   (official 0.929)")
    print("\nby type:")
    for qt in sorted(agg):
        t = agg[qt]
        print(f"  {qt:28s} n={t['n']:3d}  P@1={t['p1']/t['n']:.3f}  P@5={t['p5']/t['n']:.3f}  MRR={t['mrr']/t['n']:.3f}")


if __name__ == "__main__":
    main()
