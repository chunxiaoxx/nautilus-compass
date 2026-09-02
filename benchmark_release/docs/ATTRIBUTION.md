# NautilusMem/T0 attribution 与许可结论(2026-09-03 凌晨 · LOOP 轮产物)

## 上游事实(已核实)

- 仓库 [xiaowu0162/LongMemEval-V2](https://github.com/xiaowu0162/LongMemEval-V2)(Di Wu 等,UCLA 系;2026/08 仍在活跃更新 AgentRunbook-C V2)
- 组成:451 手工题 + 5 记忆能力(static state / dynamic state / workflow knowledge / environment gotchas / premise awareness)+ web/enterprise 双域 + small/medium 两档 + **官方 leaderboard(submission form,禁 issue 提交)**
- **官方口径**:reader 固定 Qwen3.5-9B(我们一致 ✓)· embedding Qwen3-Embedding-8B · judge **gpt-5.2 medium reasoning**(我们=doubao-seed-2-0-pro low/16384,口径不同 ✗)
- 第三方接入:官方支持自定义 memory backend(`@register_memory` + `insert/query` 接口)——**我们的 compass 后端(lmev2_compass_memory.py)正是这条官方路径**

## 许可结论(保守策略)

- 上游 GitHub README **无 license 声明**(GitHub API 超时未查到 LICENSE 文件;HF dataset license 字段同样待查——代理不稳,下轮补)→ 按 all-rights-reserved 保守处理
- **我们只发布**:①自研代码(lmev2_compass_memory.py 记忆后端/判分修正工具/摘要卡生成器)= 我们的作品,MIT 自定;②对上游 harness 的 patch **以 diff 形式**(不内嵌上游代码);③跑分 evidence(jsonl/成绩)
- **不发布**:上游题目/轨迹/截图/harness 副本
- T1 自创新题若用上游轨迹改编:需 HF dataset license 落地后再定(待查项)

## T0 路径修正(基于官方 leaderboard 发现)

**首选:向官方 leaderboard 提交 compass 跑分**(submission form)——权威背章、零分发负担、社区可见性最高。
前提二选一:
- A. 按官方 judge(gpt-5.2 medium)复跑 451 题(需 OpenAI key,成本 ~几美元级,与用户确认资源)
- B. 提交时声明 judge 口径差异(doubao low/16384 + 重判修正故事),附双口径数字——社区可信度略降,但判分修正本身是卖点

**并行:GitHub 发布自研部分**(compass backend for LME-V2 + 判分卫生学协议 + 调优记录),attribution 上游、不含其代码/数据。

## 待查项(下轮 LOOP)

- [ ] HF dataset license 字段(代理稳时用 python huggingface_hub.HfApi().dataset_info 拉)
- [ ] 上游 leaderboard 现有 baseline 数字(RAG/AgentRunbook 的公开成绩)——成绩册对比表的原料
- [ ] 上游 leaderboard 提交格式的具体要求(leaderboard/README.md,需进 repo 看)

## 2026-09-03 LOOP 轮补:leaderboard 提交格式核实(README 全文已读)

- **judge 硬门**:build_submission_step_1 验证 `judge model contains gpt-5.2` → "声明差异"路线堵死
- reader 硬门:`reader model contains qwen3.5-9b`(我们一致,任意兼容端点可)
- **run 目录须含 runtime_inputs/**(questions.json 等)+ per_question 全覆盖验证;本地 d12 瘦身版无 runtime_inputs → 官方榜需完整重跑(reader 可用 API 端点,不必自部署)
- 提交包=两步构建(operating_points 双域合并→LAFS 打包)+SYSTEM_DESCRIPTION+单代码文件→tar.gz→submission form
- LAFS=accuracy(overall_full_set×100)×latency(memory_query_avg_seconds)对固定 reference frontier 增益,支持多延迟操作点

## 2026-09-03 LOOP 轮二:论文全文核实——license 落定 + 战略定位纠偏

### License 结论(终)
论文 E.2:"release our code and derived benchmark artifacts under **Apache-2.0**"。→ patch/造题/分发全通(NOTICE 归属义务保留);GitHub LICENSE 文件待最后核对一次。

### 官方 baseline 坐标(LME-V2-Small Overall,gpt-5.2 judge 口径)
| 方法 | Small | Medium | 延迟/query |
|---|---|---|---|
| No retrieval | 1.3% | 1.3% | 0s |
| RAG query→slice | **42.8%** | 38.1% | 0.1s |
| RAG slice+notes | 51.0% | 45.9% | 0.2s |
| AgentRunbook-R | 58.6% | 57.0% | 26.9s |
| Codex | 69.9% | 68.7% | 177s |
| AgentRunbook-C | **74.9%** | 70.1% | 108s |
| **compass(d12 tuned, doubao judge)** | **≈39.3%**(web 40.0/ent 38.4 合并) | — | 待测(应<1s,无 LLM controller) |

### 🔴 定位纠偏(第二次)
40.0/38.4 在我们自己的纵向比较里是大胜,放进官方坐标系=**与最弱 RAG 基线相当,非优势**。上官方 leaderboard 提交 39.3% vs 官方 RAG 42.8% = 自曝其短,无意义。
**T0 leaderboard 提交撤下优先级**;成绩册改为"诚实定位"(坐标如实+判分卫生学贡献+轻量差异化——无 LLM controller 的检索延迟应远低于 26.9s,待实测)。**真正的攻坚=三池设计移植**(官方 raw state/event/note pools vs 我们单流 dense+BM25;A 臂摘要卡≈note pool 原型)——目标 Small 55-60%(超 AgentRunbook-R),有竞争力后再上 leaderboard。

### 附:官方 judge 结构
多数题程序化判分(normalized/ordered/choice matching),仅 gotchas+abstention 走 gpt-5.2 judge;官方 abstention rubric 明确给"lacks access to live environment"判 1(与我们 d12 刀1 摸出的口径一致=方向没错过)。

## 2026-09-03 论文细节补(影响差距归因)

- **官方 memory context 预算=200k tokens,我们 d12=24k(8 倍差)**——官方允许塞远多证据;这是可解释的差距来源+我们的现成调参杠杆
- 官方 reader 采样 temp 0.6/top_p 0.95/top_k 20(非贪心),与 d12 部署默认可能不同,口径注记项
- **官方判分结构:多数 structured 题程序化判分,仅 gotchas+abstention 走 gpt-5.2 judge**——与我们"全题 LLM judge"管道结构不同;我们的 PROTOCOL 1.4(程序化优先)与官方同向
- 官方 abstention rubric(Table 5):"lacks access to live environment"明确判 1、裸 UNKNOWN 判 0——与我们 d12 刀1 摸出的口径一致(对齐方向被官方文本确认)
- AgentRunbook-R 三池细节(C.2):raw state pool(radius-1 窗+截图)/event pool(LLM 生成转移描述)/note pool(procedure+hint)——A 臂摘要卡≈note pool 简化版
