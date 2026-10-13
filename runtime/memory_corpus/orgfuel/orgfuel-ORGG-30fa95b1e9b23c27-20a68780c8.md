---
name: orgfuel-ORGG-30fa95b1e9b23c27-20a68780c8
description: "判读档判例 CLOUD_DAEMON_ROOTCURE_PLAN_20260930 · 五 · 实施顺序(零生产试错) "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-30fa95b1e9b23c27
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 CLOUD_DAEMON_ROOTCURE_PLAN_20260930 · 五 · 实施顺序(零生产试错)
## 五 · 实施顺序(零生产试错)

1. **本地**:patch v3.2(numpy 化+预算+listen 前置)→ compile+单测(转换等价/预算逐出/豁免);合成语料压测(75 项目×N 条目)全绿
2. **云端蓝绿**:新实例起 :9877(同 pkl 目录只读)→ J4/J5/J6 在蓝实例验证
3. **切换窗口**:**10/1 08:53 记忆判据终读数之后**(避开读数),systemctl 切 9877→9876,20min 观察 J1-J3
4. **回退保底**:kill 蓝实例即回原状(零动作);9/22 原版 bak 保留至 J1-J3 连续 48h 绿
