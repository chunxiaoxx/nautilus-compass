---
name: orgfuel-ORGH-eeb20061f9e93ecb-124a355d82
description: "工具决策记录 f15_glm_leg.py F15 meta-judge · glm 腿:verdict 样本抽取 + "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-eeb20061f9e93ecb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 f15_glm_leg.py
F15 meta-judge · glm 腿:verdict 样本抽取 + glm 复判(queue #12 备料件)。

F15 口径(GOALS_20260930):verdict 5% × 三供应商复判,考官面 SLA 一项。
本脚本=glm 腿(coding plan 宿主 glm-5.3-flash,子进程配方与
rejudge_subprocess_judge.py 同款:清代理+显式输出格式)。

纪律:
- 抽样名单先冻结(seed 固定,sha16 落 manifest)——预注册纪律,开跑前可审计
- 默认 dry-run 只出名单;--go 才调 API(额度窗口到即跑)
- --judge-log 接判分器 verdict log(S1 影子期上线后无缝切生产源)

用法:
  python tools/f15_glm_leg.py --dry-run        # 备好:名单+sha 冻结
  python tools/f15_glm_leg.py --go             # 额度窗口内实跑
  python tools/f15_glm_leg.py --agree          # 读数:一致率表
