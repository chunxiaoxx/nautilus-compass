---
name: orgfuel-ORGD-ca86845d0d9ce7c8-a73d54dcaf
description: "[## 读数注记(判分纪律呈现)] - **口径**:resolved=官方 swebench harness(FAIL"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-ca86845d0d9ce7c8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 读数注记(判分纪律呈现)] - **口径**:resolved=官方 swebench harness(FAIL_TO_PASS+PASS_TO_PASS 全过);判分环境=独立 A100(非实现者隔离);抽查 ≥6 题/臂复核一致(12/12 零不符);2 题镜像 EOF 已双臂补跑折入,终版环境层归零;
- **污染 caveat(附录 A)**:SWE-bench Verified 已被 OpenAI(2026/2)停引(污染证据链);本榜读数=**同模型双臂 harness 编排差分**,非模型能力绝对值;
- **双臂归因(终版)**:格式层 A 15/B 11 全定性 [实测](malformed hunk 结构;v5 管线病灶=repo 外新增文件入 diff+尾换行,mini-swe-agent 亦有 malformed);归因简报(9838/9842)已送 v5,尾换行"确定性成因"表述勘误见上;Round 2 前修复三件(尾换行补齐/路径过滤/smoke 门),25 题格式 error 作回归集;
- 抽查读数(含"解在题面"标注):分层抽 6 题/臂(12 题,含 4 题双臂同题对照),状态↔preds 逐题一致零不符;"解在题面"污染扫描(30 题全量,gold patch 新增行子串检测 [推断]):弱命中 2 题(django-14855 两行/matplotlib-26291 一行,均为常见惯用代码行,不构成污染证据,如实披露;升级路径=人工 hunk 上下文比对)。
