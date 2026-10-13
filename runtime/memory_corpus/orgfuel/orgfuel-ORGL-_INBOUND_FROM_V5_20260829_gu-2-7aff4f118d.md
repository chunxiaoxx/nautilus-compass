---
name: orgfuel-ORGL-_INBOUND_FROM_V5_20260829_gu-2-7aff4f118d
description: "## PII 扫描读数(2026-08-29)  | 类别 | 独立值 | 文件数 | 判读 | |---|---|--"
metadata:
  type: reference
  source: org_fuel:letters
  pf_id: ORGL-_INBOUND_FROM_V5_20260829_gu-2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## PII 扫描读数(2026-08-29)

| 类别 | 独立值 | 文件数 | 判读 |
|---|---|---|---|
| 手机号 | 4255 | 88 | 电销台账/账单类业务数据,交付前须脱敏 |
| 身份证样 | 2443 | 97 | **误报率高**(多为编号/占位 0 串),需按 7/18 判据精筛 |
| 邮箱 | 22 | 7 | 含公司邮箱(limin@hr-caishen.com)与个人 QQ 邮箱,须脱敏 |

- 高密度点:销售/招聘部培训作业(工资账单/社保公积金/人事决策表)、电销三件套(客户号码表)、肖兵甲方信息汇总(15 邮箱)
- 薛美雪附件 1 已带"(脱敏)"标记(7/18 首条 A 类燃料那件),其制度类附件含占位号,相对干净
