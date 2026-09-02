# compass on LongMemEval-V2 — Results Card(草案 · 按方案 B 诚实坐标 · 待用户拍板)

> 协议版本 PROTOCOL v1.0 · 成绩卡机读版 `judge_hygiene/scorecard.compass.example.json`
> 判据:reader Qwen3.5-9B(vllm)· judge doubao-seed-2-0-pro-260215(low/16384,全题 LLM)· 双口径

## 成绩(重判干净口径,2026-09-02 定案)

| 口径 | web (n=240) | ent (n=211) | 合并 (n=451) |
|---|---|---|---|
| full | 40.0% | 38.4% | 39.3% |
| non-abstention | 32.7% (n=168) | 25.2% (n=155) | 29.1% (n=323) |

内部纵向:untuned(2026-08-30)web 19.6% / ent 12.8% → tuned+rejudged 40.0/38.4。

## 分型 vs 官方方法(合并口径)

| 能力 | compass | 官方 RAG q→slice | 官方 AgentRunbook-R | 官方 -C |
|---|---|---|---|---|
| static | **21.6%** (134) | 47.1% | 66.1% | 82.0% |
| dynamic | **11.6%** (86) | 42.5% | 58.3% | 72.4% |
| workflow/procedure | **55.4%** (74) | 41.5% | 52.8% | 72.6% |
| gotchas | **48.3%** (29) | 20.7% | 31.0% | 48.3% |
| abstention 类 | 43.8–73.2% (128) | — | — | — |

**两个自洽的发现**:
1. 我们的 procedure(55.4%)超过官方 AgentRunbook-R(52.8%),gotchas(48.3%)与官方 -C 持平——滑窗 chunk+RRF 对程序性知识检索有效
2. static(21.6%)/dynamic(11.6%)是与官方的主要差距——官方消融显示 static 主要靠 **raw state pool**(去掉后 66.1→28.6),我们单流检索单元缺精确状态索引。这把升级路线收窄到:加 raw state 索引池(而非全盘重做)

## 口径差注记(诚实声明)

- 官方 context 预算 200k tokens vs 我们 24k(8 倍)
- 官方判分多数题程序化+仅 gotchas/abstention 走 gpt-5.2 judge;我们全题 doubao judge(已做预算修正重判,见 PROTOCOL §1.1)
- 两处差异方向不一,合并数字不宜直接与官方表逐行硬比;分型趋势(强 procedure/弱 static)在两种口径下均成立

## 升级路线(T1)

1. raw state 索引池(对齐官方三池的短板池)——目标 static 21.6→40+%
2. context 预算 24k→64k(渐进)
3. 摘要/笔记层(note pool,LongMemEval-S 线的 A 臂实验同思想)
4. 目标:Small 合并 55-60%(超 AgentRunbook-R)后再评估官方 leaderboard 提交(judge=gpt-5.2 硬门)

## Evidence

- 原始与重判:`vtf/_compass_lmev2_out/d12/` + `d12_rejudge/`(主仓)
- 判定与修正过程:commit 链 2026-08-30 → 09-02(d12 定案/d13 持平/d14 拒绝/重判定案)
