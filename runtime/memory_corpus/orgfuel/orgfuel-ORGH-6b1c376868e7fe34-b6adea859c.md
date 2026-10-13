---
name: orgfuel-ORGH-6b1c376868e7fe34-b6adea859c
description: "工具决策记录 l2_report_gen.py L2 深度报告生成器 v0(T5.2 · 2026-10-09 R436"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6b1c376868e7fe34
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 l2_report_gen.py
L2 深度报告生成器 v0(T5.2 · 2026-10-09 R436)。

定位:从 judge_status API 的 done 卡自动生成 L2 报告**草稿**(骨架+数据零丢失填充),
人工判读员段留槽位——生成物未经判读员署名不得作为 L2 收费交付件(判读免费/装订
收费两线定价的边界纪律,见 docs/metering 判分两线定价档)。

判据(预注册 v0):
  G1 渲染零丢失: verdict_detail 全字段原文入报告
  G2 sha 一致:   criteria_sha16 + submission 原样呈现
  G3 人工槽位:   L2-ANALYST 段+未署名不得收费声明
  G4 非 done 拒绝: status != ok/done 时 ValueError
  G5 证据层保真: [实测]/[推断]/[不可验] 原样保留,本工具不产生新断言

用法:
  python tools/l2_report_gen.py nautilus-l1-0002                # 打印到 stdout
  python tools/l2_report_gen.py nautilus-l1-0002 -o report.md   # 落盘
  python tools/l2_report_gen.py nautilus-l1-0002 --base URL     # 自定 API 基址
