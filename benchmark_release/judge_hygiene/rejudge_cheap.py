"""cheap-tier 判分补齐 adapter(2026-09-04 · judge 401 事故补救)。

背景:cheap-tier web full run 启动时 source 了 .ark_env(ARK_API_KEY),harness 默认
读 OPENAI_API_KEY → LLM 判分行全 401 记 0;程序化行(mc_choice_match 等)不受影响。
本脚本只重判 eval_function 以 llm_ 开头的行,程序化行保留原分,最终合并出干净 overall。

用法(GPU 机,等原 run 进程退出、per_question.jsonl 写满 240 行后):
  export $(cat /root/e2e/judge.env | xargs)   # OPENAI_API_KEY
  JUDGE_WORKERS=4 nohup python3 /root/rejudge_cheap.py \
      /root/lmev2_cheap_full/compass_web_small/per_question.jsonl \
      /root/rejudge_cheap_web_results.jsonl > /root/rejudge_cheap_web.log 2>&1 &

幂等:OUT 已有 question_id 跳过。checker 直 import 机上官方 harness 副本。
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/root/LongMemEval-V2/evaluation")
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
WORKERS = int(os.environ.get("JUDGE_WORKERS", "4"))


def load_rows(src: Path):
    rows = [json.loads(l) for l in src.read_text(encoding="utf-8").splitlines() if l.strip()]
    qids = [r["question_id"] for r in rows]
    if len(qids) != len(set(qids)):
        sys.exit(f"FATAL: duplicate question_id in {src} ({len(qids)} rows)")
    return rows


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
            return {"question_id": row["question_id"], "old_score": row["score"],
                    "new_score": int(bool(ok)), "attempts": attempt, "status": "ok"}
        except Exception as exc:  # noqa: BLE001
            last_err = str(exc)[:200]
            print(f"[retry] {row['question_id']} attempt {attempt}/6: {last_err}", flush=True)
    return {"question_id": row["question_id"], "old_score": row["score"],
            "new_score": 0, "attempts": len(BACKOFF), "status": "failed", "error": last_err}


def main() -> int:
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    rows = load_rows(src)
    llm_rows = [r for r in rows if r["eval_function"].startswith("llm_")]
    prog = [r for r in rows if not r["eval_function"].startswith("llm_")]
    done = set()
    if out.exists():
        done = {json.loads(l)["question_id"]
                for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    pending = [r for r in llm_rows if r["question_id"] not in done]
    print(f"total={len(rows)} llm={len(llm_rows)} prog={len(prog)} "
          f"done={len(done)} pending={len(pending)}", flush=True)

    from concurrent.futures import ThreadPoolExecutor
    lock = __import__("threading").Lock()

    def work(row):
        res = judge_one(row)
        with lock, out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
        print(f"done {res['question_id']} {res['old_score']}->{res['new_score']} "
              f"({res['status']})", flush=True)

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(work, pending))

    results = {json.loads(l)["question_id"]: json.loads(l)
               for l in out.read_text(encoding="utf-8").splitlines() if l.strip()}
    if len(results) < len(llm_rows):
        print(f"INCOMPLETE: {len(results)}/{len(llm_rows)} — rerun to resume", flush=True)
        return 1
    prog_sum = sum(r["score"] for r in prog)
    llm_sum = sum(results[r["question_id"]]["new_score"] for r in llm_rows)
    flips_up = sum(1 for r in llm_rows if results[r["question_id"]]["new_score"] > r["score"])
    flips_down = sum(1 for r in llm_rows if results[r["question_id"]]["new_score"] < r["score"])
    failed = sum(1 for v in results.values() if v["status"] == "failed")
    print(f"ALL_DONE overall={((prog_sum + llm_sum) / len(rows)):.4f} "
          f"({int(prog_sum + llm_sum)}/{len(rows)}) · prog={prog_sum}/{len(prog)} · "
          f"llm={llm_sum}/{len(llm_rows)} · flips +{flips_up}/-{flips_down} · failed={failed}",
          flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
