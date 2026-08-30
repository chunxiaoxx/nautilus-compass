"""刀3②c · 合成最终训练对:strict(g3 口径,去 eval 15 对)+ LLM 弱标注 YES 段

输入:
  lmev2_pairs_full_g3.jsonl   84 严格对(eval_pairs.jsonl 里的 question_id 剔除)
  weak_labels.jsonl           弱标注(GPU 机拉回)
  trajectories.jsonl          全轨迹(取段文本用)
输出:pairs_final.jsonl(train)+ stats
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_lmev2_contrastive_pairs import _load_trajectories  # noqa: E402

random.seed(20260830)

BASE = Path("vtf/_compass_lmev2_out")
EVAL_IDS = {json.loads(l)["question_id"] for l in open(BASE / "eval_pairs.jsonl", encoding="utf-8")}

strict_all = [json.loads(l) for l in open(BASE / "lmev2_pairs_full_g3.jsonl", encoding="utf-8") if l.strip()]
strict_train = [r for r in strict_all if r["question_id"] not in EVAL_IDS]
print(f"strict: {len(strict_all)} total, {len(strict_train)} train (eval {len(EVAL_IDS)} held out)")

weak = [json.loads(l) for l in open(BASE / "weak_labels.jsonl", encoding="utf-8") if l.strip()]
print(f"weak labeled questions: {len(weak)}")

trajs = _load_trajectories(BASE / "trajectories.jsonl")

# question_id -> 该题轨迹段列表(与 weak_label 时的顺序一致:haystack_ids 顺序拼接)
ev = {}
for dom in ["compass_web_small", "compass_enterprise_small"]:
    for line in open(BASE / "d12" / dom / "slim.jsonl", encoding="utf-8"):
        r = json.loads(line)
        ev[r["question_id"]] = r

weak_pos = []
for w in weak:
    q = ev.get(w["question_id"])
    if not q:
        continue
    segs = []
    for tid in (q.get("haystack_ids") or []):
        segs.extend(trajs.get(tid, []))
    yes = []
    no = []
    for lab in w.get("labels", []):
        v = lab.get("verdict", "")
        if v.startswith("YES"):
            if lab.get("seg_idx", -2) >= 0:
                yes.append(segs[lab["seg_idx"]])
            elif lab.get("seg_text"):
                yes.append(lab["seg_text"])
        elif v.startswith("NO") and lab.get("seg_idx", -2) >= 0:
            no.append(segs[lab["seg_idx"]])
    if yes:
        weak_pos.append({
            "question_id": w["question_id"],
            "query": q.get("question_text") or "",
            "pos": yes[0][:1200],
            "neg_hard": [n[:1200] for n in no[:2]],
            "gold_len": len(w.get("gold") or ""),
            "pos_source": "llm_weak",
        })

# 去重:weak 与 strict 同 question_id 时跳过 weak(严格对优先)
strict_ids = {r["question_id"] for r in strict_all}
weak_pos = [r for r in weak_pos if r["question_id"] not in strict_ids]

final = strict_train + weak_pos
random.shuffle(final)
with open(BASE / "pairs_final.jsonl", "w", encoding="utf-8") as f:
    for r in final:
        f.write(json.dumps(r, ensure_ascii=False) + "\n")

n_sem = sum(1 for r in final if r.get("pos_source") == "llm_weak")
print(f"weak YES questions: {len(weak_pos)} (deduped from strict)")
print(f"FINAL train pairs: {len(final)} (strict {len(strict_train)} + weak {n_sem})")
