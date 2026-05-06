"""compass · EverMemBench end-to-end · BM25 retrieve + DeepSeek answer + judge.

Mirrors paper Table 4 protocol (retrieve top-K · LLM answers · LLM judges)
but uses DeepSeek V4-flash (cheap · fast · cross-judge 88.6% w/ gemini in our paper).

Cost: 100 QAs × 2 calls × ~3-4K tokens ≈ $0.10 on DeepSeek V4-flash.
"""
import json
import os
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path
from huggingface_hub import hf_hub_download

TOPICS = ["01"]                     # smoke: 1 topic
N_QUESTIONS_PER_TOPIC = 100
TOP_K = 20

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY") or sys.exit("set DEEPSEEK_API_KEY")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
ANSWER_MODEL = "deepseek-v4-flash"
JUDGE_MODEL  = "deepseek-v4-flash"

import re as _re
STOPWORDS = {"the","what","was","during","when","why","how","who","which",
             "after","before","this","that","these","those","with","from",
             "into","there","here","then","than","also","were","been","being",
             "for","and","but","not","can","did","does","done"}


def call_deepseek(model: str, system: str, user: str, max_tokens: int = 300) -> str:
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0,
        "max_tokens": max_tokens,
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


def build_fts(topic: str, days: list) -> sqlite3.Connection:
    db = f"/tmp/em_{topic}.db"
    Path(db).unlink(missing_ok=True)
    con = sqlite3.connect(db)
    con.execute(
        "CREATE VIRTUAL TABLE messages USING fts5("
        "msg_id UNINDEXED, date UNINDEXED, group_id UNINDEXED, msg_idx UNINDEXED, "
        "speaker, content)"
    )
    for day in days:
        date = day["date"]
        for group_id, msgs in (day.get("dialogues") or {}).items():
            if not msgs: continue
            for idx, m in enumerate(msgs, 1):
                con.execute(
                    "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
                    (f"{date}|{group_id}|{idx}", date, group_id, idx,
                     m["speaker"], m["dialogue"]))
    con.commit()
    return con


def bm25_top_k(con, Q: str, k: int) -> list:
    tokens = [t.lower() for t in _re.findall(r"[A-Za-z0-9]+", Q)
              if len(t) > 2 and t.lower() not in STOPWORDS]
    if not tokens: return []
    safe_q = " OR ".join(tokens[:8])
    try:
        cur = con.execute(
            "SELECT date, group_id, msg_idx, speaker, content FROM messages "
            "WHERE messages MATCH ? ORDER BY rank LIMIT ?", (safe_q, k))
        return cur.fetchall()
    except sqlite3.OperationalError:
        return []


def format_context(rows: list) -> str:
    lines = []
    for r in rows:
        date, gid, idx, speaker, content = r
        lines.append(f"[{date} {gid} #{idx}] {speaker}: {content[:300]}")
    return "\n".join(lines)


ANSWER_SYS = ("You are a memory-augmented agent. Answer the user's question "
              "concisely (one short sentence or value). Use ONLY the provided "
              "messages as context. If the answer is not found, say UNKNOWN.")
JUDGE_SYS  = ("You are a strict evaluator. Compare PREDICTED to GROUND_TRUTH. "
              "Reply with exactly one token: CORRECT or INCORRECT.\n"
              "Semantic equivalence is OK (e.g. '65%' = 'sixty-five percent'). "
              "Numeric tolerance: exact for integers, 5%% relative for floats.")


def main():
    total = 0; correct = 0; recall_hit = 0
    t0 = time.time()
    for TOPIC in TOPICS:
        qa_path = hf_hub_download("EverMind-AI/EverMemBench-Dynamic",
                                  filename=f"{TOPIC}/qa_{TOPIC}.json", repo_type="dataset")
        dlg_path = hf_hub_download("EverMind-AI/EverMemBench-Dynamic",
                                   filename=f"{TOPIC}/dialogue.json", repo_type="dataset")
        qas = json.loads(Path(qa_path).read_text())
        days = json.loads(Path(dlg_path).read_text())
        con = build_fts(TOPIC, days)
        print(f"[topic {TOPIC}] {len(qas)} QAs · BM25 ready", flush=True)

        for qa in qas[:N_QUESTIONS_PER_TOPIC]:
            Q = qa["Q"]; A = qa["A"]
            refs = set()
            for r in qa.get("R", []):
                for idx in expand_indices(r["message_index"]):
                    refs.add((r["date"], r["group"], idx))
            if not refs: continue

            rows = bm25_top_k(con, Q, TOP_K)
            retrieved_keys = [(r[0], r[1], r[2]) for r in rows]
            if any(rk in refs for rk in retrieved_keys):
                recall_hit += 1

            ctx = format_context(rows) or "(no messages retrieved)"
            user_msg = f"CONTEXT MESSAGES:\n{ctx}\n\nQUESTION: {Q}\n\nANSWER:"
            try:
                pred = call_deepseek(ANSWER_MODEL, ANSWER_SYS, user_msg, 200).strip()
            except Exception as e:
                print(f"  [skip {qa['id']}] answer fail: {e}", flush=True)
                continue

            judge_msg = f"PREDICTED: {pred}\nGROUND_TRUTH: {A}\nVerdict:"
            try:
                verdict = call_deepseek(JUDGE_MODEL, JUDGE_SYS, judge_msg, 8).strip().upper()
            except Exception as e:
                print(f"  [skip {qa['id']}] judge fail: {e}", flush=True)
                continue

            ok = "CORRECT" in verdict and "INCORRECT" not in verdict
            if ok: correct += 1
            total += 1
            if total % 10 == 0:
                acc = correct/total*100
                rec = recall_hit/total*100
                el = time.time() - t0
                print(f"  [{total}/{N_QUESTIONS_PER_TOPIC}] acc={acc:.1f} recall@{TOP_K}={rec:.1f} · {el:.0f}s", flush=True)
        con.close()

    print()
    print("=" * 60)
    print("compass BM25 + DeepSeek V4-flash · EverMemBench-Dynamic")
    print("=" * 60)
    print(f"n           : {total}")
    print(f"recall@{TOP_K}    : {recall_hit/max(1,total)*100:.1f}%")
    print(f"e2e accuracy: {correct/max(1,total)*100:.1f}%")
    print(f"elapsed     : {time.time()-t0:.0f}s")
    print()
    print("paper Table 4 (GPT-4.1-mini · Single+Multi+Temp avg):")
    print("  Full Context : 30.99%   + MemoBase: 30.31%")
    print("  + Mem0       : 24.32%   + Zep    : 31.58%")
    print("  + MemOS      : 35.30%")


if __name__ == "__main__":
    main()
