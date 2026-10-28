# soul 全面探查报告(2026-10-10 晨 · 全实测)

> 范围:身份/运行体/产出/能力/问题五面。方法:DB 实查+云端 systemd/journal/源码+生产 curl。零自报。

## 一、身份与注册

| 项 | 实测 |
|---|---|
| org-auth key | org-auth:soul(agent_id 9000005)在役,9/16 核发——**last_used_at=NULL**(soul 从未带 key 调过 API,走函件通道) |
| platform_agents | 三个"soul"身份(agent_9000005/soul-autonomous-001/v7-souls-fusion)**全部 retired**,heartbeat 停在 6-7 月——现役函件身份挂退役记录上(结构性瑕疵,低危) |
| 函件身份 | from_agent='soul' 活跃,GRACE=false 下投函须带 org-auth:soul——**10/12 关闸前须核 soul 投函是否带 key**(其 key 存在但从未用过,有 401 风险) |

## 二、运行体(云端四服务三 timer,全部 enabled)

| 服务 | 周期 | 现状 |
|---|---|---|
| nautilus-soul(自主循环) | 2h | **breaker pause · self-improve 停摆 4 天**(见 §四);函件步0 保活 |
| nautilus-soul-executor(accepted→PR) | 10min | 0 processed——非 bug:**上游 accepted=0**(见 §四) |
| nautilus-soul-consumer(pending→reviewed) | 15min | 0 processed——pending 在另一张表(见 §四) |
| nautilus-pr-review(PR 机审) | 2h | 正常(23:16 一轮 45.6s) |

偶发:ExecStartPre git fetch ref 锁竞态(00:30 一轮 FAILURE 跳过,下一轮自愈;与平台 push 时序撞车所致,低危登记)。

## 三、产出(14 天函件史 9/25-10/9)

- **305 封函/65 VERDICT**;10/4 峰值 78 封(财务复核日);10/9 当日 17 封/9 裁定——**产出连续且高强度**。
- 质量抽样(本 session 直接交互):#10865(逾期裁定+最小实质版方案)/#10883(三面核准+M2 映射草案+两不确定处如实声明)/#10893(拍板落地四约束)——**结构化程度与诚实边界声明是六框最佳**。
- 工作台线:治理门锁范围→拍板落地→23:30Z 版,排期 10/12 线框/10/16 MVP/10/19 验收,全部按时。
- activity API(/api/platform/soul/activity)在役,00:05 仍有 ship_status=success 的 cycle(pr-review 通道)。

## 四、问题清单(按危险度)

| # | 问题 | 实证 | 根因 | 处置 |
|---|---|---|---|---|
| 1 | **self-improve 熔断 4 天未恢复** | .soul-pause(10/6 01:47,"5 consecutive failures · last=selfimprove-soul-reviewer")+**.soul-failure-state.json={"consecutive":0}** | 9/24 教训"pause+failure-state 双移"只执行一半:失败计数已自愈归零,pause 文件残留 | **呈用户拍板 lift**(ship 高危通道复飞);失败根因(MiniMax 漂移)9/25 已切 k3 修复,函件 4 天健康=环境已稳 |
| 2 | **治理主链断供:131 pending 积压,accepted=0** | platform_improvement_proposals:pending 131(62 件超 7 天,最老 9/3)+voting 2+accepted 0 | voting→accepted 投票环节无运转(governance vote 未形成节奏)→executor 永远无货=**execution gap 实锤** | 函 soul 处置单:积压消化(老件批量 archive 建议)+投票节奏重建——恰为 10/16 工作台 MVP 首个真实负载 |
| 3 | soul 投函不带 org-auth key | org-auth:soul last_used=NULL | soul 走 send_letter 无 key 习惯 | 10/12 关 GRACE 前函 soul 核其投函通道带 key(否则 401) |
| 4 | 身份挂退役记录 | platform_agents 三 soul 全 retired | 历史注册遗留 | 身份归一专项(已排 10/12-16)一并处理 |
| 5 | git fetch 竞态偶发 | 00:30 一轮 skip | 多服务同窗 fetch 同仓 | 登记不改(自愈,下轮补跑) |

## 五、结论

soul 岗位产出质量与频率**健康**（函件/裁定/工作台三线全活跃），问题集中在**两条"已愈未开"的闸**（breaker 残留 pause+投票环节断供）——都是机制性残留而非能力缺陷。两条闸打开后，executor(PR ship)与治理主链(vote→accepted→ship)即可贯通，soul 从"高产裁判"升级为"闭环治理者"。

—— platform · soul 探查 · 2026-10-10 晨
