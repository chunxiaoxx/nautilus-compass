# L2 深度报告(草稿) · nautilus-l1-0006

> 由 `l2gen-v0` 自动生成于 2026-10-12 23:18+0800 · **草稿件——未经判读员署名,
> 不得作为 L2 收费交付件**(判读永久免费/装订收费边界,判据零放宽)。

## 一、卡面摘要

- 判读卡: nautilus-l1-0006 · Intake pipeline selftest · compass-pipeline-selftest@v1(开业日演练单)
- 判定: `insufficient_evidence` · 状态: done
- 判据 sha16: `5c8e0a7ce3a0048b` ([判据披露](https://nautilus.social/criteria/))
- 提交物 sha16: `8b97795ac55b4b5d`
- 结果页: /intake.html

## 二、判定与证据链(原文零改动)

### 被测元数据

[实测] repo=chunxiaoxx/nautilus-compass 公开可锚;harness=compass-pipeline-selftest@v1;lane=l1;submission=8b97795ac55b4b5d(is_smoke=true 自动标记)

### 评测证据

[实测缺失] 评测任务集读数=零;评测产物=零;note 自述『开业前管线端到端演练单,自检性质』与证据状态一致

### 三态判定

insufficient_evidence —— 无可判读评测读数;演练目的是验证 GRACE 期 intake→受理→派单链路(非真实评测需求),与证据状态一致

### 处置

不予收录(不进名次区/观察区);演练成果=intake 端到端全链实测通(HTTP 200/is_smoke 自动标记/SLA 自动计算);可携评测产物重提走正常判读

## 三、流程时间线

| 时点 | 环节 | 状态 |
|---|---|---|
| 2026-10-10T04:23+08 | intake | done |
| 2026-10-10T04:25+08 | criteria_refer(5c8e0a7c 同构自检单判据引用,零放宽) | done |
| 2026-10-10T04:30+08 | metadata_check | done |
| 2026-10-10T04:35+08 | three_state_judging | done |
| 2026-10-10T04:40+08 | card_issued | done |

## 四、独立复算指引

```bash
# 判读状态 API(卡面原始 JSON)
curl -s "https://nautilus.social/api/judge_status?id=nautilus-l1-0006" | python -m json.tool
```

复算免费开放;判据 sha16 锚定预注册口径。对判定有异议走复核通道(免费)。

## 五、L2-ANALYST 槽位(人工判读员填写)

<!-- TODO-L2-ANALYST: 归因分析 / 上下文背景 / 方法论评注 / 建议 -->

**本段为空即报告未署名,不得收费交付。**

---
*生成器 `l2gen-v0` · 判读岗 compass · 证据三层标注沿用卡面原文*
