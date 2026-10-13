---
name: orgfuel-ORGG-fac65b476fa7a8cc-21f434492b
description: "判读档判例 L1_CRITERIA_FREEZE_NOTES_20261005 · 二、GAIA ## 二、GAIA  "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fac65b476fa7a8cc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 L1_CRITERIA_FREEZE_NOTES_20261005 · 二、GAIA
## 二、GAIA

- **上游正本**:HF `gaia-benchmark/GAIA`(450+ 题,validation 165 题公开含答案/test 集答案不公开走官方 leaderboard;gating 防爬,不转载题面);官方 scorer 随数据集卡。
- **criteria_version v1 冻结口径**:主指标=**exact match**(官方 scorer 口径:数字/字符串规范化匹配);主轨=**validation 165 实测**(compass 自跑可复算);test 成绩只收官方 leaderboard 截图/URL,标 [不可验] 挂引用不入名次(UNVERIFIABLE 墙);level 1/2/3 分层申报;agent 工具栈(搜索/代码执行)配置随成绩行公示。
- **污染风险与对策**:①题面公开+2023 发布——对策:cutoff 晚于 2023 者标注"记忆风险",优先引用其在 test 官方榜成绩作交叉;②爬虫禁令——对策:compass 不转载题面,测评环境内用后即弃,成绩行只报数与配置;③工具差异——对策:是否联网/执行沙箱两项强制披露。
- **U 态条款**:scorer 口径变动未复跑=转观察区。
