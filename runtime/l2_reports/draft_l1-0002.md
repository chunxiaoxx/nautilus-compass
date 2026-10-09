# L2 深度报告(草稿) · nautilus-l1-0002

> 由 `l2gen-v0` 自动生成于 2026-10-09 21:12+0800 · **草稿件——未经判读员署名,
> 不得作为 L2 收费交付件**(判读永久免费/装订收费边界,判据零放宽)。

## 一、卡面摘要

- 判读卡: nautilus-l1-0002 · L1 selftest-claude-code v1.0.0 · 平台自检单(管线首例)
- 判定: `insufficient_evidence` · 状态: done
- 判据 sha16: `5c8e0a7ce3a0048b` ([判据披露](https://nautilus.social/criteria/))
- 提交物 sha16: `72fdcb665e79482b`
- 结果页: /leaderboard.html

## 二、判定与证据链(原文零改动)

### 被测元数据

[实测] repo=anthropics/claude-code HTTP 200(149820 stars);version_anchor=1.0.0 npm 口径可锚(git tag 无——单未声明锚口径,披露)

### 评测证据

[实测缺失] 任务集读数(SWE-bench Verified resolved%)=零;评测产物=零;模型配置/采样参数=零

### 三态判定

insufficient_evidence —— 无可判读评测读数;单据自述『平台自检单,非真实评测需求』与证据状态一致

### 处置

不予收录(不进名次区/观察区);管线 intake→judging→delivered 首例走通;可携评测产物重提走正常判读

## 三、流程时间线

| 时点 | 环节 | 状态 |
|---|---|---|
| 2026-10-08T12:01+08 | intake | done |
| 2026-10-08T16:30+08 | criteria_prereg | done |
| 2026-10-08T16:35+08 | metadata_check | done |
| 2026-10-08T16:40+08 | three_state_judging | done |
| 2026-10-08T16:45+08 | card_issued | done |

## 四、独立复算指引

```bash
# 判读状态 API(卡面原始 JSON)
curl -s "https://nautilus.social/api/judge_status?id=nautilus-l1-0002" | python -m json.tool
```

复算免费开放;判据 sha16 锚定预注册口径。对判定有异议走复核通道(免费)。

## 五、L2-ANALYST 槽位(人工判读员填写)

<!-- TODO-L2-ANALYST: 归因分析 / 上下文背景 / 方法论评注 / 建议 -->

**本段为空即报告未署名,不得收费交付。**

---
*生成器 `l2gen-v0` · 判读岗 compass · 证据三层标注沿用卡面原文*
