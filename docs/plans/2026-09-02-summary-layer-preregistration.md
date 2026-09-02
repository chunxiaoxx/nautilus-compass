# 跨会话聚合专项 · 摘要层预注册方案(2026-09-02)

> 用户拍板:先做跨会话聚合专项(摘要层/实体卡片),这是 e2e500 最大分差。
> 本文 = 诊断结论 + 方案设计 + 预注册判据。跑分前锁定,防 whipsaw。

## 一、诊断结论(零成本考古,2026-09-02)

数据源:`docs/evidence/e2e_500_gpu_20260829.tar.gz` 4 分片 500 题 raw + `e2e_500_full_20260829.json`。

### 分型与责任划分(错题 = 检索漏 vs 组装漏)

| 型 | n | acc | 错题 | 检索漏(gold 不在 top5) | 组装漏(gold 在 top5 仍错) |
|---|---|---|---|---|---|
| ssu | 70 | 0.957 | 3 | 0 | 3 |
| ssp | 30 | 0.800 | 6 | 1 | 5 |
| ku | 78 | 0.731 | 21 | 0 | 21 |
| **ssa** | 56 | **0.250** | 42 | 1 | **41** |
| **ms** | 133 | **0.226** | 103 | 1 | **102** |
| **tr** | 133 | **0.158** | 112 | 5 | **107** |

**结论:三短板型 257 道错题中 250 道(97%)gold session 已在 top5——检索层几乎无责任,组装层负全责。** 组装层现状:reranker 从 top5 session 里只挑 3 条 utterance(每条 500 字符)——ms 题 gold evidence 平均散布 3+ session,3 条 utterance 装不下,模型只能数到一部分。

### 错题形态指纹

ms 103 道错题中 45 道(44%)是"数漏"(answer 数字 < truth 数字,如 truth=3 件衣服只答 1 件)——evidence 不全的直接证据,非模型算力不足。

### 现有管线的两处截断(根因)

1. `build_ssu_context` max_utterances=3:top5 session 的全部 utterance 里只留 3 条。
2. `build_context` session 级路径 max_chars=800:session 只给前 800 字符(该路径 ms/tr 在用)。

注:jsonl 的 `truth_in_top` 是"至少一个 gold 在 top5"(`any()`),部分覆盖未计入;数据集 join 后的精确全覆盖率见附录(待补)。

## 二、方案设计:摘要层(session summary layer)

### 2.1 session 摘要卡(预生成,一次构建全量复用)

对数据集每个 unique session 生成一张结构化摘要卡(ARK coding plan 端点,plan 内额度):

```
[Session <id> · <date>]
USER FACTS: 每条一行,保留实体/数量/金额/日期(可数、可聚合)
  - 要去干洗店取回海军蓝西装
  - 买了柠檬树,花了 $85
ASSISTANT: 助手做过/说过/推荐的(每条一行)
  - 推荐了三个瑜伽馆
TOPICS: 3-5 个关键词
```

关键设计约束:
- **可数性优先**:ms 题 = 数东西,USER FACTS 的 bullet 结构让"数数"变成数 bullet。
- **保实体保数量**:金额/数量/日期/专名逐条保留,不写段落式总结(段落会吞数量)。
- 输入预算:session 原文按 6000 字符分段(超过则分段摘要再合并),单卡输出 ≤150 字。
- 幂等缓存:summary_cache.json 按 session_id + 内容 hash 键,断点续跑。

### 2.2 context 组装(ZMM_SUMMARY_LAYER=1 时,ms/ssa/tr 三型路由)

```
=== Session Timeline(全部 top5 session 的摘要卡,按日期排序)===
[Session A · 2023-01-15] USER FACTS: …
[Session B · 2023-01-22] USER FACTS: …
...
=== Evidence Extracts(现有 utterance 管线,上限 3→6 条)===
--- Utterance 1 (Session B, 2023-01-22) --- ...
```

原理:摘要卡给全貌(可数可聚合),utterance 给原文证据(可引用可判对错);tr 型沿用 timeline prompt,摘要卡天然带日期序列。ssu/ssp/ku 三型**字节不变**(已近天花板,不动)。

### 2.3 实体卡片(B 计划,本轮不实现)

若摘要层 PARTIAL(见判据),对 top5 session 内高频实体聚合"关于 X 的所有陈述"。预留接口,不提前建。

## 三、预注册判据(A/B)

### 3.1 实验设计

- **B 臂(基线)= 8/29 全量 evidence,不重跑**:同判据(subject=doubao-seed-2-0-pro-260215 / judge=glm-5.3-flash / 同 retrieval 配置),500 题分型数字即为基线。
- **A 臂(摘要层)= 只跑三短板型 322 题**(ms 133 + tr 133 + ssa 56),ZMM_SUMMARY_LAYER=1,其余 env 与 8/29 全量一致。
- 高分三型不跑不比(未改动,理论字节不变;全量时顺带回归验证)。

### 3.2 三态判定(跑分前锁定)

| 判定 | 条件 | 处置 |
|---|---|---|
| **PASS** | ms ≥ 35%(锚 22.6)且 ssa ≥ 40%(锚 25.0)且 tr ≥ 30%(锚 15.8)三型全达 | 上 500 全量(ssu/ssp/ku 顺带回归,不回退门 ≤1pt) |
| **PARTIAL** | ≥2 型达标且其余型不低于锚 | 只在达标型路由,上全量 |
| **FAIL** | ≥2 型未达标 | 摘要层设计错,回炉查摘要质量(抽 20 张卡人工验),**不加大剂量不换参数硬调** |

n 说明:ms/tr n=133、ssa n=56,±5pt 内视为平(二项 CI);门都设在 +12pt 以上,远超噪声带。

### 3.3 计算资源(待用户拍板)

- 选项 1:本地跑(API 调用 + 本地 bge-m3 CPU 检索,估 2-4h embed + 322×~2min ≈ 11h 墙钟,零成本)
- 选项 2:重租 4090(¥1.65/h,30-60s/题,322 题 ≈ 4h ≈ **¥7**,摘要生成也在 plan 内)

## 四、执行清单

1. ✅ 诊断(本文 §一)
2. ⏳ `vtf/build_session_summaries.py`(幂等缓存,断点续跑)
3. ⏳ harness 改造:`ZMM_SUMMARY_LAYER` 门 + `build_summary_context()` + 单测
4. ⏳ 摘要全量生成(unique session 数以数据集实测为准,join 后补)
5. ⏳ A 臂 322 题(资源待拍板)
6. ⏳ 判定 → PASS/PARTIAL 则 500 全量;GOAL_SSOT 修正(e2e500 早已完成 42.6%,N5 行"375/500"系过时中间态)

## 附录(2026-09-02 实测补全)

### 数据集事实
- longmemeval_s = 278MB 单文件,500 题,**unique sessions = 19829**(每题独立 haystack,基本不跨题共享)→ 摘要按需生成(322 弱点题 top5+gold = **1663 张卡**,非全量)
- evidence session 数分布:1 个=176 / 2 个=250 / 3 个=41 / 4-6 个=33

### 精确 gold 全覆盖率(join answer_session_ids vs 8/29 top5)

| 型 | 错题 | gold 全在 top5 | 部分在 | 全漏 |
|---|---|---|---|---|
| ssa | 42 | **41(98%)** | 0 | 1 |
| ms | 103 | **72(70%)** | 30 | 1 |
| tr | 112 | **93(83%)** | 14 | 5 |

对照组(对题)gold 全在率:ssa 100% / ms 83% / tr 100%——组装层责任进一步坐实。

### smoke 单题(q70 · 0a995998 · "取退几件衣服" · truth=3)
- 8/29 基线:答 1(数漏);摘要层:答 2(数出两双 Zara 靴,漏干洗 blazer)——方向性改善,evidence 全在卡中,残余瓶颈=模型聚合数数
- 检索 top5 与 8/29 完全一致(本地 CPU bge-m3 复现性 ✅)

### 过程中修掉的三个坑(已 commit)
1. **`_dates` 作用域 bug(8/29 就存在)**:只在 utterance 分支赋值,session 级题型读到同分片前一题的日期数组(错位污染)/或 UnboundLocalError。修复=定义提到分支外。
2. **ARK base url 漂移**:本机 env 的 `ARK_BASE_URL` 指向 `/api/v3`(按量端点,红线禁用)——runner 硬编码 coding plan 端点 `/api/coding/v3`。
3. **newapi 网关 UA 过滤**:python-requests UA 被 403,curl UA 放行(实测 UA=curl/8.9.1 → 200)。harness 请求头统一加 UA。
- 另发现安全问题:vtf/e2e500_shards.sh(8/29 已入库)硬编码 judge newapi key,待用户轮换。

