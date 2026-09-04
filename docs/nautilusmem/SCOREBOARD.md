# NautilusMem 成绩册 · compass 记忆后端在 LongMemEval-V2 上的成绩(T0-4 · 定稿)

> 状态 9/4:呈现口径已由用户拍板 = **选项 B**(现役数字+双口径并报,官方坐标系注明判分
> 口径差,不加 gpt-5.2 折算)。cheap-tier web 定案:**36.3%**(240 题,86 LLM 行经 401 事故
> 重判补齐 flips +47/−0·0 失败,154 程序化行原分保留;产物固化 `vtf/_compass_lmev2_out/cheap_web/`)
> ——三改组合未超 d12 现役(-3.75pt),d12 维持现役,归因待 ent 对照(双域落→组合关;ent 超→域特异)。

## 0. 这是什么(一句话)

compass 记忆后端在**官方 LongMemEval-V2 基准**(xiaowu0162/LongMemEval-V2,Di Wu 等,
UCLA 系)上的完整成绩与调优记录:我们发布自研记忆后端代码+判分卫生学协议+成绩
evidence;题目/轨迹/harness 归上游,不随本成绩册分发。

## 1. 成绩总表(Small 档 · full 口径)

| 配置 | web | ent | 说明 |
|---|---|---|---|
| untuned(首跑基线,doubao 口径) | 19.6% | 12.8% | 8/30 首次全量基线 |
| **tuned d12 + 重判(现役)** | **40.0%** | **38.4%** | 三刀调优+judge 预算修正重判 |
| cheap-tier raw-state 强化 | 36.3% | [待补] | 三改组合(a11y_chars1500/query_decomp/shot_per_traj)· web 定案 9/4:精度 -3.75pt + 查询 p50 8.0s(慢 d12 ~48×),双面净伤,维持 d12 现役;ent 跑分中 |
| non-abst 口径(现役重判合并) | 32.7% | 25.2% | 可作答题 n=168/155 |
| abstention-only 口径(现役) | 56.9% | 75.0% | 应拒答题 n=72/56;画像=拒答判别强、知识召回弱 |

单域调优幅度:web +20.4pt(2.0×)· ent +25.6pt(3.0×)。

## 2. 官方坐标系(注明判分口径差)

官方 README baseline(gpt-5.2 judge + 200k 预算口径,Small Overall):

| 系统 | 成绩 | 备注 |
|---|---|---|
| No retrieval | 1.3% | 无记忆下限 |
| RAG query→slice | 42.8% | 与我们架构最像的官方基线 |
| RAG slice+notes | 51.0% | |
| AgentRunbook-R | 58.6% | 三池+LLM controller,延迟 26.9s |
| AgentRunbook-C | 74.9% | coding agent,延迟 108s |
| **compass(本成绩册)** | **39.3%**(web 40.0/ent 38.4 合并) | doubao judge,24k 预算,延迟 [待补] |

**两处结构性口径差**(解释差距的一部分,不是借口):
1. context 预算:官方 200k vs 我们 24k(8.3×)
2. 判分:官方程序化+gpt-5.2 judge vs 我们全题 LLM judge(doubao low/16384,重判修正)

**差异化的实测**:无 LLM controller——memory_query 延迟 web p50 0.165s / p95 0.339s,
ent p50 0.328s / p95 0.798s(d12 全量实测)vs AgentRunbook-R(LLM controller)26.9s——**约 80× 差距**。
诚实注记:max 尾部(web 23.8s/ent 50.9s)= 冷启动/索引进场,非稳态。

## 3. 判分修正故事(卫生学贡献)

- d13 发现:doubao judge `max_completion_tokens=4096` 被 reasoning 吃满 → 空/截断输出
  系统性记 0 分。web 156 题重判 +3.3pt,ent -1.9pt——**方向都不一样**,不重判就带错误数字发布。
- 重判工具 `rejudge_run.py`(幂等/断点续跑/flip 记账)随基准分发。
- 判分纪律全文:[PROTOCOL.md](PROTOCOL.md) v1.0(judge 预算下限/双口径强制/成绩卡 config 节/
  verifier 优先/污染声明)。
- 500 题 e2e 附加证据:judge 断连把 14.2% 基础设施故障记成错题(5.4pt 失真,占真实
  32.8pt 效应的 1/5)——详见 paper2(J-C 连接盲)。

## 4. 成绩卡 config 节(自我遵守 PROTOCOL 1.3)

```
judge: doubao-seed-2-0-pro-260215 / ark coding endpoint / max_completion_tokens 16384 / low
subject: Qwen/Qwen3.5-9B(与官方 reader 一致)/ temp 0.6 / top-p 0.95 / top-k 20
retrieval: BGE-m3 embedder / top_k 20(d12 run_args 双域同值) / 检索单元=轨迹段
口径: full 40.0/38.4 + non-abst 32.7/25.2 + abst-only 56.9/75.0(web/ent)
重判: 已跑(d12 现役数字=重判后,flips web 12/ent 16)
```

## 5. attribution 与许可

- 上游:https://github.com/xiaowu0162/LongMemEval-V2(451 手工题/双域/两档/官方榜)
- 上游 README 无 license 声明 → 按 all-rights-reserved 保守处理:只发布自研代码
  (lmev2_compass_memory.py 后端/判分修正工具/摘要卡生成器)+ 对 harness 的 patch
  以 diff 形式 + 成绩 evidence;不分发上游题目/轨迹/截图/harness 副本
- 完整结论:[ATTRIBUTION.md](ATTRIBUTION.md)

## 6. 待办(发布前)

- [x] cheap-tier web 240 全量数字落表(9/4 定案 36.3%,判分经 rejudge 补齐+产物固化)
- [ ] ent 211 接力后同表
- [x] non-abst 双口径(d12 aggregated+重判 flips 合并,full 锚定 40.0/38.4 校验通过)
- [x] memory_query 延迟实测(p95 web 0.339s / ent 0.798s)
- [ ] 用户拍板呈现口径(DECISION B/C)→ 定稿
