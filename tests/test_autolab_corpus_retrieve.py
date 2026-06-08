"""RSI grounded-retrieval · A 簇避坑语料语义检索(替裸 cat).

`ops/autolab_corpus_retrieve` turns the bare `autolab_avoid_<task>.md` corpus
(currently `cat`'d wholesale into the producer's round-2 grounded arm) into a
query-driven retrieve over compass's bge-m3 + bge-reranker-v2-m3 stack. Given the
producer's optimization sub-goal as a query, it returns only the MOST relevant
avoid-atoms — and ALWAYS keeps the batch balance-warning (correctness-first), the
meta-lesson that retrieval must never drop.

Turf: compass owns the retrieve + corpus; V5's producer owns inject. The
embed/rerank backend is injected so CI stays compass-only (NO model, NO LLM here);
the real bge-m3 + reranker path is verified on the GPU separately.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from ops import autolab_corpus_retrieve as r  # noqa: E402


CORPUS = """# 避坑语料 · autolab/radix_sort(compass·RSI grounded-retrieval 用)
> round-N eval 失败/低分原因 → producer 下轮 grounded 臂 retrieve 注入。

## 平衡警示(本批·最高优先)
⚠️ 平衡警示(批次 4/10 候选破坏正确性): **优化必须先保 bit-exact 正确性,再求加速**。

## 候选避坑
- cand=c_bandwidth.c reward=0.20 median=1.58s [below_reference]: 远低于 reference,访存带宽是瓶颈,需访存合并/cache 分块
- cand=c_simd.c reward=0.28 median=1.06s [below_reference]: SIMD 向量化未对齐,需 256-bit AVX 对齐加载
- cand=c_build.c reward=0.0 [build_fail]: 编译失败,改动需先过 gcc -O2 编译门
- cand=c_correct.c reward=0.0 [correctness_fail]: 破坏正确性,输出非完全有序
"""


# ── stub backend (deterministic · no model) ─────────────────────────────────
def _embed(text: str):
    """3-dim bag vector: [bandwidth, simd, build]. Lets tests assert dense order."""
    t = text.lower()
    return [
        float(t.count("带宽") + t.count("bandwidth") + t.count("访存")),
        float(t.count("simd") + t.count("向量") + t.count("avx")),
        float(t.count("编译") + t.count("build") + t.count("gcc")),
    ]


# ── RED 1 · parse splits balance-warning from candidate atoms ────────────────
def test_parse_separates_balance_and_candidate_atoms():
    parsed = r.parse_corpus(CORPUS)

    assert len(parsed["balance"]) == 1
    assert "bit-exact" in parsed["balance"][0]
    # four candidate atoms, with tag + cand preserved
    cands = {a["cand"]: a for a in parsed["atoms"]}
    assert set(cands) == {"c_bandwidth.c", "c_simd.c", "c_build.c", "c_correct.c"}
    assert cands["c_build.c"]["tag"] == "build_fail"
    assert cands["c_bandwidth.c"]["reward"] == 0.20


# ── RED 2 · retrieve orders candidate atoms by dense cosine to the query ─────
def test_retrieve_ranks_relevant_atom_first_by_dense():
    parsed = r.parse_corpus(CORPUS)
    # query about memory bandwidth → the 带宽/访存 atom must rank first
    hits = r.retrieve("访存带宽 memory bandwidth 瓶颈", parsed["atoms"],
                      top_k=2, embed_fn=_embed, rerank_fn=None)

    assert hits[0]["cand"] == "c_bandwidth.c"
    assert len(hits) == 2


# ── RED 3 · reranker, when supplied, decides the final order ─────────────────
def test_retrieve_applies_reranker_over_dense():
    parsed = r.parse_corpus(CORPUS)
    seen = {}

    def rerank(query, texts):
        seen["n"] = len(texts)
        # invert: score by NEGATIVE index so the LAST dense candidate wins
        return [float(i) for i in range(len(texts))]

    # dense would put 带宽 first for this query; reranker promotes whatever it
    # scores highest (last one) → proves rerank actually reorders dense output.
    hits = r.retrieve("访存带宽 bandwidth", parsed["atoms"], top_k=1,
                      embed_fn=_embed, rerank_fn=rerank, candidates=4)
    assert seen["n"] == 4  # all 4 dense candidates fed to reranker
    # reranker scored the last-fed candidate highest → it wins, not dense #1
    assert hits[0]["cand"] != "c_bandwidth.c"


# ── RED 4 · build_grounding ALWAYS keeps the balance-warning meta-lesson ─────
def test_build_grounding_always_includes_balance_warning():
    # top_k=1 and a query unrelated to correctness → balance still present
    out = r.build_grounding(CORPUS, "SIMD 向量化对齐", top_k=1,
                            embed_fn=_embed, rerank_fn=None)
    assert "bit-exact" in out
    # the SIMD atom (most relevant) is retrieved
    assert "c_simd.c" in out


# ── RED 5 · build_grounding returns a SUBSET (retrieval ≠ wholesale cat) ─────
def test_build_grounding_is_subset_not_full_dump():
    out = r.build_grounding(CORPUS, "访存带宽 bandwidth", top_k=1,
                            embed_fn=_embed, rerank_fn=None)
    # only the top-1 candidate atom is injected; the unrelated SIMD/build atoms
    # are dropped — this is what makes it retrieval rather than `cat corpus`.
    assert "c_bandwidth.c" in out
    assert "c_simd.c" not in out
    assert "c_build.c" not in out
