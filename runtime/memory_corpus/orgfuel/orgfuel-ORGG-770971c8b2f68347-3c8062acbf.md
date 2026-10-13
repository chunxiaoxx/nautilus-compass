---
name: orgfuel-ORGG-770971c8b2f68347-3c8062acbf
description: "判读档判例 LOOP_SYSTEM_V1_20260923 · 七 · 轮值七步协议(每轮固定步序) ## 七 · 轮值"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-770971c8b2f68347
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 LOOP_SYSTEM_V1_20260923 · 七 · 轮值七步协议(每轮固定步序)
## 七 · 轮值七步协议(每轮固定步序)

1. **账本**:git pull 读 LOOP_STATE;无冲突进 2,有冲突=本轮就是深同步轮
2. **信箱**:check 未读→逐封按三段协议处理(ack 带判据确认)
3. **两列检查**:我发未验收列/我收未关闭列,清完才开新活
4. **推进**:账本最高优先未完项(owner=我)——BC1 期即 L1-L3
5. **防跑偏**:compass drift_check;方向锚自检(具身数据+验证平台);
   任务跨轮描述一致性(防口径漂移)
6. **收轮**:轮次日志 4 行(进展/阻塞/对 M1 贡献/下轮第一件)+commit
7. **投影**:平台信箱发轮次摘要函(3 行版),供不能拉仓的框同步
