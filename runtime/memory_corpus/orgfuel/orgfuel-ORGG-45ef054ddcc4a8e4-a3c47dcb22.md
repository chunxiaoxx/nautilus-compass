---
name: orgfuel-ORGG-45ef054ddcc4a8e4-a3c47dcb22
description: "判读档判例 2026-06-24-compass-memory-benchmark · 两阶段 ## 两阶段  ### "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-45ef054ddcc4a8e4
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-24-compass-memory-benchmark · 两阶段
## 两阶段

### 阶段 1 · 内部 A/B(最快·dogfood·先做)
**问题**:lifecycle 各层各加多少分?用现有语料+harness,只加"开关"。

**对比组(逐层叠加·看增量)**:
| 组 | 召回逻辑 | 测什么 |
|---|---|---|
| D0 baseline | 纯 bge-m3 flat top-k | 地基分 |
| D1 +PoI | D0 + `boost_top_k_with_snapshot`(已证影响加权) | PoI 加多少 |
| D2 +tier | D1 + `apply_tier_weight`(分层加权) | 分层加多少 |
| D3 +Gemini | D2 + query_rewrite(Gemini flash 改写 query) | 小 LLM 加多少 |

**指标(harness 已有)**:MRR · P@1 · P@3 · P@5。每组跑同一批 query,看逐组 delta。

**Task 1.1**: 扩 `tests/eval_recall.py` → 加 `--mode {flat,poi,tier,gemini}` 开关,各 mode 用对应召回逻辑重排 top-k。TDD:小语料 fixture 验证各 mode 真切换 + 不崩。
**Task 1.2**: 跑全语料(本地或盒上 9720)× 4 mode → 出一张对比表(MRR/P@k × 4 组)。
**Task 1.3**: 🔴 **诚实判读**:若 D2-D0 ≈ 0 → lifecycle 在这语料上没用(诚实记录·别美化);若 >0 → 量化的 B1 价值证明。Gemini D3-D2 同理(且记 token
