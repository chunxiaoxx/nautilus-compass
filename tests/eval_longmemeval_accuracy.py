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
_ms_reranker = Path.home() / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3"
RERANKER_PATH = os.environ.get(
    "ZMM_RERANKER_MODEL",
    # local ModelScope path preferred · HF repo id fallback (mirrors daemon.py:
    # HF-cache-only hosts must not crash on the modelscope path being absent)
    str(_ms_reranker) if _ms_reranker.exists() else "BAAI/bge-reranker-v2-m3",
)

SUBJECT_MODEL = os.environ.get("ZMM_SUBJECT_MODEL", "gemini-2.5-flash")
JUDGE_MODEL = os.environ.get("ZMM_JUDGE_MODEL", "gemini-2.5-pro")
# ZMM_RETRIEVE_K caps the candidate pool fed to the reranker. Hardcoded 50 was
# a no-op on LongMemEval-S (haystack ≈40 sessions/Q → dense/BM25 pools are both
# the full corpus, RRF can only reshuffle, rerank erases order). 20 lets BM25
# actually swap in candidates dense missed.
TOP_K_RETRIEVE = int(os.environ.get("ZMM_RETRIEVE_K", "50"))
# Tier B #7 · Context window expansion. Default 5 preserves the v0.8 baseline.
# ZMM_TOPK=10 doubles the evidence given to the subject LLM. DeepSeek-V3.2 has
# 128K ctx so truncation isn't a risk. Expected +1~2 pts on ms/temporal.
TOP_K_CONTEXT = int(os.environ.get("ZMM_TOPK", "5"))
# Tier A #3 · Self-consistency majority vote. 1 = baseline (byte-identical to
# pre-vote behavior). 3 = run subject+judge 3x per question, take majority
# verdict. Expected +2~3 pts overall, reduces ssp variance.
ZMM_VOTE = int(os.environ.get("ZMM_VOTE", "1"))
SUBJECT_TEMPERATURE = float(os.environ.get("ZMM_SUBJECT_TEMPERATURE", "0.1"))

# Tier A #4 · Hybrid BM25 + dense retrieval with Reciprocal Rank Fusion.
# ZMM_HYBRID=0 (default): byte-identical to dense-only baseline · paper lock.
# ZMM_HYBRID=1: run BM25 in parallel with dense top-TOP_K_RETRIEVE, fuse by
# RRF (k=60), then feed fused top-TOP_K_RETRIEVE into the existing cross-encoder
# reranker. Target: single-session-user 58.6% → ~70%, overall P@5 86% → 90%.
ZMM_HYBRID = os.environ.get("ZMM_HYBRID", "0") == "1"
# v3.1 · retrieval-only loop: skip subject+judge entirely (fast iteration on
# retrieval levers — hit-rate is logged, no LLM calls, ~10s/q vs ~250s/q)
ZMM_RETRIEVAL_ONLY = os.environ.get("ZMM_RETRIEVAL_ONLY", "0") == "1"
RRF_K = 60

# Tier S #2 · ssu utterance-pair retrieval.
# ZMM_SSU_UTTERANCE=0 (default): byte-identical baseline · paper lock.
# ZMM_SSU_UTTERANCE=1: for qt=single-session-user only, after session-level
# retrieval, extract user-anchored utterance pairs from the top sessions and
# rerank with bge-reranker. Keeps top 3 utterance pairs as context instead of
# full sessions. Target: ssu P@5 58.6% → ~70%+, overall +1~2 pts.
# Other question types are UNAFFECTED (ssa 83.9%, ms 94% P@5 stay identical).
ZMM_SSU_UTTERANCE = os.environ.get("ZMM_SSU_UTTERANCE", "0") == "1"

# Ablation gate for the temporal-reasoning specialization.
# ZMM_TEMPORAL=1 (default): use the timeline scratch-pad prompt + extract_temporal_answer.
# ZMM_TEMPORAL=0: treat temporal-reasoning like any other qt (generic prompt, no pre-vote
# extraction) so we can measure the lift from the temporal specialization alone.
TEMPORAL_ENABLED = os.environ.get("ZMM_TEMPORAL", "1") == "1"


def _bm25_tokenize(text: str) -> list[str]:
    """Whitespace + punctuation split, lowercased. Keeps alphanumeric runs.

    Matches the Tier A #4 spec: simple, stateless, no stemmer/stopwords so the
    behavior is reproducible without a language resource dependency.
    """
    return re.findall(r"[a-z0-9]+", text.lower())

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

# === Temporal-reasoning specialized prompt ===
# Addresses the failure mode seen in v0.8 final (full 500): retrieval P@5=91.7%
# but acc=46.6% → the evidence is present but the model doesn't arrange events
# on a timeline before answering. Forcing a <timeline> scratch-pad lifts the
# reasoning ceiling without retraining.
TEMPORAL_PROMPT_TMPL = """You are a memory-augmented assistant. The user is asking a TIME-SENSITIVE question about facts established in past conversations. The retrieval system has already filtered to the {k} most relevant past sessions — the evidence IS in them (91%+ recall).

YOUR TASK: Extract the correct fact by FIRST building a timeline of events, THEN answering.

MANDATORY 2-STEP FORMAT:
  Step 1 — <timeline>
    List every dated/ordered event from the sessions relevant to the question, one per line:
      [DATE or SESSION#] event description
    Include ALL candidate events even if you're unsure which one matches.
    Sort chronologically (earliest first).
  Step 2 — <answer>
    Look at the timeline and pick the event that answers the question.
    Be literal about "before/after/most recent/first/last/between" — count events on the timeline.
    Output 1-2 sentences with the specific fact (date, duration, event name, ordering).

CRITICAL RULES:
  1. The answer IS in these sessions. Refusing is the worst mistake.
  2. "Most recent X" = the LAST entry of type X on your timeline.
  3. "How long between X and Y" = compute the difference from the timeline entries.
  4. If the question asks relative timing (before/after/since), the timeline makes it trivial — USE IT.
  5. Lead the final <answer> block with the fact, no preamble.

=== {k} past sessions (most relevant first) ===
{context}

=== Question (temporal-reasoning) ===
{question}

Respond with <timeline>...</timeline> then <answer>...</answer>:"""


def pick_subject_prompt(qt: str) -> str:
    """Route to specialized prompt by question_type.

    temporal-reasoning gets the timeline-first scratch-pad (Tier S #1 target)
    when TEMPORAL_ENABLED. Ablation path (ZMM_TEMPORAL=0) falls back to the
    generic template so temporal-reasoning is evaluated with the same prompt
    as every other qt.
    Other types keep the general prompt that already hits ssa 83.9% etc.
    """
    if qt == "temporal-reasoning" and TEMPORAL_ENABLED:
        return TEMPORAL_PROMPT_TMPL
    return SUBJECT_PROMPT_TMPL


def extract_temporal_answer(raw: str) -> str:
    """Strip the <timeline> scratch-pad; judge only sees the final <answer>.

    The timeline is thinking not answering — including it would leak
    false-positive keywords into the judge and inflate scores.
    """
    import re
    m = re.search(r"<answer>(.*?)(?:</answer>|$)", raw, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # Fallback: model ignored format · return everything after last </timeline>
    m2 = re.search(r"</timeline>(.*)", raw, re.DOTALL | re.IGNORECASE)
    if m2:
        return m2.group(1).strip()
    return raw  # judge will do its best

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


# === Tier S #2 · ssu utterance-pair retrieval ===
# See ZMM_SSU_UTTERANCE docstring above for rationale.
def extract_user_utterances(session: list[dict], window: int = 2) -> list[str]:
    """Sliding window of user-anchored utterance pairs.

    Each pair = [user_turn, next_turn] joined to 500 chars. ssu questions are
    phrased 'what did I say about X' — answer lives in one user turn plus its
    immediate assistant acknowledgment, so window=2 gives the right shape.
    """
    pairs = []
    n = len(session)
    for i, t in enumerate(session):
        if t.get("role") != "user":
            continue
        end = min(n, i + window)
        chunk_parts = []
        for j in range(i, end):
            tj = session[j]
            chunk_parts.append(f"[{tj.get('role', '?')}] {tj.get('content', '')}")
        chunk = "\n".join(chunk_parts)[:500]
        if chunk.strip():
            pairs.append(chunk)
    return pairs


def build_ssu_context(top_sessions: list[dict], question: str,
                      reranker=None, max_utterances: int = 3) -> str:
    """Utterance-level rerank within top sessions. Falls back to session-level
    if reranker absent or no user utterances found (e.g. sessions with only
    assistant turns — should not happen in LongMemEval but defensive).
    """
    all_pairs = []  # list[(session_idx, pair_text)]
    for si, s in enumerate(top_sessions, 1):
        for p in extract_user_utterances(s, window=2):
            all_pairs.append((si, p))
    if not all_pairs:
        return build_context(top_sessions)

    if reranker is not None and len(all_pairs) > max_utterances:
        rr_pairs = [(question, txt) for _, txt in all_pairs]
        try:
            scores = reranker.predict(rr_pairs)
            ranked = sorted(zip(all_pairs, scores), key=lambda x: -x[1])
            kept = [p for p, _ in ranked[:max_utterances]]
        except Exception:
            kept = all_pairs[:max_utterances]  # defensive · same as no reranker
    else:
        kept = all_pairs[:max_utterances]

    chunks = []
    for idx, (si, txt) in enumerate(kept, 1):
        chunks.append(f"--- Utterance {idx} (from Session {si}) ---\n{txt}")
    return "\n\n".join(chunks)


def call_vertex_gemini(model: str, prompt: str, max_out_tok: int = 2048,
                       temperature: float = 0.1) -> str:
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
            "temperature": temperature,
        },
    )
    return resp.text or ""


def _parse_judge(judge_raw: str) -> bool:
    """Parse judge response · first-occurrence of CORRECT/INCORRECT wins.

    Mirrors the original inline logic so single-call (ZMM_VOTE=1) stays
    byte-identical.
    """
    m_inc = judge_raw.find("INCORRECT")
    m_cor = judge_raw.find("CORRECT")
    if m_inc != -1 and (m_cor == -1 or m_inc < m_cor):
        return False
    elif m_cor != -1:
        return True
    return False


def _run_one_vote(qt: str, prompt_tmpl: str, context: str, question: str, truth: str):
    """Single subject+judge roundtrip · post-processed identically to the
    pre-vote path (temporal-reasoning goes through extract_temporal_answer
    before hitting the judge).

    Returns (model_answer, raw_answer, judge_raw, is_correct).
    """
    try:
        raw_answer = call_vertex_gemini(
            SUBJECT_MODEL,
            prompt_tmpl.format(k=TOP_K_CONTEXT, context=context, question=question),
            max_out_tok=2048,
            temperature=SUBJECT_TEMPERATURE,
        ).strip()
        if qt == "temporal-reasoning" and TEMPORAL_ENABLED:
            model_answer = extract_temporal_answer(raw_answer)
        else:
            model_answer = raw_answer
    except Exception as e:
        model_answer = f"[SUBJECT_ERROR: {e}]"
        raw_answer = model_answer

    try:
        judge_raw = call_vertex_gemini(
            JUDGE_MODEL,
            JUDGE_PROMPT_TMPL.format(question=question, truth=truth, answer=model_answer),
            max_out_tok=2048,
        ).strip().upper()
        is_correct = _parse_judge(judge_raw)
    except Exception as e:
        is_correct = False
        judge_raw = f"[JUDGE_ERROR: {e}]"

    return model_answer, raw_answer, judge_raw, is_correct


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
    print(f"vote (n):       {ZMM_VOTE}")
    print(f"subject temp:   {SUBJECT_TEMPERATURE} (judge stays 0.1)")
    print(f"temporal:       {'enabled (ZMM_TEMPORAL=1)' if TEMPORAL_ENABLED else 'disabled (ZMM_TEMPORAL=0)'}")
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

    # Load BM25 dependency if hybrid mode is on. Import is lazy so the default
    # (dense-only) path does not require rank_bm25 to be installed.
    BM25Okapi = None
    if ZMM_HYBRID:
        try:
            from rank_bm25 import BM25Okapi as _BM25Okapi
            BM25Okapi = _BM25Okapi
        except ImportError as e:
            raise ImportError(
                "ZMM_HYBRID=1 requires the `rank_bm25` package. "
                "Install with: pip install rank-bm25"
            ) from e
        print(f"hybrid:         ENABLED (BM25 + dense RRF, k={RRF_K})")
    else:
        print(f"hybrid:         disabled (dense-only baseline)")

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

            # Step 1b (optional): BM25 retrieve + RRF fuse into dense ranking.
            # Baseline path (ZMM_HYBRID off) skips this entirely so top_indices
            # flow is byte-identical to the pre-hybrid code.
            if ZMM_HYBRID:
                # Per-question BM25 index · the haystack is different per
                # question, matching how sess_embs is built per question.
                bm25_corpus = [_bm25_tokenize(t) for t in sess_texts]
                bm25 = BM25Okapi(bm25_corpus)
                bm25_scores = bm25.get_scores(_bm25_tokenize(question))
                bm25_ranked = sorted(
                    range(len(sess_ids)), key=lambda j: -bm25_scores[j]
                )

                # RRF fusion across dense ranking and BM25 ranking, each
                # truncated to TOP_K_RETRIEVE. Fused score = sum 1/(k + rank).
                dense_top = [idx for idx, _ in sims[:TOP_K_RETRIEVE]]
                bm25_top = bm25_ranked[:TOP_K_RETRIEVE]
                rrf = defaultdict(float)
                for r, idx in enumerate(dense_top):
                    rrf[idx] += 1.0 / (RRF_K + r + 1)
                for r, idx in enumerate(bm25_top):
                    rrf[idx] += 1.0 / (RRF_K + r + 1)
                fused = sorted(rrf.items(), key=lambda kv: -kv[1])
                # Replace sims with fused ranking so the downstream reranker
                # / no-rerank branch reuses the same code path.
                sims = [(idx, score) for idx, score in fused]

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
            if ZMM_SSU_UTTERANCE and qt == "single-session-user":
                context = build_ssu_context(top_sessions, question, reranker=reranker)
            else:
                context = build_context(top_sessions)

            # Step 3+4: Subject LLM answers + Judge LLM scores.
            # ZMM_VOTE=1: single call (baseline, byte-identical to pre-vote).
            # ZMM_VOTE=3: self-consistency · 3 independent subject calls, each
            # judged independently, majority vote wins (tie impossible at n=3).
            if ZMM_RETRIEVAL_ONLY:
                votes = [{"answer": "", "raw_answer": "", "judge_raw": "", "is_correct": False}]
            else:
                prompt_tmpl = pick_subject_prompt(qt)
                votes = []
                for _ in range(ZMM_VOTE):
                    ans, raw, jraw, ok = _run_one_vote(qt, prompt_tmpl, context, question, truth)
                    votes.append({"answer": ans, "raw_answer": raw, "judge_raw": jraw, "is_correct": ok})

            if ZMM_VOTE == 1:
                # Preserve exact baseline field shape
                v = votes[0]
                model_answer = v["answer"]
                raw_answer = v["raw_answer"]
                judge_raw = v["judge_raw"]
                is_correct = v["is_correct"]
            else:
                n_correct = sum(1 for v in votes if v["is_correct"])
                is_correct = n_correct > (len(votes) / 2)
                # Pick a representative answer for the summary log: prefer an
                # answer from the winning side so the logged model_answer
                # matches the logged verdict.
                winners = [v for v in votes if v["is_correct"] == is_correct]
                rep = winners[0] if winners else votes[0]
                model_answer = rep["answer"]
                raw_answer = rep["raw_answer"]
                judge_raw = rep["judge_raw"]

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
                "raw_answer": raw_answer[:800] if qt == "temporal-reasoning" else None,
                "judge_raw": judge_raw[:80],
                "is_correct": is_correct,
                "top_session_ids": [sess_ids[j] for j in top_indices],
                "truth_in_top": any(sess_ids[j] in q.get("answer_session_ids", []) for j in top_indices),
            }
            if ZMM_VOTE > 1:
                entry["votes"] = [
                    {"answer": v["answer"][:300], "judge_raw": v["judge_raw"][:80],
                     "is_correct": v["is_correct"]}
                    for v in votes
                ]
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
        "subject_temperature": SUBJECT_TEMPERATURE,
        "vote_n": ZMM_VOTE,
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
