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

TOPICS = ["01"]
N_QUESTIONS_PER_TOPIC = 100              # smoke first · increase later
TOP_K_RECALL = 50                        # BGE-m3 cosine top-K
TOP_K_RERANK = 20                        # reranker output

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY") or sys.exit("set DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
ANSWER_MODEL = "deepseek-v4-flash"
JUDGE_MODEL  = "deepseek-v4-flash"


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


ANSWER_SYS = ("You are a memory-augmented agent. Answer the user's question "
              "concisely (one short sentence or value). Use ONLY the provided "
              "messages as context. If the answer is not found, say UNKNOWN.")
JUDGE_SYS = ("Compare PREDICTED to GROUND_TRUTH. Reply CORRECT or INCORRECT only.\n"
             "Semantic equivalence OK (e.g. '65%' = 'sixty-five percent').")


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
        texts = [f"{m[3]}: {m[4][:1500]}" for m in msgs]
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

            q_emb = bge.encode([Q], return_dense=True)["dense_vecs"][0].astype(np.float32)
            q_emb = q_emb / (np.linalg.norm(q_emb) + 1e-9)
            sims = emb_norm @ q_emb
            top_idx = np.argpartition(-sims, TOP_K_RECALL)[:TOP_K_RECALL]
            top_idx = top_idx[np.argsort(-sims[top_idx])]

            # rerank top-K_RECALL with cross-encoder, take top-K_RERANK
            pairs = [[Q, texts[i]] for i in top_idx]
            scores = rk.predict(pairs, batch_size=32, show_progress_bar=False)
            order = np.argsort(-np.asarray(scores))[:TOP_K_RERANK]
            final_idx = [int(top_idx[i]) for i in order]

            retrieved_keys = [keys[i] for i in final_idx]
            if any(rk_ in refs for rk_ in retrieved_keys):
                n_recall += 1

            ctx_lines = []
            for i in final_idx:
                d, g, ix, sp, ct = msgs[i]
                ctx_lines.append(f"[{d} {g} #{ix}] {sp}: {ct[:1500]}")
            ctx = "\n".join(ctx_lines)
            user_msg = f"CONTEXT MESSAGES:\n{ctx}\n\nQUESTION: {Q}\n\nANSWER:"

            try:
                pred = call_deepseek(ANSWER_MODEL, ANSWER_SYS, user_msg, 1024).strip()
            except Exception as e:
                print(f"  [skip {qa['id']}] answer fail: {e}", flush=True)
                continue
            try:
                verdict = call_deepseek(JUDGE_MODEL, JUDGE_SYS,
                    f"PREDICTED: {pred}\nGROUND_TRUTH: {A}\nVerdict:", 256).strip().upper()
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
