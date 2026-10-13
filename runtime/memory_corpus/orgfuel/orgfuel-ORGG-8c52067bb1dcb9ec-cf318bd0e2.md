---
name: orgfuel-ORGG-8c52067bb1dcb9ec-cf318bd0e2
description: "判读档判例 JUDGE_UPGRADE_PREP_20261004 · 三 · 人类抽检标定协议(草案) ## 三 · "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-8c52067bb1dcb9ec
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_UPGRADE_PREP_20261004 · 三 · 人类抽检标定协议(草案)
## 三 · 人类抽检标定协议(草案)

- **目的**:给判官读数一个"与人类一致性"锚,补 AI 判官透明申报的最后一环。
- **抽样框**:主包 498 帧分层抽 60(dim2 三置信层按 v4 读数分层:高/中/低各 20;低置信层 oversample——错也错得有信息)。
- **双盲**:标定人不看判官输出;标定判据=E1 判官须知原文(同一份,防判据二义)。
- **门槛(建议,启动时由组织方裁)**:一致性 ≥80%(Cohen's κ≥0.6)→判官读数获"人类标定"背书;<80%→差异题逐题归因(判据二义/判官错/材料歧义三类),归因报告先出再议。
- **成本**:60 题×人工≈2-3h(组织方或第三方人力);判读方(我)出材料包+汇总,不参与标定(独立性)。
