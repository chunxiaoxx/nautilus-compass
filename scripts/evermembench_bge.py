"""compass · EverMemBench end-to-end · BGE-m3 dense + bge-reranker-v2-m3.

Same protocol as paper Table 4: Add → Search → Answer → Evaluate.
Subject + Judge: DeepSeek V4-flash (cheap · same vendor as our LongMemEval pipe).

Default: 1 topic (488 QAs) · ~$0.30 · ~30 min on T4.
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
from huggingface_hub import hf_hub_download
from FlagEmbedding import BGEM3FlagModel
from sentence_transformers import CrossEncoder  # working w/ new transformers

TOPICS = ["01", "02", "03", "04", "05"]   # all topics · stratified
N_QUESTIONS_PER_TOPIC = 100              # 100 per topic = 500 total
TOP_K_RECALL = 100                       # BGE-m3 cosine top-K (was 50)
TOP_K_RERANK = 30                        # reranker output (was 20)
CTX_CHAR_LIMIT = 2500                    # per-message char limit (was 1500)
PER_DAY_MAX = 2                          # day-bucket: max msgs per day in final
QUERY_REWRITE = True                     # paper §3.3 · 3 angles

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY") or sys.exit("set DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
ANSWER_MODEL = os.environ.get("ANSWER_MODEL", "deepseek-v4-pro")  # was v4-flash · pro for accuracy
JUDGE_MODEL  = os.environ.get("JUDGE_MODEL",  "deepseek-v4-flash")  # cheap judge OK


def call_deepseek(model, system, user, max_tokens=200):
    # V4-flash defaults to thinking mode · reasoning_tokens steal budget
    # use non-think for EverMemBench simple Q&A
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
        "reasoning_mode": "non-think",
    }).encode()
    req = urllib.request.Request(DEEPSEEK_URL, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
    }, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                obj = json.loads(r.read())
                return obj["choices"][0]["message"]["content"]
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def expand_indices(s):
    out = []
    for part in str(s).split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-"); out.extend(range(int(a), int(b)+1))
            except ValueError: pass
        else:
            try: out.append(int(part))
            except ValueError: pass
    return out


def flatten_messages(days):
    """Returns: list of (date, group_id, msg_idx, speaker, content)."""
    out = []
    for day in days:
        date = day["date"]
        for group_id, msgs in (day.get("dialogues") or {}).items():
            if not msgs:
                continue
            for idx, m in enumerate(msgs, 1):
                out.append((date, group_id, idx, m["speaker"], m["dialogue"]))
    return out


ANSWER_SYS = (
    "You are a memory-augmented agent answering questions over a "
    "multi-day, multi-party project conversation log.\n"
    "\n"
    "When you receive CONTEXT MESSAGES tagged [DATE GROUP #IDX], reason as follows:\n"
    "1. Identify which speaker / group / day the question targets.\n"
    "2. For multi-step questions, decompose: who · when · what was said.\n"
    "3. For numbers, percentages, dates, or specific names: cite the exact value\n"
    "   from the message that contains it. Do not paraphrase numerical answers.\n"
    "4. For 'after X happened, what was Y?': locate the message describing X,\n"
    "   then look at messages from the same speaker/group AFTER that timestamp.\n"
    "5. Answer concisely: one short sentence or a single value.\n"
    "6. If the retrieved messages do not contain enough information, say UNKNOWN.\n"
    "Do NOT fabricate. Use ONLY the provided messages."
)
JUDGE_SYS = ("Compare PREDICTED to GROUND_TRUTH. Reply CORRECT or INCORRECT only.\n"
             "Semantic equivalence OK (e.g. '65%' = 'sixty-five percent').")

REWRITE_SYS = (
    "You are a query rewriting assistant for memory retrieval over multi-day "
    "project chat logs. Given a question, output exactly 3 lines, each one a "
    "different reformulation that captures different lexical angles:\n"
    "Line 1: Direct restatement (use the original entities verbatim).\n"
    "Line 2: Topic-extracted (the underlying domain/task as a noun phrase).\n"
    "Line 3: Conversational-marker (how someone might say it in chat: 'X said', 'Y mentioned', 'after Z').\n"
    "No numbering, no bullets, no preamble. Just 3 lines."
)


def main():
    print("[init] loading BGE-m3 ...", flush=True)
    bge = BGEM3FlagModel("BAAI/bge-m3", use_fp16=True, device="cuda")
    print("[init] loading bge-reranker-v2-m3 ...", flush=True)
    # Match compass's working setup (sentence_transformers · not FlagReranker)
    rk_path = os.environ.get("ZMM_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3")
    ms_local = Path.home() / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3"
    if ms_local.exists():
        rk_path = str(ms_local)
    rk = CrossEncoder(rk_path, device="cuda")

    overall_total = 0
    overall_correct = 0
    overall_recall_hits = 0
    per_topic = {}
    t0 = time.time()

    for TOPIC in TOPICS:
        qa_path = hf_hub_download("EverMind-AI/EverMemBench-Dynamic",
                                  filename=f"{TOPIC}/qa_{TOPIC}.json",
                                  repo_type="dataset")
        dlg_path = hf_hub_download("EverMind-AI/EverMemBench-Dynamic",
                                   filename=f"{TOPIC}/dialogue.json",
                                   repo_type="dataset")
        qas = json.loads(Path(qa_path).read_text())
        days = json.loads(Path(dlg_path).read_text())

        msgs = flatten_messages(days)
        texts = [f"{m[3]}: {m[4][:CTX_CHAR_LIMIT]}" for m in msgs]
        keys = [(m[0], m[1], m[2]) for m in msgs]
        print(f"[topic {TOPIC}] {len(msgs)} messages · encoding ...", flush=True)

        t_enc = time.time()
        emb = bge.encode(texts, batch_size=64, max_length=256, return_dense=True)["dense_vecs"]
        emb = emb.astype(np.float32)
        print(f"[topic {TOPIC}] encoded in {time.time()-t_enc:.1f}s · shape {emb.shape}", flush=True)

        # normalize for cosine
        emb_norm = emb / (np.linalg.norm(emb, axis=1, keepdims=True) + 1e-9)

        n_correct = 0
        n_total = 0
        n_recall = 0
        qas_iter = qas[:N_QUESTIONS_PER_TOPIC] if N_QUESTIONS_PER_TOPIC else qas
        for qa in qas_iter:
            Q = qa["Q"]; A = qa["A"]
            refs = set()
            for r in qa.get("R", []):
                for idx in expand_indices(r["message_index"]):
                    refs.add((r["date"], r["group"], idx))
            if not refs:
                continue

            # ---- Query rewriting (paper §3.3 · 3 angles) ----
            queries = [Q]
            if QUERY_REWRITE:
                try:
                    rewritten = call_deepseek("deepseek-v4-flash", REWRITE_SYS, Q, 256)
                    extra = [ln.strip() for ln in rewritten.splitlines() if ln.strip()][:3]
                    queries = [Q] + extra if extra else [Q]
                except Exception:
                    pass  # fall back to single Q on rewrite fail

            # ---- Multi-angle BGE retrieval · union dedup ----
            q_embs = bge.encode(queries, return_dense=True)["dense_vecs"].astype(np.float32)
            q_embs = q_embs / (np.linalg.norm(q_embs, axis=1, keepdims=True) + 1e-9)
            # Per-angle top-K_RECALL · union
            cand_set = set()
            for q_e in q_embs:
                sims_a = emb_norm @ q_e
                t_a = np.argpartition(-sims_a, TOP_K_RECALL)[:TOP_K_RECALL]
                cand_set.update(int(i) for i in t_a)
            top_idx = np.array(sorted(cand_set))

            # ---- Rerank candidates with cross-encoder · score by Q (orig) ----
            pairs = [[Q, texts[i]] for i in top_idx]
            scores = rk.predict(pairs, batch_size=32, show_progress_bar=False)
            scored = sorted(zip(scores, top_idx), key=lambda x: -x[0])

            # ---- Day-bucket: max PER_DAY_MAX per (date) in final top ----
            day_count = {}
            final_idx = []
            for sc, idx in scored:
                date = msgs[idx][0]
                if day_count.get(date, 0) >= PER_DAY_MAX:
                    continue
                day_count[date] = day_count.get(date, 0) + 1
                final_idx.append(int(idx))
                if len(final_idx) >= TOP_K_RERANK:
                    break

            retrieved_keys = [keys[i] for i in final_idx]
            if any(rk_ in refs for rk_ in retrieved_keys):
                n_recall += 1

            ctx_lines = []
            for i in final_idx:
                d, g, ix, sp, ct = msgs[i]
                ctx_lines.append(f"[{d} {g} #{ix}] {sp}: {ct[:CTX_CHAR_LIMIT]}")
            ctx = "\n".join(ctx_lines)
            user_msg = f"CONTEXT MESSAGES:\n{ctx}\n\nQUESTION: {Q}\n\nANSWER:"

            try:
                # V4-pro think-high uses ~500-1500 reasoning_tokens · budget generously
                pred = call_deepseek(ANSWER_MODEL, ANSWER_SYS, user_msg, 2048).strip()
            except Exception as e:
                print(f"  [skip {qa['id']}] answer fail: {e}", flush=True)
                continue
            try:
                verdict = call_deepseek(JUDGE_MODEL, JUDGE_SYS,
                    f"PREDICTED: {pred}\nGROUND_TRUTH: {A}\nVerdict:", 512).strip().upper()
            except Exception as e:
                print(f"  [skip {qa['id']}] judge fail: {e}", flush=True)
                continue

            ok = "CORRECT" in verdict and "INCORRECT" not in verdict
            if ok:
                n_correct += 1
            n_total += 1
            if n_total % 10 == 0:
                acc = n_correct/n_total*100
                rec = n_recall/n_total*100
                el = time.time() - t0
                print(f"  [{TOPIC} {n_total}/{N_QUESTIONS_PER_TOPIC or len(qas)}] "
                      f"acc={acc:.1f} recall@{TOP_K_RERANK}={rec:.1f} · {el:.0f}s",
                      flush=True)

        per_topic[TOPIC] = (n_correct, n_total, n_recall)
        overall_correct += n_correct
        overall_total += n_total
        overall_recall_hits += n_recall

    print()
    print("=" * 60)
    print("compass BGE-m3 + bge-reranker-v2-m3 + DeepSeek V4-flash")
    print("=" * 60)
    for TOPIC, (c, t, r) in per_topic.items():
        if t > 0:
            print(f"topic {TOPIC} · n={t} · recall@{TOP_K_RERANK}={r/t*100:.1f}% · acc={c/t*100:.1f}%")
    if overall_total > 0:
        print("-" * 60)
        print(f"OVERALL  n={overall_total} · "
              f"recall@{TOP_K_RERANK}={overall_recall_hits/overall_total*100:.1f}% · "
              f"acc={overall_correct/overall_total*100:.1f}%")
    print(f"elapsed: {time.time()-t0:.0f}s")
    print()
    print("paper Table 4 (gpt-4.1-mini answerer · 9-subtask Average):")
    print("  Full Context 37.44  + MemoBase 34.27  + Mem0 37.09")
    print("  + Zep 39.97  + MemOS 42.55  + EverCore NOT REPORTED")


if __name__ == "__main__":
    main()
