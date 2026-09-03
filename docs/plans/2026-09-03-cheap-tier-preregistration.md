# T1 便宜档(raw state 强化)预注册 · 2026-09-03

> 用户拍板:便宜档先做+排期同意。三改:①a11y 预算 500→1500(答案行防剪枝)②题图接入(题图与 state 截图匹配/文本化)③规则式查询分解(实体名词子查询,无 LLM controller,保住低延迟卖点)。
> 跑分:GPU 重租 4090 待用户确认(≤¥10);A 臂=现役基线(d12 重判 39.3%,分型 static 21.6/dynamic 11.6/procedure 55.4/gotchas 48.3)。

## 判据(跑分前锁定,三态)

| # | 判据 | 门 | 依据 |
|---|---|---|---|
| ① | static 分型 | **≥35%**(锚 21.6) | 官方 q→slice 无 controller 即 47.1%,我们应至少到其 3/4 水位 |
| ② | 合并 full | ≥42.8%(超官方 q→slice) | static 大头+dynamic 连带 |
| ③ | procedure/gotchas 不回退 | ≥锚-3pt(52.4/45.3) | 改池不得伤强项 |
| ④ | 延迟 | 无 controller 保留(query <5s) | 差异化卖点 |

- **PASS**(①②③④全过):成绩册/README 换新数字,评估 leaderboard
- **PARTIAL**(①过②未):按分型局部采用,查合并归因
- **FAIL**(①未过):三改方向错,逐项消融定位(先查 a11y 预算是否根本不够)

## 实施清单

1. vtf/lmev2_compass_memory.py 三改(param 化:ZMM_A11Y_BUDGET/QUERY_DECOMP 环境门,默认 off 字节不动基线)
2. benchmark_release/compass_backend/lmev2_memory.py 同步
3. smoke 10 题(静态分型命中对比:错题的 gold state 是否进 top-k)
4. 全量 451(GPU,复用 lmev2 部署链)
5. 判定+成绩册刷新

## 风险与对策

- a11y 预算涨 3 倍→chunk 变长→dense 检索稀释:对策=预算分层(state 首段 500 全量索引+全文存 evidence 侧)
- 查询分解的实体抽取误伤:对策=子查询结果与原问题结果 RRF 融合而非替代
- 题图匹配可能引入噪声:对策=题图仅用于 rerank 加权,不参与首检
