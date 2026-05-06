"""compass · EverMemBench-Dynamic smoke · BM25 baseline (SQLite FTS5).

Lower-bound baseline · no BGE-m3 dense · no reranker (T4 GPU busy with V4).
Real compass uses BGE-m3 + bge-reranker-v2-m3.
"""
import json
import sqlite3
from pathlib import Path
from huggingface_hub import hf_hub_download

TOPICS = ["01", "02", "03", "04", "05"]
N_QUESTIONS = None  # None = all
TOP_K_LIST = [1, 5, 10, 20]

all_topics = []  # list of (topic_id, qas, days)
for TOPIC in TOPICS:
    qar_path = hf_hub_download("EverMind-AI/EverMemBench-Dynamic",
                               filename=f"{TOPIC}/qa_{TOPIC}.json", repo_type="dataset")
    dlg_path = hf_hub_download("EverMind-AI/EverMemBench-Dynamic",
                               filename=f"{TOPIC}/dialogue.json", repo_type="dataset")
    qas = json.loads(Path(qar_path).read_text())
    days = json.loads(Path(dlg_path).read_text())
    all_topics.append((TOPIC, qas, days))

def expand_indices(s):
    out = []
    for part in str(s).split(","):
        part = part.strip()
        if "-" in part:
            try:
                a, b = part.split("-")
                out.extend(range(int(a), int(b) + 1))
            except ValueError:
                pass
        else:
            try:
                out.append(int(part))
            except ValueError:
                pass
    return out

overall_hits = {k: 0 for k in TOP_K_LIST}
overall_total = 0
per_topic = {}

for TOPIC, qas, days in all_topics:
    db_path = f"/tmp/evermembench_{TOPIC}.db"
    Path(db_path).unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.execute(
        "CREATE VIRTUAL TABLE messages USING fts5("
        "msg_id UNINDEXED, date UNINDEXED, group_id UNINDEXED, msg_idx UNINDEXED, "
        "speaker, content)"
    )
    n_msgs = 0
    for day in days:
        date = day["date"]
        for group_id, msgs in (day.get("dialogues") or {}).items():
            if not msgs:
                continue
            for idx, m in enumerate(msgs, start=1):
                con.execute(
                    "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
                    (f"{date}|{group_id}|{idx}", date, group_id, idx,
                     m["speaker"], m["dialogue"])
                )
                n_msgs += 1
    con.commit()
    print(f"[topic {TOPIC}] {n_msgs} messages, {len(days)} days, {len(qas)} QAs")

    hits_at = {k: 0 for k in TOP_K_LIST}
    total = 0
    qas_iter = qas if N_QUESTIONS is None else qas[:N_QUESTIONS]
    import re as _re
    STOPWORDS = {"the","what","was","during","when","why","how","who","which",
                 "after","before","this","that","these","those","with","from",
                 "into","there","here","then","than","also","were","been","being",
                 "for","and","but","not","can","did","does","done"}
    for qa in qas_iter:
        Q = qa["Q"]
        refs = set()
        for r in qa.get("R", []):
            for idx in expand_indices(r["message_index"]):
                refs.add((r["date"], r["group"], idx))
        if not refs:
            continue
        tokens = [t.lower() for t in _re.findall(r"[A-Za-z0-9]+", Q)
                  if len(t) > 2 and t.lower() not in STOPWORDS]
        if not tokens:
            continue
        safe_q = " OR ".join(tokens[:8])
        try:
            cur = con.execute(
                "SELECT date, group_id, msg_idx FROM messages "
                "WHERE messages MATCH ? ORDER BY rank LIMIT ?",
                (safe_q, max(TOP_K_LIST))
            )
            retrieved = [(r[0], r[1], r[2]) for r in cur.fetchall()]
        except sqlite3.OperationalError:
            continue
        for k in TOP_K_LIST:
            if any(hit in refs for hit in retrieved[:k]):
                hits_at[k] += 1
        total += 1

    per_topic[TOPIC] = (hits_at, total)
    for k in TOP_K_LIST:
        overall_hits[k] += hits_at[k]
    overall_total += total
    con.close()

print()
print("=" * 60)
print("BM25 baseline · EverMemBench-Dynamic · all 5 topics")
print("=" * 60)
print(f"{'topic':<8} {'n':<5} " + " ".join(f"R@{k:<3}" for k in TOP_K_LIST))
for TOPIC in TOPICS:
    h, t = per_topic[TOPIC]
    row = f"{TOPIC:<8} {t:<5} " + " ".join(f"{h[k]/max(1,t)*100:5.1f}" for k in TOP_K_LIST)
    print(row)
row = f"{'OVERALL':<8} {overall_total:<5} " + " ".join(f"{overall_hits[k]/max(1,overall_total)*100:5.1f}" for k in TOP_K_LIST)
print("-" * 60)
print(row)
print()
print("compare to paper Table 4 (GPT-4.1-mini answerer · Single-hop only):")
print("  + MemoBase: 60.09  + Mem0: 55.40  + Zep: 73.71  + MemOS: 71.36")
print("  EverCore: NOT REPORTED in original paper")
