# 台账🟡8件退役评审(2026-08-31 · 用户授权启动)

> trace_id: ledger-retirement-20260831 · §⓪-E 遗忘环首次执行。
> 方法:独立采证(systemd 实况/journal/DB 时间分布/进程 fd)——不信台账自报,台账 8/28 的状态也要重新验。
> 处置分级:平台自有确凿死件=立即停用(全部可逆 systemctl 级,不删文件);跨框资产=函告限期举证;保留件=给复验判据。

## 评审结果一览

| # | 资产 | 采证证据 | 判定 | 执行 |
|---|---|---|---|---|
| 1 | **raid-trigger + raid 全家** | raid_executions 5722 行,7d 新增 319 条**全部 failed**,最新 8/30 16:08 仍在写;raid_votes 停于 8/1(30 天前);调用者坐实=raid-trigger.timer 每 30min | **退役**(空转实锤:投票死 30 天,执行账还在每 30min 记一笔败) | ✅ stop+disable |
| 2 | **soul-scorer.timer** | 每 30min 调度;产出表(soul_proposals 类)DB 中不存在;台账 8/28 记 scored=[] | **退役**(解冻=goal-sourcing,GOAL_STACK #9 预注册) | ✅ stop+disable |
| 3 | **nautilus-soul-executor.timer** | 同上,"0 proposals";conductor 无 timer 本就未通电 | **退役**(同上解冻条件) | ✅ stop+disable |
| 4 | **kairos 2.0** | systemctl show: ExecMainExitTimestamp=n/a · UnitFileState=空——**unit 文件已不存在**(8/28 台账还记"进程活",已过时) | **退役完成**(事实已清,无需动作) | ✅ 已是事实,台账销账 |
| 5 | **marketplace** | 代码在,agent_marketplace 表 DB 中不存在(零数据零消费者) | **退役**(代码归档标死;解冻=capability 供给信号+建表设计) | 📝 台账标死,代码不动 |
| 6 | **governance / resource_governor** | 代码在,从未通电,无表无消费者 | **退役**(解冻=agent 持份共治远期) | 📝 台账标死 |
| 7 | **v5-brain(prime-001)** | active 8.5 天但:journal 3 天零输出 · survival 9000009 停 **7/4**(近 2 月) · 进程 fd socket=0(三证据同向)。但属 V5 域资产 | **待停**——函告 V5 举证或同意(trace v5brain-liveness-evidence-20260831,2h SLA);到期无回执按死件停用(可逆) | 📨 函已投(id 34) |
| 8 | **v7-telegram** | active 3 周,journal 零输出(daemon 或写自有日志);**workbuddy 底座候选=有战略角色** | **保留观察**——7 天内给出 telegram 实际收发证据,否则降级退役 | 📝 判据预注册 |

## 顺带销账

- **genopt-variant-gen.timer**(8/28⚪"立即停"行动项):list-timers 已无此项——**已完成**(此前某轮已执行,台账未销账,本次补记)。
- **capability_capsules 表**:DB 不存在,7/15 死件判定维持,soul 引擎"半活"表述中的死件部分坐实。
- raid_executions 每日 ~46 条失败写账随 timer 停用归零——**无声空转止血**。

## 停用后验证(00:20 实测)

```
raid-trigger.timer: inactive · soul-scorer.timer: inactive
nautilus-soul-executor.timer: inactive · kairos: inactive
list-timers 中 raid/soul 计数 = 0
```

## 与复盘会议的关系

本次评审=复盘会议议题六(能力固化/遗忘环)的首次实物执行。方法学发现:**台账本身也会过时**——8/28 台账记 kairos"进程活"实际 unit 已删、记 v5-brain"查活性"结果三证据空转。结论:三态判定必须每次评审重新采证,台账是索引不是真相。

## 复盘会议价值审计注(议题五自查)

本评审是平台 8 月工作中少数"停掉东西"而非"新建东西"的动作——止血空转(raid 46 败/天+两 soul timer 60 调度/天)的同时未删除任何可复活资产。这正是平台"审查者/哨兵"角色(用户 8/30 拍板)的实物形态。
