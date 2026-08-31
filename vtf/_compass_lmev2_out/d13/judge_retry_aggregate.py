"""d13 judge-retry 聚合 · 按预注册合并规则 max(原分, 重判分) 出修正口径。

输入:d13 两域 per_question.jsonl(RAW)+ judge_retry_results.jsonl(重判)
输出:judge_retry_final.json(RAW / 修正后 / d12 对照 / 判据结论 / 重判成功率)
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
DOMAINS = {"ent": ("compass_enterprise_small", 211), "web": ("compass_web_small", 240)}
D12 = {"ent": 0.403, "web": 0.367}
GATE_MARGIN = 0.05  # 预注册:≥ d12 + 5pt 过门


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    retries = load_jsonl(HERE / "judge_retry_results.jsonl")
    # 双进程并行事故:21 题被重判两次。取首次出现(时间最早)——无选择偏差;一致率作披露。
    retry_by_qid: dict = {}
    for r in retries:
        retry_by_qid.setdefault(r["question_id"], r)
    from collections import Counter

    dup_cnt = Counter(r["question_id"] for r in retries)
    dup_ids = [q for q, c in dup_cnt.items() if c > 1]
    agree = sum(1 for q in dup_ids if len({x["new_score"] for x in retries if x["question_id"] == q}) == 1)

    report: dict = {"domains": {}, "judge_retry": {}}
    for domain, (subdir, expected_total) in DOMAINS.items():
        rows = load_jsonl(HERE / subdir / "per_question.jsonl")
        raw_mean = sum(r["score"] for r in rows) / len(rows)
        fixed_failed = 0
        fixed_missing = 0
        flipped_up = 0
        for row in rows:
            retry = retry_by_qid.get(row["question_id"])
            if retry is None:
                if row["score"] == 0 and row["eval_function"].startswith("llm_"):
                    fixed_missing += 1
                continue
            if retry["status"] == "failed":
                fixed_failed += 1
                continue
            if retry["new_score"] > row["score"]:
                row["score"] = retry["new_score"]
                flipped_up += 1
        fixed_mean = sum(r["score"] for r in rows) / len(rows)
        gate = D12[domain] + GATE_MARGIN
        report["domains"][domain] = {
            "n": len(rows),
            "expected_total": expected_total,
            "raw": round(raw_mean, 4),
            "fixed": round(fixed_mean, 4),
            "d12": D12[domain],
            "gate_line": round(gate, 4),
            "pass_gate": fixed_mean >= gate,
            "flipped_up": flipped_up,
            "retry_failed_kept_zero": fixed_failed,
            "llm_zero_not_in_retry_list": fixed_missing,
        }

    ok = len(retry_by_qid)
    failed = sum(1 for r in retry_by_qid.values() if r["status"] == "failed")
    report["judge_retry"] = {
        "total_rows": len(retries),
        "unique_questions": ok,
        "dup_rejudged": len(dup_ids),
        "dup_agreement": f"{agree}/{len(dup_ids)}",
        "ok": ok,
        "failed": failed,
        "fail_rate": round(failed / ok, 4) if ok else None,
        "inconclusive_if_fail_rate_gt": 0.20,
    }
    inconclusive = retries and failed / len(retries) > 0.20
    report["verdict"] = "INCONCLUSIVE(重判失败率>20%)" if inconclusive else (
        "任一域过门" if any(d["pass_gate"] for d in report["domains"].values())
        else "双域均未过门 → 刀3 全量验证路线关闭定案"
    )
    (HERE / "judge_retry_final.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
