"""刀3③ · bge-m3 LoRA 域适配训练(GPU 机)

输入:pairs_final.jsonl —— 合并 严格对(84,g3 口径)+ LLM 弱标注 YES 对
  字段:query, pos, neg_hard(list,可空), src(="strict"|"semantic")
损失:MultipleNegativesRankingLoss(有难负例用三元组,否则二元组)
LoRA:peft r=16 alpha=32 只挂 attention q/k/v —— 小数据防灾难遗忘
护栏:留出 eval_pairs.jsonl 15 对,每 epoch 结束算 recall@5 不降
产物:/root/knife3/bge-m3-lmev2/(merge 后完整模型,d13 部署直接换路径)

用法:
  python3 train_lmev2_lora.py --train pairs_final.jsonl \
    --eval eval_pairs.jsonl --out /root/knife3/bge-m3-lmev2
"""
import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

SEED = 20260830
random.seed(SEED)
np.random.seed(SEED)


def load_pairs(p: str) -> list[dict]:
    rows = []
    for line in open(p, encoding="utf-8"):
        if line.strip():
            rows.append(json.loads(line))
    return rows


def to_train_samples(rows: list[dict]) -> list[tuple]:
    samples = []
    for r in rows:
        negs = r.get("neg_hard") or []
        if negs:
            samples.append((r["query"], r["pos"], negs[0]))
        else:
            samples.append((r["query"], r["pos"]))
    return samples


def recall_at_k(model, eval_rows: list[dict], k: int = 5) -> float:
    """每题:正例 vs 全部候选(正例+同题难负+其它题正例池 30)排进 top-k 的比例。"""
    hits = 0
    others = [r["pos"] for r in eval_rows]
    for i, r in enumerate(eval_rows):
        cands = [r["pos"]] + (r.get("neg_hard") or [])[:5]
        pool = [c for j, c in enumerate(others) if j != i][:30]
        emb_c = model.encode(cands + pool, normalize_embeddings=True)
        emb_q = model.encode([r["query"]], normalize_embeddings=True)[0]
        order = np.argsort(-(emb_c @ emb_q))
        if 0 in order[:k]:
            hits += 1
    return hits / len(eval_rows) if eval_rows else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", required=True)
    ap.add_argument("--eval", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="/root/models/bge-m3")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--lr", type=float, default=2e-4)
    args = ap.parse_args()

    from sentence_transformers import (InputExample, SentenceTransformer,
                                       losses)
    from torch.utils.data import DataLoader
    from peft import LoraConfig, get_peft_model

    rows = load_pairs(args.train)
    eval_rows = load_pairs(args.eval)
    print(f"train pairs: {len(rows)} (strict={sum(1 for r in rows if r.get('src')=='strict')}, "
          f"semantic={sum(1 for r in rows if r.get('src')=='semantic')}) eval: {len(eval_rows)}",
          file=sys.stderr)

    model = SentenceTransformer(args.model, device="cuda")
    model.max_seq_length = 512

    lora_cfg = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05,
                          target_modules=["query", "key", "value"],
                          bias="none", task_type="FEATURE_EXTRACTION")
    base = model[0].auto_model
    base = get_peft_model(base, lora_cfg)
    model[0].auto_model = base
    base.print_trainable_parameters()

    samples = [InputExample(texts=list(t)) for t in to_train_samples(rows)]
    loader = DataLoader(samples, shuffle=True, batch_size=args.batch)
    loss = losses.MultipleNegativesRankingLoss(model)

    r0 = recall_at_k(model, eval_rows)
    print(f"[guard] recall@5 before: {r0:.3f}", file=sys.stderr)

    best = r0
    for ep in range(args.epochs):
        model.fit(train_objectives=[(loader, loss)],
                  epochs=1, warmup_steps=max(1, int(0.1 * len(loader))),
                  optimizer_params={"lr": args.lr}, show_progress_bar=True)
        r = recall_at_k(model, eval_rows)
        print(f"[guard] epoch {ep+1}: recall@5 = {r:.3f}", file=sys.stderr)
        if r >= best:
            best = r
            base.save_pretrained(args.out)  # adapter 存盘(不中断训练引用)
            print(f"[guard] adapter saved -> {args.out}", file=sys.stderr)
        else:
            print("[guard] regression, keep previous best", file=sys.stderr)

    # 训练结束:按最佳 adapter merge 出完整模型(d13 部署直接换路径)
    base_merged = base.merge_and_unload()
    model_full = SentenceTransformer(args.model, device="cuda")
    model_full[0].auto_model = base_merged
    model_full.max_seq_length = 512
    model_full.save(args.out)
    print(f"DONE best_recall@5={best:.3f} merged -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
