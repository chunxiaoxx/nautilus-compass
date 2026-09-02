"""d12 基线 451 题全量重判执行(low/16384 口径,与 d14 一致)。

复用 d13 重判同款逻辑(import 同一份 rescued_upstream checker),
仅输入换成 d12 全量 451 题清单。幂等:results jsonl 已有 question_id 跳过。
"""
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent / "d13" / "rescued_upstream"))

import qa_eval_metrics  # noqa: E402

EVALUATOR_KW = dict(
    evaluator_model="doubao-seed-2-0-pro-260215",
    evaluator_base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
    evaluator_api_key=os.environ["OPENAI_API_KEY"],
    evaluator_reasoning_effort="low",
    evaluator_max_completion_tokens=16384,
    evaluator_timeout_seconds=240.0,
)
BACKOFF = [1, 2, 4, 8, 16, 32]
OUT = HERE / "rejudge_results.jsonl"
WORKERS = int(os.environ.get("JUDGE_WORKERS", "4"))


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
                "d12_score": row.get("d12_score"),
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
        "d12_score": row.get("d12_score"),
        "new_score": 0,
        "attempts": len(BACKOFF),
        "status": "failed",
        "error": last_err,
    }


def main() -> int:
    done = load_done()
    todo = []
    for name in ["ent_rejudge_list.jsonl", "web_rejudge_list.jsonl"]:
        for line in (HERE / name).read_text(encoding="utf-8").splitlines():
            if line.strip():
                todo.append(json.loads(line))
    pending = [r for r in todo if r["question_id"] not in done]
    print(f"total={len(todo)} done={len(done)} pending={len(pending)}", flush=True)

    from concurrent.futures import ThreadPoolExecutor

    write_lock = __import__("threading").Lock()

    def judge_and_log(row):
        result = judge_one(row)
        with write_lock:
            with OUT.open("a", encoding="utf-8") as fout:
                fout.write(json.dumps(result, ensure_ascii=False) + "\n")
        print(f"done {row['question_id']} {row.get('d12_score')}->{result['new_score']} ({result['status']})", flush=True)
        return result

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(judge_and_log, pending))
    lines = OUT.read_text(encoding="utf-8").splitlines()
    failed = sum(1 for line in lines if '"failed"' in line)
    print(f"ALL_DONE total={len(lines)} failed={failed} fail_rate={failed/len(lines):.2%}" if lines else "EMPTY", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
