"""d12 重判聚合:LLM 题用重判分,mc 题保持原分 → d12 口径对齐版 overall。

聚合规则(预注册):
- LLM checker 题(156)取重判分 new_score;failed 题保留 d12 原分并计入披露。
- mc_choice_match 题(295)确定性判定,保持 d12 原分。
- 输出重判版 d12 基线 overall,作为 d14 判据锚。
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
D12 = HERE.parent / "d12"


def main() -> int:
    rejudged = {}
    failed = []
    with (HERE / "rejudge_results.jsonl").open(encoding="utf-8") as fin:
        for line in fin:
            if not line.strip():
                continue
            r = json.loads(line)
            rejudged[r["question_id"]] = r
            if r["status"] == "failed":
                failed.append(r["question_id"])

    summary = {}
    for domain, subdir in [("ent", "compass_enterprise_small"), ("web", "compass_web_small")]:
        total = llm_n = mc_sum = llm_sum = 0
        flips = []
        with (D12 / subdir / "per_question.jsonl").open(encoding="utf-8") as fin:
            for line in fin:
                if not line.strip():
                    continue
                r = json.loads(line)
                total += 1
                qid = r["question_id"]
                if r["eval_function"].startswith("llm_"):
                    llm_n += 1
                    rr = rejudged.get(qid)
                    if rr and rr["status"] == "ok":
                        s = rr["new_score"]
                        if s != r["score"]:
                            flips.append((qid, r["score"], s))
                    else:
                        s = r["score"]  # failed 保留原分
                    llm_sum += s
                else:
                    mc_sum += r["score"]
        n = total
        overall = (llm_sum + mc_sum) / n
        summary[domain] = dict(
            total=n, llm_rejudged=llm_n, mc_kept=n - llm_n,
            flips=flips, flip_up=sum(1 for f in flips if f[2] > f[1]),
            flip_down=sum(1 for f in flips if f[2] < f[1]),
            rejudge_overall=round(overall, 4),
            d12_reported=dict(ent=0.403, web=0.367)[domain],
        )
        print(f"{domain}: n={n} llm={llm_n} flips={len(flips)}(+{summary[domain]['flip_up']}/-{summary[domain]['flip_down']})  REJUDGE_OVERALL={overall:.4f}  (d12 报告口径 {summary[domain]['d12_reported']})")

    if failed:
        print(f"WARNING: {len(failed)} failed rows kept at original score: {failed[:5]}...")
    (HERE / "rejudge_final.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print("-> rejudge_final.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
