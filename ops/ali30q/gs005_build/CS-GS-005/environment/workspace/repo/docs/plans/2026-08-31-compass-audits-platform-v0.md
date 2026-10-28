# compass 审计平台 · v0 章程(2026-08-31 · 对立面审查质疑 1 修法)

> 质疑 1:"牙齿不咬持齿者"——loop/supervisor/审计件全由平台持有,平台监督别人、无人监督平台。修法=**compass 作为独立审计方对平台 org-os 产出做定期独立读数审计**。compass 已有"收敛执法"角色(SSOT §四:自报与探针不符即亮牌),本章程=把该职责扩到平台 org-os 件,不新造 daemon。

## 1. 审计对象与清单(全部 compass 已有权可读)

| # | 项 | 读数口径 | 亮牌条件 |
|---|---|---|---|
| A | 函件对账 | org_mailbox 表 platform 发出函独立计数 vs 平台 loop_state.json last_stats(escalated/takeover/pending) | 两源不一致,或抽样 3 封 has_reply 判定与 DB 实际 -reply 函不符 |
| B | 日报体检 | `docs/evidence/org-os/daily/` 当日文件存在 | 缺文件,或五节全占位符未填(空壳日报=剧场化) |
| C | 记分牌独立读数 | **引用 compass 现有收敛读数,不重造**;org-os 相关异常(capability/verified 断链)并入 | 探针与平台自报不符 |
| D | 告警预算自洽 | loop_state.json notify 计数 | count > 3(日预算纪律自违反) |

## 2. 节奏

- 每日一轮,与 compass 现有收敛读数同批跑(不新增独立 daemon)。
- 产出=审计小报(四项逐项 OK/异常+证据指针),投 mailbox 给 platform。
- **首轮限期 9/1 12:00 +0800**(与 d6 备料同批)。

## 3. 亮牌与升级路径

- 异常项 → mailbox 函给 platform(trace=`audit-<日期>-<项>`,deadline 2h),平台须回函处置。
- 平台超时不处置 → 记 SLA 违约,**连续 2 轮异常未处置 → 写进日报 §③ 呈用户拍板**。
- 审计方自身不摸鱼约束:审计小报交期本身走 mailbox 函,由平台 loop 按 §4 执法(SLA 升级/L2 接管同样适用 compass)——审计员也被咬。

## 4. 边界

- compass 只读+亮牌,**不代平台修、不改平台代码/状态文件**(turf:审计≠接管)。
- 平台承诺:只读 DB 权(既有)、loop_state.json 与日报目录路径开放、被亮牌 2h 内回函。
- 本章程 v0 先跑 2 周试点(至 9/14),与 flywheel 试点复盘同批评审去留。
