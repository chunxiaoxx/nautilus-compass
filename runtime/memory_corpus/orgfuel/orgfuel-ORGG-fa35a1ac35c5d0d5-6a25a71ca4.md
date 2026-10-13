---
name: orgfuel-ORGG-fa35a1ac35c5d0d5-6a25a71ca4
description: "判读档判例 2026-09-18-10verdict-recompute · 系统性读数 ## 系统性读数  1. **"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fa35a1ac35c5d0d5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-18-10verdict-recompute · 系统性读数
## 系统性读数

1. **C2 违例 5/10**:4158/4159/4162(ev=true, external_verified_at 聚簇
   2026-08-25 20:56:56-14,7 行 18 秒内=程序化批量)+ 4380/4384(8/29 批,试点已证
   手工置位)。外部来源排查:verification_logs **全表 0 行**、audit_log **全表 0 行**、
   org_mailbox 8/25-8/30 无复算主题函 → ev=true 无任何外部复算者痕迹,行内亦无
   verifier 身份字段 → 生产者自置成立,与 9/15 试点病灶同款。
2. **C3 违例 2/10**:4380/4384(两条件均为三模型批)turn 内 usage 非零而
   total_tokens=0 且 provider_used 缺失——聚合字段失效,元数据自相矛盾。
3. **C1 结构债 10/10**:行内 items=[] 全量(写入器回归在旧格式行未修);本轮
   可复算性全部经由函 280 指针链达成(verdict_id→evidence 档名确定性映射→仓内
   commit→worktree 重跑)。指针链 10/10 唯一解析,无一处歧义(含三臂/四臂口语名)。
4. **skip 标签保真 1/3**:x8f1d 精确复现;f08c/d821 的 fixture_broken_red 复现为
   "无红"——结局一致、病因标签不准。
5. 置观:e8dd 档内 winning_diff 的 index 行为占位哈希(1111111..2222222),内容
   语义已被 ref 绿灯独立证实,属档格式
