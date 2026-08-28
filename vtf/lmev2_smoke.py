"""LME-V2 compass backend smoke test — real question + 5 real trajectories."""
import json
import sys
import time

sys.path.insert(0, "/home/ubuntu/LongMemEval-V2")
from memory_modules.memory import build_memory  # noqa: E402

ROOT = "/home/ubuntu/LongMemEval-V2/data/longmemeval-v2"

qs = [json.loads(l) for l in open(f"{ROOT}/questions.jsonl")]
trajs = {}
with open(f"{ROOT}/trajectories.jsonl") as f:
    for l in f:
        t = json.loads(l)
        trajs[t["id"]] = t

hay = json.load(open(f"{ROOT}/haystacks/lme_v2_small.json"))
q = qs[0]
pool_ids = hay[q["id"]][:5]
print(f"question {q['id']} domain={q['domain']} type={q['question_type']}")
print(f"pool: {len(pool_ids)} trajs (smoke: 5), total dataset {len(qs)} q / {len(trajs)} trajs")
print(f"Q: {q['question'][:120]}")
print(f"gold: {str(q.get('answer'))[:200]}")

m = build_memory(
    {"memory_type": "compass_chunk_hybrid", "memory_params": {"device": "cpu"}}
)
t0 = time.time()
for tid in pool_ids:
    m.insert(trajs[tid])
print(f"insert 5 trajs: {time.time()-t0:.1f}s, chunks={len(m._chunks)}")

t0 = time.time()
items = m.query(q["question"])
print(f"query: {time.time()-t0:.1f}s -> {len(items)} items")
for it in items[:4]:
    v = it["value"]
    print("-", it["type"], f"({len(v)}ch)", v[:140].replace("\n", " "))
print("SMOKE_OK")
