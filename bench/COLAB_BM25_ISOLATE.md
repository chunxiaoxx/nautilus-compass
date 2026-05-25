# LongMemEval-S BM25 RRF Isolate · Colab T4 · 3-group A/B/C

Verify Path B BM25 RRF fusion真的补 9.2pp gap(86% → 95.2% agentmemory R@5)还是反而拖累 LongMemEval P@5.

## Critical pre-req · PyPI v2.0.0 没含 BM25 RRF

BM25 RRF 代码至 2026-05-25 才回流 git(commit 9815219 in feat/restore-prod-v2.1.0).
- PyPI `nautilus-compass==2.0.0` ❌ 不带 BM25
- PyPI `nautilus-compass==2.0.1` ❌ 不带 BM25
- 必须 from-source install branch feat/restore-prod-v2.1.0 才能跑 BM25 ON

## 3-group setup

| Group | env vars | hypothesis |
|---|---|---|
| **A · baseline** (BM25 off) | `COMPASS_USE_BM25_RRF=0` (default) | 当前 86% P@5 baseline · 跟 v0.8 56.6% acc 类似 |
| **B · BM25 default** | `COMPASS_USE_BM25_RRF=1 COMPASS_BM25_RRF_K=60 COMPASS_BM25_RRF_TOP_K=30` | spec_compass_path_b 假设的 +9pp |
| **C · BM25 tuned** | `COMPASS_USE_BM25_RRF=1 COMPASS_BM25_RRF_K=10 COMPASS_BM25_RRF_TOP_K=10` | 减 noise · 测 retrieval depth 是否关键 |

## Per-Colab-session changes (apply to colab_longmemeval.ipynb cell 1)

```python
# Original cell 1: pip install nautilus-compass==2.0.0
# REPLACE with from-source install (含 BM25 RRF code):
!pip install -q "git+https://github.com/chunxiaoxx/nautilus-compass.git@feat/restore-prod-v2.1.0"
!pip install -q rank_bm25
```

Apply env var BEFORE importing nautilus_compass (cell 2 or 3):

```python
import os
# === Group A (baseline) ===
os.environ["COMPASS_USE_BM25_RRF"] = "0"

# === Group B (BM25 default) ===
# os.environ["COMPASS_USE_BM25_RRF"] = "1"
# os.environ["COMPASS_BM25_RRF_K"] = "60"
# os.environ["COMPASS_BM25_RRF_TOP_K"] = "30"

# === Group C (BM25 tuned) ===
# os.environ["COMPASS_USE_BM25_RRF"] = "1"
# os.environ["COMPASS_BM25_RRF_K"] = "10"
# os.environ["COMPASS_BM25_RRF_TOP_K"] = "10"
```

## Run order

1. **SUBSET=30 validation** for each group (30min × 3 = 1.5h) · 先验 instrument 不挂
2. **N=500 full** for each group (8h × 3 = 24h) · Colab free session limit 12h · 必须 group 间断开 + reconnect

## Per-题型 P@5 break-down (必须报告)

baseline single-session-user 58.6% 是真弱点 · 必须看 BM25 RRF 是否补这一类 vs 拖累其它强类:

| 题型 | n | A baseline | B default | C tuned |
|---|---|---|---|---|
| single-session-assistant | 56 | 96.4% | TBD | TBD |
| multi-session | 133 | 94.0% | TBD | TBD |
| temporal-reasoning | 133 | 91.7% | TBD | TBD |
| knowledge-update | 78 | 84.6% | TBD | TBD |
| single-session-preference | 30 | 73.3% | TBD | TBD |
| **single-session-user** | **70** | **58.6%** | **TBD** | **TBD** |
| **overall** | 500 | 86.0% | TBD | TBD |

## Instrumentation (建议 cell 修改前加)

在 retrieval pipeline 加 per-query log:

```python
import json
def log_retrieval(query_id, bm25_top5, vec_top5, fused_top5, correct_id):
    with open("retrieval_trace.jsonl", "a") as f:
        f.write(json.dumps({
            "qid": query_id,
            "bm25_top5": bm25_top5,
            "vec_top5": vec_top5,
            "fused_top5": fused_top5,
            "correct_in_bm25": correct_id in bm25_top5,
            "correct_in_vec": correct_id in vec_top5,
            "correct_in_fused": correct_id in fused_top5,
        }) + "\n")
```

分析: `correct_in_vec=1 & correct_in_fused=0` 的 query 数 = BM25 fusion 颠覆了 vector 正确答案 · 这是 BM25 拖累的直接证据.

## Decision matrix · 完三组后

| 结果 | 解读 | 下一步 |
|---|---|---|
| B 拖累所有题型 | BM25 fusion 算法错(可能 RRF score scale) | Read rrf_fusion() · 验是否 reciprocal-rank · 不是 raw score weighted |
| B 只拖累 single-session-user 以外题型 | tokenizer 问题 · CJK split() 退化 | 改 jieba 分词或 char-bigram tokenizer |
| B 补 single-session-user 但拖累其它 | scope 限制 dynamic gating | query length detect · 短 narrative 走 BM25 · 长查询走 vec |
| B 全题型 +5pp | spec 假设正确 · ship 进 v2.1.0 release | merge feat/restore-prod-v2.1.0 → main + PyPI release |
| C 比 B 好 | retrieval depth 是 noise 来源 | top_k=10 进 v2.1.0 release |

## 相关 memory

- spec_compass_path_b_phase_plan.md (BM25 RRF 设计原理)
- session_20260525-1400_stage1a_complete_prod_git_divergence_finding.md (BM25 代码源 finding)
- infra_t4_gpu_server.md (T4 已死 · 必须用 Colab)

## E3 教训补充 · knew_but_failed instrumentation(必加)

2026-05-21 E3 ablation 实证:MEME benchmark 上 BFS graph traverse 净 -1.8pp · root cause 是 LLM `knew_but_failed = 28q`(LLM 自己 reasoning 弱 · 给再多 ctx 也救不了)· **不是 retrieval 错**。

为防 LongMemEval 重蹈覆辙 · 上面 instrumentation snippet 必须扩 `llm_answered_correctly` field:

```python
def log_retrieval_full(query_id, qtype, bm25_top5, vec_top5, fused_top5,
                       correct_id, llm_answer_judged_correct):
    with open("retrieval_trace.jsonl", "a") as f:
        f.write(json.dumps({
            "qid": query_id,
            "qtype": qtype,
            "correct_in_bm25": correct_id in bm25_top5,
            "correct_in_vec": correct_id in vec_top5,
            "correct_in_fused": correct_id in fused_top5,
            "llm_answered_correctly": llm_answer_judged_correct,  # 关键新增
        }) + "\n")
```

### 分析必算 4 个 metric · 不只 P@5

| metric | 公式 | 解读 |
|---|---|---|
| retrieval_recall@5 | sum(correct_in_fused) / N | retrieval 性能 |
| answer_accuracy | sum(llm_answered_correctly) / N | 端到端 |
| **knew_but_failed** | sum(correct_in_fused & !llm_answered_correctly) / sum(correct_in_fused) | **LLM 推理 bottleneck**(retrieval 给对但 LLM 答错的比例) |
| missed_by_retrieval | sum(!correct_in_fused) / N | retrieval 漏召 |

per-题型还要算 knew_but_failed break-down · 不只 net average(E3 教训:net 数字骗人 · per-题型方向不一致)。

### Decision matrix 扩展(原 5 行基础)

| 结果 | 解读 | 下一步 |
|---|---|---|
| **knew_but_failed > 25%** | retrieval 改善天花板低 · **LLM 自己 reasoning 是 bottleneck** | 不该再死磕 retrieval(BM25/RRF/graph)· 改 prompt(CoT)· 换更强 LLM(Gemini Pro / Sonnet)· 或加 verification pass |
| knew_but_failed < 10% & retrieval_recall@5 < 90% | retrieval 是真 bottleneck | 继续 fusion / reranker / typed graph 改进(本 plan Sprint 1-4) |
| 两者都低 · answer_accuracy > 92% | 接近 SOTA · 难再涨 | 转 v3.0 typed graph + I GraphRAG · 不在 fusion 死磕 |
| single-session-user knew_but_failed 异常高 | 这一类 query LLM 不会从 user fact 推 | 加 entity-aware prompt template · 不是改 retrieval |

E3 ablation -1.8pp 是 noise within sample 因为 LLM bottleneck 占主导 · retrieval 改进被 LLM 抵消。LongMemEval 上同样可能。**先看 knew_but_failed 比例 · 再决定继续哪条 sprint 路径**。
