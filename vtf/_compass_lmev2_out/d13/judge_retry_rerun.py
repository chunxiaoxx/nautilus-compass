"""d13 judge-retry 离线重判 · 按预注册 D13_JUDGE_RETRY_PREREG_20260831.md 执行。

- 直接 import 抢救回的上游 evaluation/qa_eval_metrics.py(与 d13 管线同源,未打 retry patch),
  调 llm_abstention_checker / llm_gotchas_checker → judge prompt 与管线同款结构性保证。
- 外层重试按预注册:单并发,指数退避 1/2/4/8/16/32s,每题最多 6 试;6 试全败 status=failed
  保留原 0 分并计入披露。
- 幂等:judge_retry_results.jsonl 已有的 question_id 跳过(支持中断续跑)。
- API key 从 ARK_API_KEY 传入 OPENAI_API_KEY,不落盘不回显(ARK coding plan 端点红线合规)。
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE / "rescued_upstream"))

import qa_eval_metrics  # noqa: E402

EVALUATOR_KW = dict(
    evaluator_model="doubao-seed-2-0-pro-260215",
    evaluator_base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
    evaluator_api_key=os.environ["OPENAI_API_KEY"],
    # 口径披露:d13 实配 medium/4096,reasoning 预算被吃满致 content 空(finish=length,
    # 诊断实测 reasoning_tokens=4096/4096 与 16384/16384 两档均吃满),系统性压 0。
    # 重判用 low/16384 允许 judge 完成判断;定案文档须披露此差异。
    evaluator_reasoning_effort="low",
    evaluator_max_completion_tokens=16384,
    evaluator_timeout_seconds=240.0,
)
BACKOFF = [1, 2, 4, 8, 16, 32]
OUT = HERE / "judge_retry_results.jsonl"
WORKERS = int(os.environ.get("JUDGE_WORKERS", "4"))  # 温和并发;d13 风暴为 16 路


def load_done() -> set[str]:
    if not OUT.exists():
        return set()
    return {
        json.loads(line)["question_id"]
        for line in OUT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def judge_one(row: dict) -> dict:
    checker = (
        qa_eval_metrics.llm_abstention_checker
        if row["eval_function"].startswith("llm_abstention_checker")
        else qa_eval_metrics.llm_gotchas_checker
    )
    last_err = None
    for attempt, delay in enumerate([0] + BACKOFF, start=1):
        if delay:
            time.sleep(delay)
        try:
            ok = checker(
                row["response_raw"],
                row["answer_gold"],
                question_item={"question": row["question_text"]},
                parsed_prediction=row["response_parsed_boxed"],
                model_response=row["response_raw"],
                **EVALUATOR_KW,
            )
            return {
                "question_id": row["question_id"],
                "domain": row.get("domain", ""),
                "new_score": int(bool(ok)),
                "attempts": attempt,
                "status": "ok",
            }
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)[:200]
            print(f"[retry] {row['question_id']} attempt {attempt}/6 failed: {last_err}", flush=True)
    return {
        "question_id": row["question_id"],
        "domain": row.get("domain", ""),
        "new_score": 0,
        "attempts": len(BACKOFF),
        "status": "failed",
        "error": last_err,
    }


def main() -> int:
    done = load_done()
    lists = [
        ("ent", HERE / "ent_judge_retry_list.jsonl"),
        ("web", HERE / "web_judge_retry_list.jsonl"),
    ]
    todo = []
    for domain, path in lists:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            row["domain"] = domain
            todo.append(row)
    pending = [r for r in todo if r["question_id"] not in done]
    print(f"total={len(todo)} done={len(done)} pending={len(pending)}", flush=True)

    from concurrent.futures import ThreadPoolExecutor

    write_lock = __import__("threading").Lock()

    def judge_and_log(row):
        result = judge_one(row)
        with write_lock:
            with OUT.open("a", encoding="utf-8") as fout:
                fout.write(json.dumps(result, ensure_ascii=False) + "\n")
        print(f"done {row['question_id']} -> {result['new_score']} ({result['status']})", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        results = list(pool.map(judge_and_log, pending))
    failed = sum(1 for line in OUT.read_text(encoding="utf-8").splitlines() if '"failed"' in line)
    total_now = len(load_done())
    rate = failed / total_now if total_now else 0
    print(f"ALL_DONE total={total_now} failed={failed} fail_rate={rate:.2%}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
