# compass 分框对照自查表(23241 全员令·48h 回函)

> 🔴 **勘误指针(2026-10-29 R187)**:本档为并行会话早期草稿,部分结论已过时——"区分度三指标未入 gate5"不实,gate5 v2(R183 commit 2fe77b08)已实装⑥门调 discrimination_jaccard.signature_gates(ops/ali30q/gate5.py:163-178)[实测]。**正本对照以 `ops/ali30q/GATE5_CHARTER_ALIGNMENT_20261029.md`(亲读代码逐项比对版)为准**,本档仅存档。

> 框: compass · 职能: 判据工程化(gate5)+独立判读卡+判分值守
> 正本: nautilus-core docs/feishu/两正本(需求1145行+质检1677行)·亲读状态: 质检方案部分段已读/需求文档部分段已读/剩余段落本轮补完

## compass 负责条款面

| 条款 | 内容 | compass 在产工作 | 符合/差距 | 修正动作+工时 |
|---|---|---|---|---|
| §3.3.1 UT字段 | id/ut_name/turn/dimension/description/criterion_necessity/judge_type/evidence_required | gate5 判定器按五条件判 | 差距: ut_index [[metadata.ut_index]] 部分题缺 | v5 补 |
| §3.3.2 数值约束 | UT>20·badpattern UT≥2·三维度·判分确定性·禁注水·禁表述锁定 | gate5 六门含UT数检查 | 差距: 判分确定性(连跑3次100%一致)未验证 | 补验证脚本 30min |
| §3.3.3 三必需维度 | 语义正确性+改一查十+单轮反幻觉 | pipeline_report 有三维度标注 | 差距: 部分题三维度未全覆盖 | 逐题核查 2h |
| §3.3.4 证据链 | evidence_required per UT | 未实现 | **缺口**: 未建 | 脚本化 1h |
| §3.6 基线试测 | 五模型×4轮·整体<70%·opus∈[1,3]·qwen双低+passrate∈{25,50}·区分度三指标 | gate5 已实现五条件 | 差距: 区分度三指标未入 gate5 | 接入 discrimination_jaccard 30min |
| 首部判分原则 | 全对记1否则0·不设gating/权重/LLM judge | gate5 按此实现 | ✅ 符合 | — |

## 回函

compass 分工确认：判据工程化(gate5)+独立判读卡+判分值守。不做：出题、调档设计。
差距三条(UT确定性验证/evidence_required脚略/区分度三指标接入)今日修正。
素材主线： 卡1·题2(513+004B)·门0(待opus方差带实测)。

—— compass · 2026-10-29
