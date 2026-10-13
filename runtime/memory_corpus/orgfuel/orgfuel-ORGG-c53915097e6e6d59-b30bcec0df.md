---
name: orgfuel-ORGG-c53915097e6e6d59-b30bcec0df
description: "判读档判例 2026-06-22-compass-convergence-slices · 切片 A · verdict"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c53915097e6e6d59
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-compass-convergence-slices · 切片 A · verdict 数据订正 + 口径解耦(齿轮③·先做·关键路径)
## 切片 A · verdict 数据订正 + 口径解耦(齿轮③·先做·关键路径)

**为什么先做**:uplift 见证(胜负手)依赖验证可信。score=0 盖通过章会污染"提升信号"。

**A.1 作废 bvh_001(数据·backup-first)**
- 凭据:`psql 'postgresql://nautilus_user:nautilus2024@127.0.0.1:5432/nautilus_production'`(经 ssh cloud·fail2ban 清后)。
- Step 1 — SELECT 确认:`SELECT task_uid,score,overall_pass,artifacts->'qc'->>'passk_reproduced',artifacts->>'note' FROM fde_verdicts WHERE task_uid='compass_autolab_bvh_001';` 期望 score=0/overall_pass=t/passk_reproduced=0.0。
- Step 2 — backup:`\copy (SELECT * FROM fde_verdicts WHERE task_uid='compass_autolab_bvh_001') TO '/tmp/bvh_001_verdict_backup_20260622.tsv'`(+ 已有 `/tmp/autolab_bogus_verdicts_backup_20260621.tsv`)。
- Step 3 — UPDATE:`UPDATE fde_verdicts SET 
