# cheap-tier web vs d12(干净口径)逐题归因 · 2026-09-04

> 对照:两边 llm 行均用 low/16384 重判分(cheap=rejudge_cheap_web_results·d12=d12_rejudge),
> 程序化行取原分。重叠 240/240,d12_clean=96/240(40.0%)vs cheap=87/240(36.25%),净 −9 题。

| question_type | n | both对 | cheap赢 | cheap输 |
|---|---|---|---|---|
| static-environment | 60 | 4 | +1 | **−7** |
| dynamic-environment | 51 | 7 | +2 | 0 |
| procedure | 42 | 24 | +2 | **−5** |
| static-environment-abs | 31 | 13 | +6 | −7 |
| dynamic-environment-abs | 21 | 10 | +3 | −5 |
| procedure-abs | 20 | 5 | +5 | −1 |
| errors-gotchas | 15 | 4 | +1 | −4 |
| **TOTAL** | 240 | 67 | **+20** | **−29** |

## 初步归因(ent 出数前)

1. **伤害集中在非弃答检索型**:static-environment(−7)与 procedure(−5)合计 −12,
   两型主体是程序化 mc 行——三改里的检索侧改动(a11y_chars 500→1500 扩窗 + query_decomp
   子查询 RRF 融合)改变了 mc 题的证据装填,伤了精确率(与既往"rerank 有害/K 无关"教训
   同族:web 域检索栈已近饱和,加法倾向添噪)。
2. **弃答型(llm 行)整体中性偏正**:procedure-abs 净 +4,static-abs −1,dynamic-abs −2。
   更长 a11y 窗对"快照证据不足→拒答"判定有小幅帮助但不抵检索型损失。
3. **dynamic-environment 零回退**(0 输):三改未伤 d12 的强项。

## 终判规则(预注册式,ent 出数后执行)

- ent 也落(cheap_ent < 38.4%)→ **三改组合关闭**,维持 d12 现役,cheap-tier 线归档
  为"失败实验公开"素材(营销第二帖诚实段+SCOREBOARD 备注)。
- ent 超 38.4% → 域特异(web 伤/ent 赚),需拆刀单因子归因再议。
- 数据:`per_question.jsonl.gz`(md5 28286db9)+ `rejudge_cheap_web_results.jsonl`(86 行 0 失败)。
