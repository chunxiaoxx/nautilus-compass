---
name: orgfuel-ORGQ-R318-dcd9acf874
description: "### R318 · 2026-10-08 凌晨(部署窗阻断解法:dedup 索引方案+153 组定性) - **105"
metadata:
  type: reference
  source: org_fuel:gate_passed
  pf_id: ORGQ-R318
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

### R318 · 2026-10-08 凌晨(部署窗阻断解法:dedup 索引方案+153 组定性)
- **10502 阻断**(对冲不删行→唯一索引 974 组仍违规)→**第四种方案 a+ 双腿标记**(10507):apply 事务内被冲正行同标 .dedup(元数据可逆/凭证保全/执行器仅 UPDATE 加一列)+部分唯一索引(排 hr/stake/.dedup 四谓词);apply 后违规组期望 0;(b) 单独窗多余/(c) 删行永不维持。
- **10505 定性[实测]**:残留=prime-001 737+v5 85+kairos 等 152(同 agent 三连发真实重复,样本 12/12)——**全在 974 冲正清单内**,无第三类新增;三假说裁决=归并对齐✓+真实重复✓(但非增量)+hr 豁免独立。
- 10503 迁移窗三件办结 ack;bounty_settlement 唯一路径兑现。
