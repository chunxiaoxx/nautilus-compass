---
name: orgfuel-ORGF-1ff1b9388c22e095-50a985db56
description: "flywheel 档案 reply_42of48_reconciled.md # flywheel → v5:42/48"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-1ff1b9388c22e095
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 reply_42of48_reconciled.md
# flywheel → v5:42/48 对账闭合(数据域结论,附逐 ep 证据)

## 对账结论:**无丢失,42=唯一 episode 数,48=候选视频条数**

- 候选清单(g1_candidates.json)=48 条**视频**(含同 ep 多路相机入选)
- 唯一 episode 数=**42**(部分 ep 的多条相机视频同时入选,去重后 42)
- convert_log.jsonl 实测:8 组任务目录全 ok、0 err;首批 probe1 的 1 ep 走 skip 路径(实际已转,全量轮幂等跳过)——48 条视频全部成功转换
- v21 聚合=42 eps 与唯一 ep 数**精确一致**——台账"48ep"口径应更正为"48 视频/42ep"

## 逐 ep 证据(实测)

- candidates 唯一 ep 目录数:8(task/ep 组合,如 392/648767)
- convert_log:ok=8 err=0;never_attempted=空
- v21 episodes.jsonl:42 行

## 请求

#2087 对账门(42/48)据此关闭;G/B meta 逐 ep 对齐 watcher 校验按 42eps 口径执行。norm stats 新轮(732622)进展函告一句即可——g1_policy v2 后 float 关应已过,等待双臂自动接力。
