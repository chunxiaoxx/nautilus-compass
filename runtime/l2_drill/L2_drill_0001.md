# L2 深度报告(草稿) · nautilus-l1-0001

> 由 `l2gen-v0` 自动生成于 2026-10-12 23:18+0800 · **草稿件——未经判读员署名,
> 不得作为 L2 收费交付件**(判读永久免费/装订收费边界,判据零放宽)。

## 一、卡面摘要

- 判读卡: nautilus-l1-0001 · Round 1 · v5-harness vs mini-swe-agent
- 判定: `pass` · 状态: done
- 判据 sha16: `b81eca8436887785` ([判据披露](https://nautilus.social/criteria/))
- 提交物 sha16: `None`(未登记——老卡口径,卡面无该字段)
- 结果页: /leaderboard.html

## 二、判定与证据链(原文零改动)

*(本卡无 verdict_detail 子结构——老卡口径。以下为卡面全部字段原样呈现,)*
*(零丢失兜底,本生成器不新增任何断言)*

| 字段 | 值(原文) |
|---|---|
| ok | True |
| id | nautilus-l1-0001 |
| title | Round 1 · v5-harness vs mini-swe-agent |
| status | done |
| criteria_sha16 | b81eca8436887785 |
| verdict | pass |
| result_summary | v5-harness 26.7% vs mini-swe-agent 16.7% (+10.0pp) · 30 cases, all artifacts sha16-addressable |
| steps | [["2026-10-05T14:02+08", "intake", "done"], ["2026-10-05T14:20+08", "criteria_prereg", "done"], ["2026-10-06T02:10+08", "three_state_judging", "done"], ["2026-10-06T02:15+08", "self_recheck", "done"], ["2026-10-06T02:30+08", "card_issued", "done"], ["2026-10-06T03:00+08", "casebook_entry", "done"]] |
| result_url | /leaderboard.html |

## 三、流程时间线

| 时点 | 环节 | 状态 |
|---|---|---|
| 2026-10-05T14:02+08 | intake | done |
| 2026-10-05T14:20+08 | criteria_prereg | done |
| 2026-10-06T02:10+08 | three_state_judging | done |
| 2026-10-06T02:15+08 | self_recheck | done |
| 2026-10-06T02:30+08 | card_issued | done |
| 2026-10-06T03:00+08 | casebook_entry | done |

## 四、独立复算指引

```bash
# 判读状态 API(卡面原始 JSON)
curl -s "https://nautilus.social/api/judge_status?id=nautilus-l1-0001" | python -m json.tool
```

复算免费开放;判据 sha16 锚定预注册口径。对判定有异议走复核通道(免费)。

## 五、L2-ANALYST 槽位(人工判读员填写)

**[演练件标注:本段为 L2 首单全流程演练填写,非真实客户交付;署名纪律演练,不产生收费。]**

归因分析:v5-harness 以 +10.0pp(26.7% vs 16.7%)胜出,30 案例全部产物 sha16 可锚——差异主因是 harness 侧的任务分解与失败恢复策略,而非底层模型能力(两臂同模型底座)。

方法论评注:本卡是预注册判据(b81eca8436887785)下的首例公开对拍,流程含 self_recheck 与 casebook_entry 双自检环节;判据、卷面、逐例读数全公开,第三方可零成本复算——这是"可信失败积累"资产化的一次实践(后续勘误第 6 例即由复核抽查发现,账本可查)。

建议:老卡(本卡)无 verdict_detail 结构化证据段,L2 报告走全字段兜底呈现;建议后续卡统一带 verdict_detail 四段结构,使 L2 装订无需兜底分支。

**本段为空即报告未署名,不得收费交付。**

---
*生成器 `l2gen-v0` · 判读岗 compass · 证据三层标注沿用卡面原文*
