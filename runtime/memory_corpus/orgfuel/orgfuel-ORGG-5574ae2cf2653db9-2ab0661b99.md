---
name: orgfuel-ORGG-5574ae2cf2653db9-2ab0661b99
description: "判读档判例 JUDGE_UPGRADE_7B_FIRSTRUN_20261004 · 四 · OOD 400 题补跑读数"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-5574ae2cf2653db9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 JUDGE_UPGRADE_7B_FIRSTRUN_20261004 · 四 · OOD 400 题补跑读数(验收③,[实测])
## 四 · OOD 400 题补跑读数(验收③,[实测])

- 脚本:`tools/e1_j2_batch_judge_ood_7b.py`(3B OOD 版仅四处改:模型路径/输出名/CSV 名/署名,判据与 PROMPT 逐字零改动)
- dim1:未动 172 / 部分 226 / **完成 2**——**三态全非零**;且"完成"在 OOD 集出现、主包为 0,与判读发现 1 互证(主包"完成=0"=材料无完成帧的分布属性,非判官缺陷) [实测]
- dim2:无法判断 176 / 异常 219 / 正常 5;dim3 低 395(置信保守与主包同型)
- pos/neg 方向自洽且与 dim1 内部一致:pos 全否 400,neg 是 398/否 2——2 条 neg=否恰对 2 条 dim1=完成 [实测]
- 与 3B OOD 同 id 对照(400/400 交集):dim1 一致 56.5%(3B 全"部分"单态→7B 三态分化);dim2 一致 11.2%(3B 正常 332→7B 异常 182+无法判断 145,仅 5 保持正常)——**翻转幅度大于主包,归因同判读发现 2(画面-标称一致性严格执行),OOD 分布外材料失配更普遍故幅度更大** [实测+推断(归因)]
- 启动过程留痕:pgrep -f 自匹配假阳性两轮(RUNNING 假信号,log 空坐实未启动)→`[e]` 修法重启→完成;轮次考古以远端实物(log 全程+[done] 行)为准 [实测]
