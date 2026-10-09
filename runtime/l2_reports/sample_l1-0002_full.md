# L2 深度报告(草稿) · nautilus-l1-0002

> 由 `l2gen-v0` 自动生成于 2026-10-10 00:37+0800 · **草稿件——未经判读员署名,
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

> ⚠️ 本段为**管线演练示例**(R449 干跑),演示 L2 报告的成品形态;真实交付须由值勤判读员对当单独立撰写并署名。

**归因分析** [实测+推断]:本单判定为 insufficient_evidence 的直接原因是评测证据三要素全缺(任务集读数/评测产物/采样配置均为零,见第二节原文)——提交物 sha16 `72fdcb66` 对应的自检单本身不含可判读评测内容,与单据自述"平台自检单"一致。**推断**:该单为管线首例验证件而非评测诉求,判定与证据状态吻合,无判读争议空间。

**方法论评注**:此单的价值在管线而不在判定——intake→criteria_prereg→metadata_check→three_state_judging→card_issued 五环 4h44m 全链走通,且被平台独立复现(verdict/criteria_sha16 逐项命中)。它同时是三态判读的示范:当证据不足时,判"判不动"(insufficient_evidence)比硬判 pass/fail 更诚实——这正是 U 态纪律的活教材。

**建议**:提交方如需真实评测判读,按 intake 页 L1 通道携产物重提(判据 sha 重新锚定,与本次自检单互不污染)。

**判读员**(演练签):compass 值守轮 · 本段为样例,不构成收费交付件。

**本段为空即报告未署名,不得收费交付。**

---
*生成器 `l2gen-v0` · 判读岗 compass · 证据三层标注沿用卡面原文*
