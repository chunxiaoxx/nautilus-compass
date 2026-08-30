"""刀3② · 语义转述对齐扩对(gpu 机跑,bge-m3 encode)

背景:精确 substring 对齐 56 对是结构上限(gold 未必逐字在 agent 轨迹里——
标注答案基于完整环境写,轨迹只是部分浏览记录)。本脚本用 bge-m3 语义
相似度找"gold 的转述段"做弱标注正例。

设计:
- 段文本构造与 build_lmev2_contrastive_pairs.py 同款(_state_text 500/1200),
  防 train/serve skew。
- 对非abst、gold>=5 有效字符、且精确对齐失败的题:
  cos(gold, seg) 对该题引用轨迹的全部段打分,输出 top1 + 分布。
- 输出全量分布 JSONL(阈值不硬编码,人工抽验后本地定档)。

用法(gpu 机):
  python3 semantic_align_pairs.py \
    --evidence evidence_web.jsonl:evidence_ent.jsonl \
    --trajectories /root/LongMemEval-V2/data/longmemeval-v2/trajectories.jsonl \
    --out /root/knife3/semantic_scores.jsonl
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_lmev2_contrastive_pairs import _load_trajectories, _norm  # noqa: E402


def _valid_gold(gold: str, min_len: int = 5) -> bool:
    g = _norm(gold)
    if not g or len(g) < min_len:
        return False
    # bool 字面不参与(与精确对齐同口径)
    if g in ("true", "false"):
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--evidence", required=True,
                    help="逗号分隔的 slim evidence jsonl 路径")
    ap.add_argument("--trajectories", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=256)
    args = ap.parse_args()

    rows = []
    for p in args.evidence.split(","):
        for line in open(p.strip(), encoding="utf-8"):
            if line.strip():
                rows.append(json.loads(line))
    print(f"evidence rows: {len(rows)}", file=sys.stderr)

    trajs = _load_trajectories(Path(args.trajectories))
    print(f"trajectories: {len(trajs)}", file=sys.stderr)

    # 只 encode 被引轨迹的段
    need_tids = set()
    for r in rows:
        need_tids.update(r.get("haystack_ids") or [])
    segs: dict[str, list[str]] = {}
    for tid in need_tids:
        if tid in trajs:
            segs[tid] = trajs[tid]
    all_segs = [s for v in segs.values() for s in v]
    seg_owner: list[str] = []
    for tid, v in segs.items():
        seg_owner.extend([tid] * len(v))
    print(f"segments to encode: {len(all_segs)}", file=sys.stderr)

    import sentence_transformers as st_model

    model = st_model.SentenceTransformer(
        "/root/models/bge-m3", device="cuda")
    model.max_seq_length = 512
    seg_emb = model.encode(all_segs, batch_size=args.batch,
                           show_progress_bar=True, normalize_embeddings=True)
    print(f"seg_emb: {seg_emb.shape}", file=sys.stderr)

    # 精确对齐口径复现(判定 not_found)

    out = open(args.out, "w", encoding="utf-8")
    n_done = 0
    for r in rows:
        if r.get("is_abstention_problem"):
            continue
        gold = r.get("answer_gold") or ""
        if not _valid_gold(gold):
            continue
        g_norm = _norm(gold)
        exact = any(g_norm in _norm(s)
                    for tid in (r.get("haystack_ids") or [])
                    for s in segs.get(tid, []))
        if exact:
            continue  # 精确对齐已覆盖,不重复出对
        q_emb = model.encode([f"Question: {r.get('question_text') or ''}"],
                             normalize_embeddings=True)[0]
        g_emb = model.encode([gold], normalize_embeddings=True)[0]
        import numpy as np

        cand_idx = [i for i, t in enumerate(seg_owner)
                    if t in set(r.get("haystack_ids") or [])]
        if not cand_idx:
            continue
        sub = seg_emb[cand_idx]
        cos_g = sub @ g_emb
        cos_q = sub @ q_emb
        top = int(cos_g.argmax())
        out.write(json.dumps({
            "question_id": r["question_id"],
            "category": r.get("category"),
            "gold": gold[:200],
            "top_seg": all_segs[cand_idx[top]][:400],
            "cos_gold_seg": float(cos_g[top]),
            "cos_query_seg": float(cos_q[top]),
            "n_cand": len(cand_idx),
        }, ensure_ascii=False) + "\n")
        n_done += 1
        if n_done % 20 == 0:
            print(f"scored {n_done}", file=sys.stderr)
    out.close()
    print(f"DONE scored={n_done}", file=sys.stderr)


if __name__ == "__main__":
    main()
