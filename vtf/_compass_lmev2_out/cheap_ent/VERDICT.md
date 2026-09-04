# cheap-tier ent 定案 · 2026-09-04(双域齐,三改组合关闭)

## 终值

**ent 36.49%(77/211,重判后)** vs d12 现役 38.4% → 未超,**预注册规则执行:双域均落 → 三改组合(a11y_chars1500/query_decomp/shot_per_traj)关闭,d12 维持现役**。

| 口径 | 分数 | 说明 |
|---|---|---|
| raw(启动坏配置 4096+medium 判官) | 30.81%(65/211) | 空响应重试风暴+give-up 11 起记 0 |
| **重判后(定案,low+16384)** | **36.49%(77/211)** | flips +16/−4,failed=0 |

- 程序化行 32/141(原分保留)· LLM 行 45/70(全量重判)
- 坏判官把 ent 压了 **5.7pt**(web 线同款故事:raw 被系统性压分,重判修复)
- web 对照:cheap-tier web 36.3%(87/240)同样未超现役 40.0% → 双域结论一致

## 产物(md5 与 GPU 机一致)

- `per_question.jsonl`(13,093,384B · md5 f88aea603718a178b5857724f8c997df)
- `rejudge_results.jsonl`(md5 cc1a196e3404e1cdb46b92e28e5d1219)
- `rejudge.log`(ALL_DONE 行)
- 本地独立复算:overall 77/211=0.3649 ✓(2026-09-04,Python 直算)

## 判官两坑(本线第 4/5 次 judge 事故,启动模板已固化 TRANSFER_RUNBOOK)

- web 轮:401(key 变量名坑,harness 默认 OPENAI_API_KEY)
- ent 轮:4096+medium(启动漏带修正 flag → 空响应风暴,单题拖分钟级,give-up 11)
- 共同修复:跑完 `judge.env` + `rejudge_cheap.py`(内置 low+16384)全量重判 LLM 行

## watcher 全自动链路(本线首次全程无人值守)

`/root/watch_ent_rejudge.sh`(PID 1309347):harness 进程退出 → 自动 export judge.env → 重判 → ALL_DONE。跑完到定案零人工干预,复制该模式为后续跑分默认。

## 结论对 SCOREBOARD 的影响

cheap-tier 行双域齐:web 36.3% / ent 36.5%,双双低于 d12 现役(40.0/38.4)→ raw-state 强化路线关闭,营销/README 沿用 d12 现役数字。
