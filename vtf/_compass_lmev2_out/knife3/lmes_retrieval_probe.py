"""刀3④ 前置 · LME-S 检索回归代理(GPU 机,零 LLM 成本)

e2e overall(0.567 基线)需 ARK reader/judge;ARK 欠费期间先用纯检索代理
提前探测 LoRA 域适配是否伤害 LME-S 对话域检索(灾难遗忘先行信号)。

每题:question 为 query,各 haystack session(拼接,截 2000 字符)为候选。
指标:recall@8(答案 session 进 top8)· overlap@8(两模型 top8 交集)。
口径:stride 采样 100 题;非正式判据,ARK 恢复后仍跑正式 e2e 回归。

用法(GPU 机):python3 lmes_retrieval_probe.py > /tmp/lmes_probe.out 2>&1
"""
import json

from sentence_transformers import SentenceTransformer

SAMPLE_STRIDE = 5  # 500 题 -> 100 题


def build_rows(path: str) -> list:
    data = json.load(open(path))
    rows = []
    for r in data[::SAMPLE_STRIDE]:
        sess_texts = [" ".join(t["content"] for t in sess)[:2000]
                      for sess in r["haystack_sessions"] if sess]
        sess_ids = r["haystack_session_ids"] or []
        ans = set(r["answer_session_ids"] or [])
        labels = [1 if sid in ans else 0 for sid in sess_ids[:len(sess_texts)]]
        if not sess_texts or not any(labels):
            continue
        rows.append((r["question"], sess_texts, labels))
    return rows


def run(rows: list) -> None:
    base = SentenceTransformer("/root/models/bge-m3", device="cuda")
    base.max_seq_length = 512
    merged = SentenceTransformer("/root/knife3/bge-m3-lmev2", device="cuda")
    merged.max_seq_length = 512

    base_ranks, merged_ranks = [], []
    for name, m, store in (("base", base, base_ranks), ("merged", merged, merged_ranks)):
        hits = 0
        for q, texts, labels in rows:
            E = m.encode(texts, normalize_embeddings=True, batch_size=32)
            Q = m.encode([q], normalize_embeddings=True)[0]
            top = (E @ Q).argsort()[::-1][:8].tolist()
            hits += 1 if any(labels[i] for i in top) else 0
            store.append(top)
        print(f"[{name}] recall@8 = {hits/len(rows):.3f}", flush=True)

    ov = sum(len(set(a) & set(b)) / 8 for a, b in zip(base_ranks, merged_ranks)) / len(rows)
    print(f"overlap@8 = {ov:.3f}  (n={len(rows)})", flush=True)


if __name__ == "__main__":
    rows = build_rows("/root/e2e/.cache/longmem_s.json")
    print(f"probe rows: {len(rows)}", flush=True)
    run(rows)
