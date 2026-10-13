---
name: orgfuel-ORGM-da798fea001783aa-f3bc454895
description: "记忆条目 no-jargon-user-correction-20260829.md --- name: no-jarg"
metadata:
  type: reference
  source: org_fuel:memory
  pf_id: ORGM-da798fea001783aa
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

记忆条目 no-jargon-user-correction-20260829.md
---
name: no-jargon-user-correction-20260829
description: "用户纠正:禁用跨框黑话'收棺'(以及同类俚语)——对外/对用户文档一律用'路线关闭定案/结论已定'等平实表述"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 803cee4f-6f04-4ee0-92fd-3ce055d70a29
  fact_status: measured
---

2026-08-29 用户两次批评"收棺"："为何会反复出现这样的错误的词？"

**Why**: '收棺'是 V5/platform 框的内部黑话（负结论关闭的戏称），compass 沿用进了回函/GOAL_SSOT 等正式文档。对用户和外部读者它不可读、不专业、观感差。这不是第一次黑话外泄——'真X'禁用规则（全局 CLAUDE.md）同源。

**How to apply**:
1. compass 框所有文件（回函/SSOT 增量/memory/commit message/回复文本）禁用"收棺"——用"路线关闭定案/结论已定/假设已排除"
2. 引用 platform/V5 原文时若含黑话，转述时翻译成平实表述，不复制
3. SSOT 里 platform 写的历史原文不单方面改（变更协议=canonical 先改），但 compass 自己的增量段落必须干净
4. 推而广之：写任何对外可见文本前过一遍"外人说人话"检查

关联 [[gpu-instance-reuse-not-rent]]
