#!/usr/bin/env python3
# Usage: python tests/claude_rejudge.py <input.jsonl> --out <output.jsonl> --model claude-haiku-4-5-20251001 [--limit N] [--resume]
"""Claude cross-judge re-scoring for LongMemEval accuracy eval.

Re-judges the (question, truth, model_answer) tuples produced by
tests/eval_longmemeval_accuracy.py using Claude via a proxy. Pair with
the existing Gemini-2.5-pro judge to compute inter-rater reliability
(Cohen's kappa) — the standard reviewer ask for LLM-as-judge papers.

Stdlib only (urllib.request). Reads:
  ANTHROPIC_BASE_URL   (default https://v2.qixuw.com)
  ANTHROPIC_AUTH_TOKEN (required · sent as x-api-key header)

Uses the EXACT JUDGE_PROMPT_TMPL from tests/eval_longmemeval_accuracy.py
for fair comparison.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

# Byte-identical copy of JUDGE_PROMPT_TMPL from tests/eval_longmemeval_accuracy.py.
# DO NOT re-word — reviewer reliability requires identical prompt across judges.
JUDGE_PROMPT_TMPL = """You are a strict evaluator. The user asked a question. You are given the ground-truth answer and a model-generated answer. Decide whether the model's answer is correct.

The model's answer is CORRECT if it conveys the same factual content as the ground truth, even if worded differently. Allow paraphrasing, partial matches that capture the key fact, or extra context. Mark INCORRECT if the model's answer is factually wrong, missing the key fact, or hallucinated.

Question: {question}

Ground-truth answer: {truth}

Model's answer: {answer}

Reply with ONLY one word: CORRECT or INCORRECT."""


BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://v2.qixuw.com").rstrip("/")
AUTH_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT = 60  # seconds


def call_claude(model: str, prompt: str, max_tokens: int = 16) -> str:
    """POST /v1/messages via proxy · returns raw text content."""
    if not AUTH_TOKEN:
        raise RuntimeError("ANTHROPIC_AUTH_TOKEN env var is empty")
    url = f"{BASE_URL}/v1/messages"
    body = json.dumps({
        "model": model,
        "max_tokens": max_tokens,
        "temperature": 0.0,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": AUTH_TOKEN,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    # Claude response: {"content": [{"type": "text", "text": "..."}], ...}
    blocks = payload.get("content", [])
    for b in blocks:
        if b.get("type") == "text":
            return b.get("text", "")
    return ""


def call_claude_with_retry(model: str, prompt: str) -> str:
    """One retry on timeout or 5xx · otherwise let it raise."""
    try:
        return call_claude(model, prompt)
    except (urllib.error.URLError, TimeoutError) as e:
        # urllib.error.HTTPError is a subclass of URLError · inspect status below
        status = getattr(e, "code", None)
        if status is not None and 400 <= status < 500:
            raise  # client error · don't retry
        time.sleep(1.0)
        return call_claude(model, prompt)


def parse_verdict(raw: str) -> bool:
    """Normalize Claude's reply to bool · matches eval_longmemeval_accuracy.py.

    Check INCORRECT before CORRECT because 'INCORRECT' contains 'CORRECT'.
    Default to INCORRECT on ambiguous output (strict eval).
    """
    head = (raw or "").strip().upper()
    if not head:
        return False
    window = head[:32]
    if "INCORRECT" in window:
        return False
    if "CORRECT" in window:
        return True
    return False


def load_done_ids(out_path: Path) -> set:
    done = set()
    if not out_path.exists():
        return done
    with out_path.open("r", encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except json.JSONDecodeError:
                continue
            qid = rec.get("question_id")
            if qid:
                done.add(qid)
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="per-question jsonl from eval_longmemeval_accuracy.py")
    ap.add_argument("--out", required=True, help="output jsonl with claude_judge_raw/is_correct appended")
    ap.add_argument("--model", default="claude-haiku-4-5-20251001")
    ap.add_argument("--limit", type=int, default=0, help="0 = no limit")
    ap.add_argument("--resume", action="store_true", help="skip question_ids already in --out")
    ap.add_argument("--sleep", type=float, default=0.3, help="seconds between calls · default 0.3")
    args = ap.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    done_ids = load_done_ids(out_path) if args.resume else set()
    if done_ids:
        print(f"[resume] skipping {len(done_ids)} already-judged questions", file=sys.stderr)

    n_done = 0
    n_agree = 0
    t0 = time.time()
    with in_path.open("r", encoding="utf-8") as fin, \
         out_path.open("a", encoding="utf-8") as fout:
        for ln in fin:
            ln = ln.strip()
            if not ln:
                continue
            try:
                rec = json.loads(ln)
            except json.JSONDecodeError as e:
                print(f"[warn] skip malformed line: {e}", file=sys.stderr)
                continue
            qid = rec.get("question_id")
            if qid in done_ids:
                continue
            if args.limit and n_done >= args.limit:
                break
            question = rec.get("question", "")
            truth = rec.get("truth", rec.get("answer", ""))
            model_answer = rec.get("model_answer", "")
            prompt = JUDGE_PROMPT_TMPL.format(
                question=question, truth=truth, answer=model_answer)
            try:
                raw = call_claude_with_retry(args.model, prompt)
            except Exception as e:
                print(f"[error] qid={qid} {type(e).__name__}: {e}", file=sys.stderr)
                raw = f"<ERROR: {type(e).__name__}: {e}>"
            claude_correct = parse_verdict(raw)
            out_rec = dict(rec)
            out_rec["claude_judge_raw"] = raw
            out_rec["claude_is_correct"] = bool(claude_correct)
            fout.write(json.dumps(out_rec, ensure_ascii=False) + "\n")
            fout.flush()

            n_done += 1
            gemini_correct = bool(rec.get("is_correct"))
            if gemini_correct == claude_correct:
                n_agree += 1
            if n_done % 20 == 0:
                pct = 100.0 * n_agree / n_done
                elapsed = time.time() - t0
                rate = n_done / elapsed if elapsed > 0 else 0.0
                print(f"[{n_done}] agreement={pct:.1f}%  "
                      f"({n_agree}/{n_done})  {rate:.2f} q/s",
                      file=sys.stderr)
            time.sleep(args.sleep)

    if n_done:
        pct = 100.0 * n_agree / n_done
        print(f"[done] {n_done} rejudged · agreement={pct:.1f}% ({n_agree}/{n_done}) "
              f"-> {out_path}", file=sys.stderr)
    else:
        print("[done] 0 new questions judged", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
