#!/usr/bin/env python3
"""LongMemEval-S end-to-end accuracy eval (paper's official metric).

Pipeline per question:
  1. Compass retrieves top-K sessions (bge-m3 ± reranker)
  2. Subject LLM answers given retrieved context
  3. Independent judge LLM scores answer correctness vs ground truth (binary)

This is the LongMemEval paper's primary evaluation metric (accuracy via
GPT-4o LLM-as-judge with >97% human agreement). We substitute Gemini-2.5-pro
as judge (Vertex AI · GCP service account) due to no GPT-4o access; paper
discusses this judge-model substitution caveat.

Variants:
  --pipeline=m3-only      | bge-m3 bi-encoder · top-5 retrieved
  --pipeline=m3-rerank    | bge-m3 retrieve top-50 → bge-reranker top-5  (default)

Run:
  py -3.12 tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --subset 30
  py -3.12 tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full

Cost estimate (full 500):
  · Vertex Gemini-Flash subject calls   ~$1
  · Vertex Gemini-Pro judge calls       ~$3
  · GPU embed + rerank                  free (local)
  Total ~$4 · ~85 min wall clock
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

PLUGIN = Path.home() / ".claude" / "plugins" / "nautilus-compass"
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402

DATASET_PATH = Path(os.environ.get(
    "ZMM_LONGMEMEVAL_PATH",
    str(Path.home() / ".cache/huggingface/hub/datasets--xiaowu0162--longmemeval"
                     "/snapshots/2ec2a557f339b6c0369619b1ed5793734cc87533/longmemeval_s"),
))
RERANKER_PATH = os.environ.get(
    "ZMM_RERANKER_MODEL",
    str(Path.home() / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3"),
)

SUBJECT_MODEL = os.environ.get("ZMM_SUBJECT_MODEL", "gemini-2.5-flash")
JUDGE_MODEL = os.environ.get("ZMM_JUDGE_MODEL", "gemini-2.5-pro")
TOP_K_RETRIEVE = 50
TOP_K_CONTEXT = 5

# === Subject prompt: answer using the retrieved context ===
# Less conservative · let model attempt extraction + counting + reasoning even if
# the answer is implicit. Only refuse if NO relevant info at all.
SUBJECT_PROMPT_TMPL = """You are a memory-augmented assistant. The user is asking about facts established in your past conversations with them. The retrieval system has already filtered to the {k} most relevant past sessions below — they DO contain the answer in 90%+ of cases.

YOUR TASK: Find and report the specific fact requested.

CRITICAL ANTI-REFUSAL RULES (read carefully):
  1. The answer IS in these sessions. Refusing with "I don't have that information" is the WORST mistake — you will fail the task. Trying and being wrong is better than refusing.
  2. The fact may need extraction (a specific name/number/date), counting (count items mentioned across multiple turns), or inference (preferences shown by reactions). DO ALL OF THESE.
  3. State the specific fact directly. NO preamble like "Based on our previous conversation..." or "From our past chats...". Lead with the answer itself.
  4. Maximum 1-2 sentences. Be concrete: a number, a name, a date, a time, a place.
  5. Only refuse if the sessions are about a completely unrelated topic (e.g. user asks about cooking and sessions are all about coding). If the topic matches, COMMIT to an answer based on best available evidence.

=== {k} past sessions (most relevant first) ===
{context}

=== Question ===
{question}

Direct answer (lead with the specific fact · no preamble · commit to an answer):"""

# === Judge prompt: binary accuracy ===
JUDGE_PROMPT_TMPL = """You are a strict evaluator. The user asked a question. You are given the ground-truth answer and a model-generated answer. Decide whether the model's answer is correct.

The model's answer is CORRECT if it conveys the same factual content as the ground truth, even if worded differently. Allow paraphrasing, partial matches that capture the key fact, or extra context. Mark INCORRECT if the model's answer is factually wrong, missing the key fact, or hallucinated.

Question: {question}

Ground-truth answer: {truth}

Model's answer: {answer}

Reply with ONLY one word: CORRECT or INCORRECT."""


def session_to_text(session, max_chars=600):
    parts = [f"[{t.get('role', '?')}] {t.get('content', '')}" for t in session]
    return "\n".join(parts)[:max_chars]


def build_context(top_sessions: list[dict]) -> str:
    """Join top-K retrieved sessions with separators."""
    chunks = []
    for i, s in enumerate(top_sessions, 1):
        chunks.append(f"--- Session {i} ---\n{session_to_text(s, max_chars=800)}")
    return "\n\n".join(chunks)


def call_vertex_gemini(model: str, prompt: str, max_out_tok: int = 2048) -> str:
    """Vertex AI Gemini call · uses GOOGLE_APPLICATION_CREDENTIALS service account.

    NOTE: gemini-2.5-pro/flash are thinking models · the 'thinking budget' is
    counted against max_output_tokens. 512 was too low: thinking ate it all
    before the actual answer. Default 2048 leaves room for both.
    """
    from google import genai
    gcp = json.load(open(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], encoding="utf-8"))
    project = gcp["project_id"]
    if not hasattr(call_vertex_gemini, "_client"):
        call_vertex_gemini._client = genai.Client(
            vertexai=True, project=project, location="us-central1")
    client = call_vertex_gemini._client
    resp = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "max_output_tokens": max_out_tok,
            "temperature": 0.1,
        },
    )
    return resp.text or ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", choices=["m3-only", "m3-rerank"], default="m3-rerank")
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--subset", type=int, default=30)
    ap.add_argument("--start", type=int, default=0, help="resume from question N")
    args = ap.parse_args()

    print(f"pipeline:       {args.pipeline}")
    print(f"subject:        {SUBJECT_MODEL}")
    print(f"judge:          {JUDGE_MODEL}")
    print(f"dataset:        {DATASET_PATH}")
    print(f"GCP creds:      {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '(MISSING!)')[:60]}...")

    # Load embedder
    t0 = time.time()
    emb = zmd.get_embedder()
    print(f"bi-encoder ready: {time.time()-t0:.1f}s")

    # Load reranker if needed
    reranker = None
    if args.pipeline == "m3-rerank":
        from sentence_transformers import CrossEncoder
        try:
            import torch
            device = os.environ.get("ZMM_DEVICE",
                "cuda" if torch.cuda.is_available() else "cpu")
        except Exception:
            device = "cpu"
        t0 = time.time()
        reranker = CrossEncoder(RERANKER_PATH, device=device)
        print(f"reranker ready ({device}): {time.time()-t0:.1f}s")

    # Load dataset
    data = json.load(open(DATASET_PATH, encoding="utf-8"))
    if not args.full:
        # balanced subset · per_type questions per type
        per = max(1, args.subset // 6)
        by_type = defaultdict(list)
        for d in data:
            by_type[d["question_type"]].append(d)
        data = [x for t in sorted(by_type) for x in by_type[t][:per]]
    print(f"questions: {len(data)} (start={args.start})")

    # Output paths
    pipeline_tag = args.pipeline.replace("-", "_")
    n_tag = "full" if args.full else f"subset{len(data)}"
    out_jsonl = zmd.CACHE_DIR / f"longmemeval_acc_{pipeline_tag}_{n_tag}_{int(time.time())}.jsonl"
    out_summary = zmd.CACHE_DIR / f"longmemeval_acc_{pipeline_tag}_{n_tag}_{int(time.time())}_summary.json"

    correct = 0
    n_evaluated = 0
    by_type_stats = defaultdict(lambda: {"n": 0, "correct": 0})

    t_start = time.time()
    with open(out_jsonl, "w", encoding="utf-8") as f_out:
        for i, q in enumerate(data[args.start:], start=args.start):
            question = q["question"]
            truth = q.get("answer", "")
            qt = q["question_type"]
            sess_ids = q["haystack_session_ids"]
            sessions = q["haystack_sessions"]
            sess_texts = [session_to_text(s) for s in sessions]

            # Step 1: bi-encoder retrieve
            q_emb = emb.encode(question)
            sess_embs = [emb.encode(t) for t in sess_texts]
            sims = [(j, zmd.cosine(q_emb, sess_embs[j])) for j in range(len(sess_ids))]
            sims.sort(key=lambda x: -x[1])

            if reranker:
                # Step 2: cross-encoder rerank top-K
                topk = sims[:TOP_K_RETRIEVE]
                pairs = [(question, sess_texts[idx]) for idx, _ in topk]
                rerank_scores = reranker.predict(pairs)
                reranked = sorted(zip(topk, rerank_scores), key=lambda x: -x[1])
                top_indices = [idx for (idx, _), _ in reranked[:TOP_K_CONTEXT]]
            else:
                top_indices = [idx for idx, _ in sims[:TOP_K_CONTEXT]]

            top_sessions = [sessions[j] for j in top_indices]
            context = build_context(top_sessions)

            # Step 3: Subject LLM answers
            try:
                model_answer = call_vertex_gemini(
                    SUBJECT_MODEL,
                    SUBJECT_PROMPT_TMPL.format(k=TOP_K_CONTEXT, context=context, question=question),
                    max_out_tok=2048,
                ).strip()
            except Exception as e:
                model_answer = f"[SUBJECT_ERROR: {e}]"

            # Step 4: Judge LLM scores
            try:
                judge_raw = call_vertex_gemini(
                    JUDGE_MODEL,
                    JUDGE_PROMPT_TMPL.format(question=question, truth=truth, answer=model_answer),
                    max_out_tok=2048,
                ).strip().upper()
                # robust extraction · model may add prose
                judge_clean = re.sub(r"[^A-Z]", "", judge_raw)
                is_correct = "CORRECT" in judge_raw and "INCORRECT" not in judge_raw
                # safer: look for first occurrence
                m_inc = judge_raw.find("INCORRECT")
                m_cor = judge_raw.find("CORRECT")
                if m_inc != -1 and (m_cor == -1 or m_inc < m_cor):
                    is_correct = False
                elif m_cor != -1:
                    is_correct = True
                else:
                    is_correct = False
            except Exception as e:
                is_correct = False
                judge_raw = f"[JUDGE_ERROR: {e}]"

            n_evaluated += 1
            if is_correct:
                correct += 1
            by_type_stats[qt]["n"] += 1
            if is_correct:
                by_type_stats[qt]["correct"] += 1

            # Log per-question
            entry = {
                "i": i,
                "question_id": q.get("question_id"),
                "question_type": qt,
                "question": question[:200],
                "truth": truth,
                "model_answer": model_answer[:300],
                "judge_raw": judge_raw[:80],
                "is_correct": is_correct,
                "top_session_ids": [sess_ids[j] for j in top_indices],
                "truth_in_top": any(sess_ids[j] in q.get("answer_session_ids", []) for j in top_indices),
            }
            f_out.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f_out.flush()

            elapsed = time.time() - t_start
            eta = elapsed / (i + 1 - args.start) * (len(data) - i - 1) if i > args.start else 0
            running_acc = correct / n_evaluated
            print(f"  [{i+1}/{len(data)}] {qt:30s} {'✓' if is_correct else '✗'} "
                  f"acc={running_acc:.3f} ({correct}/{n_evaluated}) · {elapsed:.0f}s · ETA {eta:.0f}s",
                  flush=True)

    # Aggregate
    n = n_evaluated
    print(f"\n=== LongMemEval-S accuracy ({args.pipeline} · n={n}) ===")
    print(f"  overall accuracy = {correct}/{n} = {correct/n:.3f}")
    print(f"\n=== by question_type ===")
    for qt in sorted(by_type_stats):
        s = by_type_stats[qt]
        if s["n"] == 0:
            continue
        print(f"  {qt:30s} n={s['n']:3d}  acc={s['correct']/s['n']:.3f} ({s['correct']}/{s['n']})")

    summary = {
        "pipeline": args.pipeline,
        "subject_model": SUBJECT_MODEL,
        "judge_model": JUDGE_MODEL,
        "n": n,
        "accuracy": correct / n if n else 0,
        "by_type": {qt: {"n": s["n"], "correct": s["correct"], "acc": s["correct"]/s["n"] if s["n"] else 0}
                    for qt, s in by_type_stats.items()},
        "out_jsonl": str(out_jsonl),
    }
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  per-question log:  {out_jsonl}")
    print(f"  summary:           {out_summary}")


if __name__ == "__main__":
    main()
