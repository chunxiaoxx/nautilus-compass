"""刀3②b · LLM 弱标注绕开 embedder 域差距(cos 判据被域差距压制,天花板 0.73)

输入:semantic_scores.jsonl(cos 排序已在)+ 全轨迹
每题候选:cos top-10 ∪ lexical top-10(≤12 段),doubao 逐段判:
  "该段是否包含得出答案所需的信息" → YES / NO
输出:weak_labels.jsonl 供本地合成训练对。

用法(gpu 机,ARK key inline):
  ARK_API_KEY=xxx python3 llm_weak_label.py \
    --scores /root/knife3/semantic_scores.jsonl \
    --trajectories /root/LongMemEval-V2/data/longmemeval-v2/trajectories.jsonl \
    --evidence /root/knife3/evidence_web.jsonl,/root/knife3/evidence_ent.jsonl \
    --out /root/knife3/weak_labels.jsonl
"""
import argparse
import json
import os
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_lmev2_contrastive_pairs import _load_trajectories, _norm  # noqa: E402

BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MODEL = "doubao-seed-2-0-pro-260215"

PROMPT = """You are building training data for a retrieval model.

Question: {q}

Standard answer (gold): {g}

Candidate snippet (from an agent's browsing trajectory):
---
{s}
---

Does this snippet contain the information needed to derive the standard answer?
Reply with exactly one word: YES, NO, or PARTIAL."""


def call_llm(text: str, key: str, max_retry: int = 4) -> str:
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": text}],
        "max_tokens": 8,
        "temperature": 0,
    }).encode()
    last = None
    for i in range(max_retry):
        try:
            req = urllib.request.Request(
                f"{BASE_URL}/chat/completions", data=body,
                headers={"Content-Type": "application/json",
                         "Authorization": f"Bearer {key}"})
            r = urllib.request.urlopen(req, timeout=60)
            c = json.loads(r.read())["choices"][0]["message"]["content"]
            if c and c.strip():
                return c.strip().upper()[:10]
            last = ValueError("empty content")
        except Exception as e:  # noqa: BLE001
            last = e
        time.sleep(3 * (i + 1))
    raise last  # type: ignore[misc]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scores", required=True)
    ap.add_argument("--trajectories", required=True)
    ap.add_argument("--evidence", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--topk", type=int, default=10)
    args = ap.parse_args()

    key = os.environ.get("ARK_API_KEY")
    if not key:
        sys.exit("ARK_API_KEY not set")

    ev = {}
    for p in args.evidence.split(","):
        for line in open(p.strip(), encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                ev[r["question_id"]] = r

    scores = [json.loads(l) for l in open(args.scores, encoding="utf-8")]
    print(f"scored questions: {len(scores)}", file=sys.stderr)

    trajs = _load_trajectories(Path(args.trajectories))

    # 烟测:1 次真实调用
    t0 = time.time()
    smoke = call_llm("Reply with exactly one word YES.", key)
    print(f"smoke: {smoke} ({time.time()-t0:.1f}s)", file=sys.stderr)

    jobs = []
    for s in scores:
        q = ev.get(s["question_id"])
        if not q:
            continue
        segs: list[str] = []
        for tid in (q.get("haystack_ids") or []):
            segs.extend(trajs.get(tid, []))
        if not segs:
            continue
        # lexical 排序(词面重叠);cos top1 段文本单独并入候选
        qtok = set(re.findall(r"[a-z0-9]{3,}", (q.get("question_text") or "").lower()))
        gtok = set(w for w in re.findall(r"[a-z0-9]{3,}", s["gold"].lower()) if len(w) >= 3)
        ranked = sorted(
            range(len(segs)),
            key=lambda i: -(len(qtok & set(re.findall(r"[a-z0-9]{3,}", segs[i].lower())))
                            + len(gtok & set(re.findall(r"[a-z0-9]{3,}", segs[i].lower())))))
        lex_top = set(ranked[:args.topk])
        cos_top_text = s.get("top_seg") or ""
        jobs.append((q, s, segs, lex_top, cos_top_text))

    print(f"questions to label: {len(jobs)}", file=sys.stderr)

    def work(job):
        q, s, segs, lex_top, cos_top_text = job
        results = []
        for i in sorted(lex_top):
            try:
                v = call_llm(PROMPT.format(
                    q=(q.get("question_text") or "")[:600],
                    g=s["gold"][:300], s=segs[i][:1500]), key)
            except Exception as e:  # noqa: BLE001
                v = f"ERR:{e}"
            results.append({"seg_idx": i, "verdict": v})
        if cos_top_text:
            try:
                v = call_llm(PROMPT.format(
                    q=(q.get("question_text") or "")[:600],
                    g=s["gold"][:300], s=cos_top_text[:1500]), key)
            except Exception as e:  # noqa: BLE001
                v = f"ERR:{e}"
            results.append({"seg_idx": -1, "seg_text": cos_top_text[:1500],
                            "verdict": v, "src": "cos_top1"})
        return {"question_id": q["question_id"], "category": q.get("category"),
                "gold": s["gold"][:300], "labels": results}

    done = 0
    with open(args.out, "w", encoding="utf-8") as out, \
            ThreadPoolExecutor(max_workers=args.workers) as ex:
        for res in ex.map(work, jobs):
            out.write(json.dumps(res, ensure_ascii=False) + "\n")
            out.flush()
            done += 1
            if done % 20 == 0:
                print(f"labeled {done}/{len(jobs)}", file=sys.stderr)
    print(f"DONE {done}", file=sys.stderr)


if __name__ == "__main__":
    main()
