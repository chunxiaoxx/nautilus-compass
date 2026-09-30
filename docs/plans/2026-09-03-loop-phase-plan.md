# LOOP 阶段规划(2026-09-03 立 · 用户令:阶段目标+任务清单+持续推进)

> 执行锚:每轮 LOOP 按此文档顺序推进栈顶一件。GOAL_SSOT N5/N6 是目标真相源,本文是执行排程。

## 阶段 1 · A 臂判定(今天上午,自动)

| 任务 | 判据/产物 |
|---|---|
| #27 A 臂 500 题出数→三态判定 | 预注册 `docs/plans/2026-09-02-summary-layer-preregistration.md`:ms≥35/ssa≥40/tr≥30(锚 22.6/25.0/15.8);PASS/PARTIAL→刷 README e2e 段+GOAL_SSOT+memory;FAIL→归因文档 |

## 阶段 2 · T0 官方成绩册(9/12 前 · 当前主战线)

| # | 任务 | 产物 | 依赖 |
|---|---|---|---|
| #30 | 上游 license 三待查项 | HF dataset license 字段 / leaderboard baseline 公开数字 / 提交包格式(leaderboard/README.md) | 网络通(代理不稳就重试) |
| #34 | judge 口径决策材料 | 官方 gpt-5.2 复跑成本估算(451 题×2 域 judge 调用)+差异声明方案对比,呈用户拍板 | leaderboard 格式 |
| #29 | 自研部分打包 | compass backend(LME-V2 官方接口实现)+判分修正工具(rejudge)+摘要卡生成器+协议文档→可安装包(GitHub repo 骨架) | 无 |
| #31 | 成绩册文档 | 对比表(上游锚 frontier ≤14.1% / untuned 19.6/12.8 / tuned 40.0/38.4 双口径)+判分修正故事+attribution | #30/#34 |
| #32 | 判分协议 v1.0 | PROTOCOL.md 定版(成绩卡 JSON schema+提交规则) | 无 |
| #33 | 发布动作 | GitHub 发布+leaderboard 提交+营销帖 | 🔴 用户拍板 |

## 阶段 3 · 并行挂起件(阶段 2 空隙或新 session)

- P2 多租户 MVP 6 件(HANDOFF_20260831 · 破零外部用户唯一路径 · 3 工作日 · 建议新 session)
- 三支柱 9/15 验收件:消费者矩阵测试文件化、日报自证行连续
- 营销第一帖(数字门已开,发布需拍板)

## 阶段 4 · T1 NautilusMem 自创新题(9 月中下旬启动)

前瞻/反事实/任务落地/容量压力四类原创题(世界模型视角+SFT/RL 飞轮接口),attribution LME-V2 轨迹源(依赖 #30 的 HF license 结论)。

## LOOP 规则(不变项)

每轮只做栈顶一件;对外发布/GPU/花钱必等用户;凌晨跑批不杀 python;A 臂分片进程勿动;任务完成即 TaskUpdate;阶段 1 完成自动进入阶段 2 顺序。
