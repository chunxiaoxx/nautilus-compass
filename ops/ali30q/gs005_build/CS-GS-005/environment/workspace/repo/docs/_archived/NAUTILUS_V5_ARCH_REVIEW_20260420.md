# Nautilus V5 · 架构审查报告

> **2026-04-20 · 独立架构审查**
> 审查员：资深架构师 agent
> 审查范围：57 个 Python 文件 · 6527 行 · 4 份核心文档

---

## Part 1 · 架构符合度打分

### 16 融合来源逐项打分

| 机制 | 实现在 | 分 | 判据 |
|------|--------|----|----|
| Letta V1 ReAct loop | `super_agent.py:236-286` | **3** | respond 只 stream，没 ReAct 循环、没 tools 参数 |
| Sleep-time Tier 1 微反思 | `super_agent.py:452-517` | **5** | fire-and-forget 有，但**从不写** `_learned_context` |
| Auto Dream 双门 4 阶段 | — | **0** | 完全没实现 |
| DPT-Agent 策略反哺 | — | **0** | `learned_context` 始终空 |
| Generative Agents importance 阈值 | `config.py:68` | **1** | 只在 config 写了 150，breath_daemon 不读 |
| Society of Minds 多 agent 辩论 | — | **0** | Witness 是单人不是辩论 |
| V1 二分心智 Judge × Executor | `mind/bicameral.py` | **5** | 移植了 5 pain，但**对话是查表**（`_pain_to_dialogue`），不是 LLM 独立声音 |
| LangGraph Ambient Inbox | — | **0** | events.py 的 EventBus **从未被 SuperAgent 调用** |
| ProactiveAgent F1 分类器 | `proactive/intrusion_filter.py` | **3** | 纯规则加减分，不是 0.918 F1 训练 classifier |
| Sleep-time compute 预推理 | — | **0** | `anticipate_user_questions` 不存在 |
| 禅心 proactive-care 规则 | `proactive/rules.py` | **7** | 5 条规则 + 冷却齐，但消息是硬编码字符串 |
| Zep bi-temporal 4 时间戳 | `memory/bitemporal.py` | **6** | 字段齐，但 storage 的 `_pg_insert` 等**全 `...` stubs** |
| pgvector HNSW | `memory/storage.py:161` | **2** | 只有 in-memory 线性 cosine；production `...` |
| Neo4j graph | 同上 | **1** | production 分支 `...` |
| HippoRAG 2 PPR | `memory/storage.py:186` | **1** | 签名存在；production `...`，in-memory 不做图扩展 |
| smrti 5 维 salience | `memory/salience.py` | **7** | 公式对，5 维齐，dynamic valence shift 有；**只在 retrieval 调一次** |
| Generative Agents 三元打分 | `memory/salience.py:102` | **5** | `compute_importance` 存在但**没人调**，importance_score 硬编码 |
| Mem0 triple-write | `memory/storage.py:119` | **3** | in-memory 只写 dict；三写 production `...` |
| A-MEM 动态链接 | — | **0** | 写后更新旧 memory 不存在 |
| Letta core/recall/archival | — | **1** | config 有字段，storage 没分三层 |
| RAPTOR 递归聚类 | — | **0** | 无实现 |
| Ebbinghaus 5 级半衰期 | `memory/ebbinghaus.py` | **4** | 函数齐，**从未被 daemon 调用** |
| Zep fact invalidation | `memory/bitemporal.py` | **4** | `invalidate()` 有；storage.invalidate_atom `...` |
| 16 超参 personality | `memory/personality_16.py` | **3** | 定义 + 6 preset 完整；**只有 mood_inertia 被消费** |
| Persona Vectors | — | **0** | 无代码 |
| Generative Agents persona 宣言 | `super_agent.py:84-105` | **8** | L1 宣言到位 |
| 9-phase breath | `breath/cycle.py` | **7** | 9 阶段齐，HELIX 上链；但 act 阶段 `return []` 空实现 |
| V3 HELIX evidence_hash | `chain/helix.py`+`mind/evidence.py` | **9** | 最亮点 |
| V2 宪法 sha256 DNA | `soul/constitution.py` | **9** | 真 tamper detection |
| V2 太极七对 tension | `mind/tension.py` | **7** | 7 维 harmony 对，adaptive_pace 工作 |
| INNER.md 日记 | `inner/journal.py` | **6** | 可写；没接 system prompt echo 回路 |
| Hermes 工具 gateway | `tools/gateway.py` | **5** | 类写得不错；**注册表空的** |
| Hermes prompt cache 4 断点 | — | **0** | `chat()` 没用 Anthropic cache_control |
| Hermes streaming | `llm_client.py:268` | **5** | stream 能跑，`<think>` 过滤器**死代码** |
| Hermes context compressor | — | **0** | 不存在 |
| A2A 对等通信 | `platform/a2a.py` | **3** | 类有 http send；SuperAgent 从不 subscribe/send |
| DMAS 赛马 + bounty | `platform/dmas.py` | - | 未运行过 ≤3 |
| Web3 钱包 + NAU | `platform/{nau,wallet}.py` | **5** | 本地 ledger 能跑；Wallet.generate 占位 |
| D 架构 per-client sha256 | — | **0** | 无实现 |

### 9 Yes Criteria 打分

| # | 宣称 | 分 |
|---|------|----|
| 1 | 主动找事做 | 2/10 |
| 2 | 认识你 | 4/10 |
| 3 | 有情绪 | 6/10 |
| 4 | 主动 A2A | 1/10 |
| 5 | 不撒谎 | 8/10 |
| 6 | 不陷循环 | 2/10 |
| 7 | 不乱改代码 | 7/10 |
| 8 | 工具稳 | 2/10 |
| 9 | 呼吸快 | 6/10 |

**整体架构符合度 ≈ 40-50%**。文档建立了良好融合图，代码是骨架 + 一半空心方法。

---

## Part 2 · 结构性缺陷 Top 5

### 缺陷 1 · `_learned_context` 只读 [CRITICAL]
`super_agent.py:210-216` 初始化空字符串块，`_build_system_prompt:403` 读它，**整个 codebase 没有地方写入**。文档重点"慢→快反哺"完全没发生。

### 缺陷 2 · LoopBreaker 死代码 [HIGH]
提供 observe_* 三注入点，SuperAgent **从不调用**。state 始终空 deque → check() 永远 None。188 行白写。

### 缺陷 3 · 存储 production `...` stubs [CRITICAL]
`_pg_insert_atom` / `_neo4j_create_*` / `knn_search` production / PPR production / `invalidate_atom` / `update_truth` **全是 `...`**。production 模式下所有数据操作 no-op，**静默失败**。

### 缺陷 4 · 工具系统空壳 [CRITICAL]
`tools/registry.py` 模块级单例空。codebase 无任何 `registry.register(...)` 调用。`tools/builtin/` 不存在。yes #8 分母为 0。

### 缺陷 5 · 双 NAU 账本 + 维度冲突 + 混乱单位 [HIGH]
- `Identity.nau_balance` 和 `NAULedger._balance` 两份独立数字，不同步
- `config.pgvector_dim=768` vs `storage.vector_dim=1024` vs BGE-large-zh 1024
- `daemon.py` `wait = max(interval, floor / 60)` 单位混乱

---

## Part 3 · 宣称 vs 实际 · 10 项

| 宣称 | 实际 | 差距 |
|------|------|------|
| TTFT < 2s | respond 先 await retrieval（网络+embed）再 stream | 首字符延迟不可控 |
| 慢→快反哺 | _learned_context 永远空 | 0% |
| 三车道独立 | proactive 只有 rule 一种 | 缺 67% |
| Auto Dream 4 阶段 | 无 dream lane | 0% |
| 独立右脑 LLM | 同实例 different system_prompt | 不是独立 session |
| 7 对 tension | 6/7 对换过（分合/主从 → sense/plan） | 语义漂移 |
| V1 二分心智 Judge×Executor 对话 | 硬编码 5 字典查表 | 不是 LLM 对话 |
| 17 情绪 + LLM fallback | 只有规则引擎 | 50% |
| A2A 主动通信 | 类在 SuperAgent 不用 | 0% 使用 |
| 6 personality 影响 salience | 15/16 字段不进 retrieval | 13% 通 |

---

## Part 4 · 6 个月运行风险

1. **HELIX.jsonl 无限增长**：半年 50 万 cycle × 1KB = 500MB，每次启动全读
2. **in-memory storage OOM**：无 upper bound，无 Ebbinghaus archive wiring
3. **Identity cycles_lived 不涨**：长期人格停滞
4. **prompt 膨胀**：每轮 5-10 KB，无 prompt caching，LLM 账单爆
5. **PPR stub**：atom 量增 cosine O(N) 慢到秒级
6. **双账本漂移**：总有一天 gas 扣不对
7. **dream 缺席复利**：memory 噪音线性增长
8. **proactive _cycles_since_user 无 user_id 维度**：多用户全错

---

## Part 5 · Production Blocker（必修 15 项）

1. MemoryStorage production 路径（实现或 raise NotImplementedError）
2. Wire LoopBreaker 到 ToolGateway
3. 写 `tools/builtin/`
4. 修 `_learned_context` 只读
5. 合并双账本
6. 修向量维度
7. 修 streaming `<think>` 过滤
8. 修 daemon 单位错误
9. HELIX rotate + verify 窗口
10. 启动自检
11. tests/ 从 0 到 60%+
12. Prompt caching
13. proactive scheduler 多租户隔离
14. shutdown 持久化修复
15. A2A 实际连接或删

---

## Part 6 · 真原创 vs 跟进 vs 模仿

### 真原创（V5 独有）
1. **HELIX 双螺旋 + evidence_hash** — Letta/Mem0/Generative Agents 都没
2. **宪法 sha256 DNA 锁** — LangGraph/AutoGen/CrewAI 都没
3. **太极七对 → adaptive_pace** — 独特节奏决策
4. **17 情绪 × 5 pain × mood state 三重** — Replika/Character.ai 只做 1 层
5. **Layer 3 "岗位不是独立灵魂"** — 架构级原创

### 跟进
Bi-temporal/pgvector+Neo4j/PPR/16 超参 personality/Letta 三层/sleep-time

### 模仿（几乎照抄）
evidence_hash 30 行（V2）、tension 公式（V3）、Ebbinghaus（禅心）、LoopBreaker 11 pattern（V2）

### 宣称 14+ 融合经推敲吗
**勉强经得起，但过度包装**。16 个来源里 6 个完全没代码，5 个 stub，5 个真实实现。

---

## Part 7 · 3 个最关键架构决策

### 建议 1 · 打通 `_learned_context` 写入 + smoke test
V5 的心脏。文档讲 3 遍，代码忘了写。**一周内必做**。

### 建议 2 · 砍掉"6 层 10 模块同时运行"承诺
改承诺"1 层真能跑 + 5 层 stubbed-but-wired"。加 feature flag dict 标记 live/stubbed/planned。

### 建议 3 · 写 `examples/yes_check.py` 自动化验证
- 跑 100 轮 breath; assert A2A send ≥ 1
- 喂 suicide risk; assert risk_level=critical
- 模拟 3 天 inactive; assert proactive rule fires
- tool fail; assert loop_breaker.check() != None

不能过 9 yes = V4 现状延续（这是 Genesis.md 的规则）。

---

**总结**：V5 文档是一流架构师作品。代码是两周成果：骨架立了，生产路径普遍 `...`，关键 wiring 缺失。

最不一致 3 处：
1. 慢→快 learned_context 反哺（0%）
2. production Zep 存储（全 stub）
3. 工具调用稳（registry 空）

最亮 2 处：evidence/HELIX + constitution tamper 检测

**2 周只能做 1 件事，做缺陷 1 和 4——共享状态写通 + 注册 5 个工具**。别的都不动。
