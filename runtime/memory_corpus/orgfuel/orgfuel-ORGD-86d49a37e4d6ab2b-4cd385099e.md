---
name: orgfuel-ORGD-86d49a37e4d6ab2b-4cd385099e
description: "[### 10.2 demo 动态演示方案(现场 live + 录屏兜底)] - **D1 跨会话记忆**:三个会话里分"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-86d49a37e4d6ab2b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 10.2 demo 动态演示方案(现场 live + 录屏兜底)] - **D1 跨会话记忆**:三个会话里分别说三件事→第四个会话问跨会话问题→答对(对照:清掉记忆后同样问题答不出)
- **D2 多 agent 记忆胶囊**:agent A 解题 reward 1.0→写胶囊→agent B 直接继承(B 从 FAIL→PASS 的实录复刻)
- **D3 安全四探针**:现场跑 probes.py 打生产端点,四绿大屏(隔离/撤销肉眼可见)
- 录屏兜底:发布会前一周录制 1080p 三段;现场网络/环境故障即切录屏
- 技术准备:demo 专用干净 profile+预置会话数据脚本+恢复脚本(现场可重置)
