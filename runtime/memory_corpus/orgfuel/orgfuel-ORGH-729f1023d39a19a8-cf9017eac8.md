---
name: orgfuel-ORGH-729f1023d39a19a8-cf9017eac8
description: "commit 3255a304f7db 2026-09-05 fix(marketing): 深讲版 PPT v3 高对"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-729f1023d39a19a8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 3255a304f7db 2026-09-05
fix(marketing): 深讲版 PPT v3 高对比版式重做——fitz 量化验证渲染产物
根因(fitz 量化,非自报):
- v2 全设计系统无实色区块,内容页非白像素仅 13-16%(用户观感'纯白背景'坐实)
- 7 页大图底边 546-600pt 超出页高 540 被裁 11-15%(用户观感'错层'实锤,v2 检查只验文字块漏检图 bbox)
- PPTX 侧排除:marp 整页栅格化 2560x1440 无拉伸

修复:
- 实色页眉带(62px 深绿)+白字幕名替代悬浮 kicker;pageno 幕序
- 卡片实色底(浅绿/蓝/红/黄)+深色顶边;表格深色表头白字;panel 要点面板
- 封面/幕分隔/收尾 9 页整页品牌渐变色块(非白 100%)
- 8 图重渲非纯白底+统一装裱居中;大图改高度约束 h:372 绝不溢出
- 内容页文字/panel 补强(三不变量/FAQ/结论块)

验证(fitz 渲染产物量化):全页非白 22%->40.1%,内容页 13-16%->24.2%,图被裁 7->0,文字越界 0

Generated with [Claude Code](https://claude.ai/code)
via [Happy](https://happy.engineering)

Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Happy <yesreply@happy.engineering>
