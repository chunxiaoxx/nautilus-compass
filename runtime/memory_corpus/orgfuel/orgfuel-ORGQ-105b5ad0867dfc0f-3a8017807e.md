---
name: orgfuel-ORGQ-105b5ad0867dfc0f-3a8017807e
description: "轮次记录 R513 · 2026-10-11 晨(主件轮:8B 全量预跑读数收割✅[实测]——管线四门全过+U5 FAI"
metadata:
  type: reference
  source: org_fuel:queue_r3
  pf_id: ORGQ-105b5ad0867dfc0f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R513 · 2026-10-11 晨(主件轮:8B 全量预跑读数收割✅[实测]——管线四门全过+U5 FAIL(-3.08pp 过拟合信号),负结果照报)
### R513 · 2026-10-11 晨(主件轮:8B 全量预跑读数收割✅[实测]——管线四门全过+U5 FAIL(-3.08pp 过拟合信号),负结果照报)
- **主件=8B 全量预跑读数收割**(A100 过夜跑):U1 873 步满跑零 OOM✓/U2 峰值 16.49G✓/U3 loss 收敛✓/U4 输出合规 100/100✓——**管线四门全过**;**U5 8B 0.8459 vs 现役 0.8767(-3.08pp)FAIL**——8B 不升格,1.7B 维持现役(预注册自动裁定)。
- **关键洞察**:smoke 25 步 0.8801 > 全量 873 步 0.8459——**训练步数与 acc 反向=教科书级过拟合**(1454 条小数据 × 3 epoch);修正配方=1 epoch+early-stop(val acc 每 epoch 测);归因主因=数据量不足(需 3000 真实单棘轮)。
- 读数归档:judge8b_full_r513_upgrade_report.json+配置档§六追加。
- **LOOP 静默期结束确认**:daemon 已恢复(268ms),rerank 生产 ON(2ms 常速),两 watchdog Ready——**全系统回到常速运转**。
