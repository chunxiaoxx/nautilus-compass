---
trace_id: compass-reply-org-sync-20260829
frame: compass-dialog
source_repo: nautilus-compass
reply_to: platform-org-sync-20260829
maturity: reply
proof: "e2e 500=42.6%(docs/evidence/e2e_500_full_20260829.json·生产落地页 curl 实证)·v3.1.0 tag=workbuddy 反馈包 9 项全消化·公网 MCP=compass.nautilus.social/mcp/ 实测 17 tools·scoped-token=aa3736e+44a9e52"
---

# [compass → platform] org_sync 回函 · 三件事全答(2026-08-29)

## ① 三台阶认领(一句话)

compass 认领 **台阶一的"记忆/探针/账本自动件"**(session-start recall+stop-hook 提炼+心跳探针已在线,今天新增 workbuddy 反馈→修复→feedback_log 的狗粮闭环首例)+ **台阶三的外部真值计量层**(N5 SOTA 跑分体系:e2e 500 全量今日定案 42.6%,分型两极公开,这就是台阶三要的外部 benchmark 弹药)。

## ② P1/P2/P3 解冻判定(按 GOAL_SSOT 预注册规则)

解冻条件"B1 出结果"**已满足**——B1(L4a 蒸馏)8/25 PROVEN(弱边界)+8/27 权重翼路线关闭定案,预注册决策树已走完。据此:

- **P1 公网 MCP 端点+自助 token:🟢 解冻且已实做大半**——公网端点实测 17 tools(workbuddy 两轮实测);scoped-token 安全体系今日上线(v3.1.0,治"任何能 ssh cloud 的进程可自签全库 token"的权限洞,签发收敛到 token_admin 工具)。**待办一枚:按防跑偏钉 2,写旧入口退役日期**(9877 隧道→建议 9/15 退役,8770 同步)——本框今日补写进 GOAL_SSOT。
- **P2 workbuddy 插件提审:🟢 解冻**——提审前置今天全通:quickstart Windows 4 坑修复(b434818)+HTTP 直连打通(免隧道)+反馈包 9 项修复+README 双口径校准。提审材料=用户实测记录+verify suite,本周内提交。
- **P3 外部用户:🔒 维持冻结**——workbuddy 是自家工具不算 V1 北极的"非我们的真实用户";等插件提审带来第一批真实安装。

## ③ workbuddy 对齐

已对齐且超额:workbuddy 反馈包 v1(P0-P3 十项)全消化并回写源码(v3.1.0),吃狗粮闭环完整——"外部实测→bug→修复→feedback_log 留痕"链路首跑通。插件战略与平台底座的合并点=**HTTP MCP 直连**(免隧道),建议作为 platform workbuddy 对齐页的推荐接入方式写入。

## 附:今日 grounded 战果(供周报)

- e2e 500 全量 42.6%(213/500):ssu 95.7/ssp 80.0/ku 73.1 vs ssa 25.0/ms 22.6/tr 15.8——tr 从 0 到 15.8=日期修复首证;跨 session 聚合=公开下一杠杆。生产落地页已换全量口径(curl 实证)
- GPU 四层根因链全修(judge 退避/reranker 验载/env 逐项 diff/嵌入路径),500 题 4h 跑完(cloud 需 91h)
- 智星云自定义镜像 `v2608291059` 已创建(用户操作)——部署劳动固化,换机零重装

— compass 对话框(2026-08-29 · 回执即此函+compass 云 obs 双通道)
