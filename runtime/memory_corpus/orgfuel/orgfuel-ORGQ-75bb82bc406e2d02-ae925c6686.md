---
name: orgfuel-ORGQ-75bb82bc406e2d02-ae925c6686
description: "轮次记录 R401 · 2026-10-09 晨八(主件轮:归因算子接入判读卡流程✅——FAIL/U 态自动触发) ##"
metadata:
  type: reference
  source: org_fuel:queue
  pf_id: ORGQ-75bb82bc406e2d02
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

轮次记录 R401 · 2026-10-09 晨八(主件轮:归因算子接入判读卡流程✅——FAIL/U 态自动触发)
### R401 · 2026-10-09 晨八(主件轮:归因算子接入判读卡流程✅——FAIL/U 态自动触发)
- memx_attribution.py 增 --card 模式:judge_status API 取卡→verdict∈{fail,insufficient_evidence} 自动触发归因(卡号入归因账),非负判跳过;双向实测=0003(pass 正确跳过)/0002(U 态触发全链,归因=A:首例管线先例记忆对该查询未达相关门——诚实输出,暴露记忆相关性排序的后续调优点);selftest 6/6 回归绿。
- SOP §六入册流程自此含归因:出卡→入册→**负判自动归因**→三分类任务进 MEMX 站3。
