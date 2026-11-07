#!/usr/bin/env python3
"""LongMemEval-S · hindsight 臂(独立评测 · 预注册 V1 + V1.1 附录)。

冻结面协议(与 compass 56.6% 参照跑的最大对齐):
  · subject/judge prompt、judge 解析、temporal 抽取、温度、单 vote——全部
    逐字复用 tests/eval_longmemeval_accuracy.py(import 而非复制,冻结文件零改动)
  · 唯一置换:检索步 = hindsight retain→recall(官方 hindsight-client,默认参数)
  · subject=judge=qwen3.8-max(V1.2 附录:参照车道 deepseek-v3.2/ARK coding 已死,
    11/7 实测订阅过期;qwen 车道=百炼 TokenPlan 订阅,用户 11/7 指定;MiniMax-M3 为
    已验证 fallback)

Run(两阶段,均可断点续跑):
  python tests/eval_hindsight_arm.py --phase retain --workers 6
  python tests/eval_hindsight_arm.py --phase eval

Bank 协议:每题一 bank(lme2-<sha12>),retain 内容=session_to_text(600),
document_id=session_id,timestamp=haystack 日期(其原生接口)。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

# === LLM 车道(V1.2 附录冻结):qwen3.8-max @ 百炼 TokenPlan compatible-mode ===
# (V1.1 的 MiniMax-M3 为已验证 fallback;key 经 QWEN_TOKENPLAN_API_KEY 注入)
# 必须在 import 冻结 harness 前落位(harness 在模块级读 env)。
os.environ.setdefault("ZMM_LLM_PROVIDER", "openai")
os.environ.setdefault("ZMM_LLM_BASE_URL", "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
os.environ.setdefault("ZMM_LLM_API_KEY", os.environ.get("QWEN_TOKENPLAN_API_KEY", ""))
os.environ.setdefault("ZMM_SUBJECT_MODEL", "qwen3.8-max")
os.environ.setdefault("ZMM_JUDGE_PROVIDER", "openai")
os.environ.setdefault("ZMM_JUDGE_BASE_URL", "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1")
os.environ.setdefault("ZMM_JUDGE_API_KEY", os.environ.get("QWEN_TOKENPLAN_API_KEY", ""))
os.environ.setdefault("ZMM_JUDGE_MODEL", "qwen3.8-max")
os.environ.setdefault("ZMM_LONGMEMEVAL_PATH", "/tmp/longmemeval_s.json")

from tests import hindsight_adapter as hsa  # noqa: E402
from tests.eval_longmemeval_accuracy import (  # noqa: E402  冻结面·逐字复用
    JUDGE_PROMPT_TMPL,
    SUBJECT_TEMPERATURE,
    _parse_judge,
    call_vertex_gemini,
    extract_temporal_answer,
    pick_subject_prompt,
    session_to_text,
)

RUN_DIR = Path(os.environ.get("HS_EVAL_RUN_DIR", "/tmp/hs_eval"))
BANKS_DONE = RUN_DIR / "banks_done.jsonl"
RESULTS = RUN_DIR / "hindsight_arm_results.jsonl"


def load_data(full: bool, subset: int, start: int, end: int) -> list[dict]:
    data = json.load(open(os.environ["ZMM_LONGMEMEVAL_PATH"], encoding="utf-8"))
    if not full:
        per = max(1, subset // 6)
        from collections import defaultdict
        by_type = defaultdict(list)
        for d in data:
            by_type[d["question_type"]].append(d)
        data = [x for t in sorted(by_type) for x in by_type[t][:per]]
    _stop = end if end else len(data)
    return data[start:_stop]


def _client():
    from hindsight_client import Hindsight
    return Hindsight(base_url=hsa.DEFAULT_BASE_URL, timeout=hsa.CLIENT_TIMEOUT)


def phase_retain(data: list[dict], workers: int) -> None:
    done: set[str] = set()
    if BANKS_DONE.exists():
        for line in BANKS_DONE.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done.add(json.loads(line)["bank"])
    todo = [q for q in data if hsa.bank_id_for(q["haystack_session_ids"]) not in done]
    print(f"banks: {len(done)} done · {len(todo)} to retain · workers={workers}")
    t0 = time.time()
    n_ok = 0
    with open(BANKS_DONE, "a", encoding="utf-8") as f_out, \
            ThreadPoolExecutor(max_workers=workers) as pool:
        def _retain_one(q: dict) -> dict:
            bank = hsa.bank_id_for(q["haystack_session_ids"])
            mem = hsa.HindsightMemory(bank, client=_client())
            n = mem.retain_corpus(
                q["haystack_sessions"], q["haystack_session_ids"],
                dates=q.get("haystack_dates"), session_to_text=session_to_text)
            return {"bank": bank, "n": n}

        futures = {pool.submit(_retain_one, q): q for q in todo}
        for fut in as_completed(futures):
            q = futures[fut]
            try:
                rec = fut.result()
            except hsa.HindsightError as e:
                # fail loud:留证后中止(预注册 §一·禁静默跳过)
                f_out.flush()
                raise SystemExit(f"RETAIN_ABORT bank={hsa.bank_id_for(q['haystack_session_ids'])}: {e}")
            f_out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f_out.flush()
            n_ok += 1
            if n_ok % 10 == 0 or n_ok == len(todo):
                el = time.time() - t0
                print(f"  retained {n_ok}/{len(todo)} banks · {el:.0f}s "
                      f"· ETA {el / n_ok * (len(todo) - n_ok):.0f}s", flush=True)
    print("retain phase complete")


def phase_eval(data: list[dict]) -> None:
    done_qids: set[str] = set()
    if RESULTS.exists():
        for line in RESULTS.read_text(encoding="utf-8").splitlines():
            if line.strip():
                done_qids.add(json.loads(line)["question_id"])
    todo = [(i, q) for i, q in enumerate(data) if q["question_id"] not in done_qids]
    print(f"eval: {len(done_qids)} done · {len(todo)} to run")

    client = _client()
    correct = 0
    n_eval = 0
    t0 = time.time()
    with open(RESULTS, "a", encoding="utf-8") as f_out:
        for i, q in todo:
            qt = q["question_type"]
            question, truth = q["question"], q.get("answer", "")
            bank = hsa.bank_id_for(q["haystack_session_ids"])
            # Step 1: hindsight recall(官方默认参数;空=数据照报)
            results = hsa.HindsightMemory(bank, client=client).recall_memory(question)
            context = hsa.build_recall_context(results)
            k = max(1, len(results))
            # Step 2+3: subject + judge(逐字复用冻结 harness)
            prompt_tmpl = pick_subject_prompt(qt)
            try:
                raw_answer = call_vertex_gemini(
                    os.environ["ZMM_SUBJECT_MODEL"],
                    prompt_tmpl.format(k=k, context=context, question=question),
                    max_out_tok=2048, temperature=SUBJECT_TEMPERATURE).strip()
                model_answer = (extract_temporal_answer(raw_answer)
                                if qt == "temporal-reasoning" else raw_answer)
            except Exception as e:  # noqa: BLE001 — 显式 error 标记(照报·禁静默)
                model_answer = f"[SUBJECT_ERROR: {e}]"
                raw_answer = model_answer
            try:
                judge_raw = call_vertex_gemini(
                    os.environ["ZMM_JUDGE_MODEL"],
                    JUDGE_PROMPT_TMPL.format(question=question, truth=truth,
                                             answer=model_answer),
                    max_out_tok=2048, is_judge=True).strip().upper()
                is_correct = _parse_judge(judge_raw)
            except Exception as e:  # noqa: BLE001
                is_correct = False
                judge_raw = f"[JUDGE_ERROR: {e}]"

            n_eval += 1
            correct += 1 if is_correct else 0
            truth_in_top = any(
                r.get("document_id") in q.get("answer_session_ids", [])
                for r in results)
            entry = {
                "i": i, "question_id": q["question_id"],
                "question_type": qt, "question": question[:200], "truth": truth,
                "model_answer": model_answer[:300],
                "judge_raw": judge_raw[:80], "is_correct": is_correct,
                "bank": bank, "n_recalled": len(results),
                "truth_in_top": truth_in_top,
                "recall_texts": [r["text"][:200] for r in results[:5]],
            }
            f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f_out.flush()
            el = time.time() - t0
            print(f"  [{n_eval}/{len(todo)}] {qt:30s} {'✓' if is_correct else '✗'} "
                  f"acc={correct/n_eval:.3f} ({correct}/{n_eval}) · "
                  f"recall={len(results)} · {el:.0f}s", flush=True)
    print("eval phase complete — run summarize:")


def summarize() -> None:
    from collections import defaultdict
    rows = [json.loads(l) for l in
            RESULTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_type = defaultdict(lambda: {"n": 0, "correct": 0, "hit": 0, "judge_err": 0})
    correct = n = hits = jerr = 0
    for r in rows:
        n += 1
        correct += r["is_correct"]
        hits += r["truth_in_top"]
        jerr += r["judge_raw"].startswith("[JUDGE_ERROR")
        s = by_type[r["question_type"]]
        s["n"] += 1
        s["correct"] += r["is_correct"]
        s["hit"] += r["truth_in_top"]
        s["judge_err"] += r["judge_raw"].startswith("[JUDGE_ERROR")
    print(f"\n=== LongMemEval-S hindsight arm (n={n}) ===")
    print(f"  overall accuracy = {correct}/{n} = {correct/n:.3f}" if n else "  (empty)")
    print(f"  truth_in_top (doc-id hit) = {hits}/{n}")
    print(f"  judge explicit errors = {jerr}/{n}")
    for qt in sorted(by_type):
        s = by_type[qt]
        print(f"  {qt:30s} n={s['n']:3d} acc={s['correct']/s['n']:.3f} "
              f"hit={s['hit']/s['n']:.3f}")


def phase_verify(data: list[dict]) -> None:
    """以 DB 落库数收账(async 提交后服务端消化可能滞后;不重提交防重复)。

    expected = 该 bank 去空/去重后的 item 数(与 adapter 逻辑同款)。
    bank 达标→verified_banks.jsonl;15 分钟零进展→报告退出(fail loud)。
    """
    import urllib.request
    expected: dict[str, int] = {}
    for q in data:
        bank = hsa.bank_id_for(q["haystack_session_ids"])
        # 逐 id 去重+跳空(与 adapter 相同口径)
        seen_ids, n = set(), 0
        for sid, sess in zip(q["haystack_session_ids"], q["haystack_sessions"]):
            if sid in seen_ids:
                continue
            if not session_to_text(sess, max_chars=600, date=None).strip():
                continue
            seen_ids.add(sid)
            n += 1
        expected[bank] = n

    def docs_count(bank: str) -> int:
        try:
            with urllib.request.urlopen(
                f"{hsa.DEFAULT_BASE_URL}/v1/default/banks/{bank}/documents",
                timeout=15) as r:
                import json as _json
                return len(_json.load(r).get("items", []))
        except Exception:
            return -1

    t0 = time.time()
    last_progress = (0, time.time())
    while True:
        pending = {b: e for b, e in expected.items()
                   if docs_count(b) < e}
        done = len(expected) - len(pending)
        el = time.time() - t0
        print(f"verify: {done}/{len(expected)} banks complete · "
              f"{len(pending)} pending · {el:.0f}s", flush=True)
        (Path("/tmp/hs_eval/verified_banks.txt")).write_text(
            "\n".join(b for b in expected if b not in pending), encoding="utf-8")
        if not pending:
            print("VERIFY_ALL_DONE")
            return
        if done == last_progress[0] and time.time() - last_progress[1] > 900:
            short = sorted(pending.items(),
                           key=lambda kv: docs_count(kv[0]))[:5]
            raise SystemExit(f"VERIFY_STALLED pending={len(pending)} "
                             f"sample={[(b, docs_count(b), e) for b, e in short]}")
        if done != last_progress[0]:
            last_progress = (done, time.time())
        time.sleep(60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["retain", "verify", "eval", "summarize"], required=True)
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--subset", type=int, default=30)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    if args.phase == "summarize":
        summarize()
        return
    data = load_data(args.full, args.subset, args.start, args.end)
    if args.phase == "retain":
        phase_retain(data, args.workers)
    elif args.phase == "verify":
        phase_verify(data)
    else:
        phase_eval(data)


if __name__ == "__main__":
    main()
