#!/usr/bin/env python3
"""GPU 真模型验证(非提交·verification-before-completion 证据).

跑 autolab_corpus_retrieve 的默认真后端(bge-m3 dense + bge-reranker-v2-m3)over
一个 DIVERSE 多主题避坑语料,证实它按 query 召回最相关原子(替裸 cat)+ 计时。
裸 cat 会把全部 8 原子塞进 context;检索只挑相关的。
"""
import time
import autolab_corpus_retrieve as r

DIVERSE = """# 避坑语料 · autolab/radix_sort_demo
> 多轮累积避坑(模拟跨主题厚 corpus·裸 cat 会全塞)。

## 平衡警示(本批·最高优先)
⚠️ 平衡警示(批次 4/10 候选破坏正确性): **优化必须先保 bit-exact 正确性,再求加速**。

## 候选避坑
- cand=c_bandwidth.c reward=0.20 median=1.58s [below_reference]: 访存带宽是瓶颈,大数组随机访问导致 cache miss,需访存合并与分块
- cand=c_simd.c reward=0.28 median=1.06s [below_reference]: SIMD 向量化未对齐,需 AVX2 256-bit 对齐加载与水平归约
- cand=c_cacheblock.c reward=0.31 median=0.95s [below_reference]: cache 分块尺寸未匹配 L2,tile 过大导致驱逐,需按 L2 容量调 tile
- cand=c_branch.c reward=0.22 median=1.40s [below_reference]: 分支预测失败率高,排序内层比较分支不可预测,可用无分支 cmov
- cand=c_unroll.c reward=0.19 median=1.62s [below_reference]: 循环未展开,计数桶累加有循环开销,可手工展开 4x
- cand=c_prefetch.c reward=0.24 median=1.30s [below_reference]: 缺软件预取,顺序写桶可 __builtin_prefetch 提前取下一块
- cand=c_build.c reward=0.0 [build_fail]: 编译失败,改动需先过 gcc -O2 编译门
- cand=c_correct.c reward=0.0 [correctness_fail]: 破坏正确性,8-bit 基数截断高位导致输出非完全有序
"""

QUERIES = [
    ("缓解访存带宽瓶颈与 cache miss", {"c_bandwidth.c", "c_cacheblock.c", "c_prefetch.c"}),
    ("SIMD 向量化对齐加载", {"c_simd.c"}),
]

parsed = r.parse_corpus(DIVERSE)
print(f"[parse] balance={len(parsed['balance'])} atoms={len(parsed['atoms'])}")

t0 = time.time()
embed = r._default_embed_fn()
print(f"[load] bge-m3 embedder {time.time()-t0:.1f}s")
t0 = time.time()
rerank = r._default_rerank_fn()
print(f"[load] bge-reranker {time.time()-t0:.1f}s")

for q, expect_top in QUERIES:
    t0 = time.time()
    hits_dense = r.retrieve(q, parsed["atoms"], top_k=3, embed_fn=embed, rerank_fn=None)
    t_dense = time.time() - t0
    t0 = time.time()
    hits_rr = r.retrieve(q, parsed["atoms"], top_k=3, embed_fn=embed, rerank_fn=rerank)
    t_rr = time.time() - t0
    dense_cands = [h["cand"] for h in hits_dense]
    rr_cands = [h["cand"] for h in hits_rr]
    print(f"\n[query] {q}")
    print(f"  dense  top3: {dense_cands}  ({t_dense*1000:.0f}ms)")
    print(f"  rerank top3: {rr_cands}  ({t_rr*1000:.0f}ms)")
    print(f"  expect-relevant ⊇ top1: {rr_cands[0] in expect_top}")

print("\n[grounding sample · cat 替代品]")
print(r.build_grounding(DIVERSE, QUERIES[0][0], top_k=2, embed_fn=embed, rerank_fn=rerank))
