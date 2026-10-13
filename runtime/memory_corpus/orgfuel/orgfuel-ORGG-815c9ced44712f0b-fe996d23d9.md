---
name: orgfuel-ORGG-815c9ced44712f0b-fe996d23d9
description: "判读档判例 REJUDGE_RECOMPUTE_PREREG_20260930 · 终读数(2026-09-30 · J"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-815c9ced44712f0b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 REJUDGE_RECOMPUTE_PREREG_20260930 · 终读数(2026-09-30 · J6 原样)
## 终读数(2026-09-30 · J6 原样)

- J1(M1 数值 85 题):冲突 0/85 = 0.0% → PASS
- J2(隔离盲判 50 题):一致 48/50 = 96.0% → PASS
  - 分歧 2 条均 partial 口径(6b7dfb22 偏好题缺具体建议 / gpt4_c27434e8_abs
    对抗题给了过度确定性排序)→ 按判据入勘误库,不计 judge 硬错
  - 11 条独立 incorrect 含 7 条 SUBJECT_ERROR 超时(judge 亦判错=一致)
- J3:双绿 → 500 题整族升 labelled(P1 目标 500 达标:labelled 52→552)
- 执行痕迹:三次子进程形态演化(25 题秒退=32K 上限→完整 agent 自主全判
  =盲为声明级→隔离目录版=物理盲);raw_subprocess_out.txt 原样存档;
  盲判为 markdown 报告,解析器提取(qid 表+partial 列表,assert 11/2)
