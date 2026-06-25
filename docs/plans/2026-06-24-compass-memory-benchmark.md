# compass 记忆 Benchmark 方案(把"我觉得有用"变成"数字证明有用")

> **For Claude:** 执行用 superpowers:executing-plans。**真跑留 fresh session**(本设计 session 极长·R3)。
> 目的三合一:① B1 价值门要的客观可测信号(证 lifecycle 真有用)② 对外展示数字 ③ 量化 Gemini 小 LLM 加多少分。

**Goal:** 用数字回答两问——(1) Goal B 刚 live 的 lifecycle(tier 加权 + PoI + reinforce)**到底比扁平 bge-m3 召回好多少?** (2) 接 Gemini 小 LLM 优化**再加多少分?**

**Architecture:** 复用现有 `tests/eval_recall.py`(leave-one-out 自召回·已有 MRR/P@1/3/5 harness)+ 9720 条真实记忆语料(盒上)。加"对比组开关",一次跑出各组分数差。不引外部数据集即可出内部 A/B 证明;外部 benchmark 作第二阶段。

**Tech Stack:** Python · 现有 eval_recall.py · bge-m3 daemon · recall_pkg/poi_weighting · apply_tier_weight · query_rewrite.py(Gemini)。

---

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
**Task 1.3**: 🔴 **诚实判读**:若 D2-D0 ≈ 0 → lifecycle 在这语料上没用(诚实记录·别美化);若 >0 → 量化的 B1 价值证明。Gemini D3-D2 同理(且记 token 成本)。
**验收**:一张 grounded 对比表 + 诚实结论(lifecycle 有用/无用·加多少分)。**这就是 B1 价值门要的可测信号。**

### 阶段 2 · 外部 benchmark(对外展示·第二批)
**问题**:compass 在标准记忆 benchmark 上能打吗?
- **数据集**:LongMemEval-S(agentmemory 参照 95.2% R@5)或 LoCoMo(多轮对话长期记忆)。选 LongMemEval(有公开 leaderboard·可对标)。
- **对比**:compass(全 lifecycle)vs 朴素向量库 vs 关 lifecycle 的 compass。
- **指标**:R@k / answer-accuracy(benchmark 自带评判)。
- **Task 2.x**: 下载数据集 → compass 当记忆后端跑 → 出数字 vs leaderboard。
- ⚠️ 重算力(embedding 全量)·跑在盒 GPU·错峰 ping soul。

---

## 关键原则(吃自己狗粮)
- **measurement-first**:绝不编分·D2-D0≈0 就老实说 lifecycle 没用(这正是诚实账,不是失败)。
- **B1 价值门闭环**:这 benchmark 本身就是给 lifecycle/PoI/Gemini 补"可测下游价值"——填 `docs/FEATURE_VALUE_LEDGER.md` 那些 ⚠️ 待补价值证明的行。
- **Gemini 隐私**:query 改写发外部 LLM·阶段1用脱敏 query 或本地 Ollama 对照;阶段2外部数据集无隐私问题。
- **不重造**:复用 eval_recall.py + poi_weighting + apply_tier_weight + query_rewrite.py,只加开关。

## 为什么这是现在最该做的
- Goal B 的 lifecycle/reinforce **刚 live**,benchmark 正好客观验证"分层 vs 扁平"真假——把 Goal B 从"代码 live"升级到"数字证明有用"。
- 给 compass 对外服务(MCP 记忆后端)一个可信的卖点数字。
- 闭合 B1 价值门:之前 ledger 里 OKF/GEP/tier 标 ⚠️ 待补价值,benchmark 给它们补上或诚实砍掉。

关联 memory:`reference_compass_self_improvement_points_distilled_from_rsi_fde_month_20260623`(B1 价值门)· `session_20260623_compass_phase1_merge_done_t4_deploy_topology_grounded`(lifecycle live 状态)。
</content>
