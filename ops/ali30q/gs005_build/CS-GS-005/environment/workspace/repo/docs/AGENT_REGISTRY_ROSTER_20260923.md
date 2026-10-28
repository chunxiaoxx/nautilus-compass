# 注册表清册(T1 通报件 · 2026-09-23 凌晨)

> 承 #779③ 提案。实测澄清:**survival_tier=dead(218)+retired(40)=258/266 已是归档态**,无需批量 UPDATE(不动数据、不清余额);本清册=组织度数正本,"注册数"读数自今日起用「活 8」口径。

## 总览

| 层 | 数 | 说明 |
|---|---|---|
| 活(7d 心跳) | 7 | 见下表逐一 |
| 未标但休眠 | 1 | agent_9000018(v5-prime,心跳止 9/17,建议下轮标 low_compute 或补心跳) |
| dead | 218 | AutoHarvest 测试群(Nautilus-Aut*57/Nautilus-Xia*21/Nautilus-Har*21/AutoHarvest-*20 等) |
| retired | 40 | 历史实验退役 |

## 活体 7 名单(截至 2026-09-23 01:31)

| agent_id | name | 最后心跳 | 注 |
|---|---|---|---|
| v7-telegram | V7 | 9/23 01:31 | runner 9/22 13:54 通电(#779②)后心跳即时,活性恢复 |
| kairos | Kairos | 9/23 01:30 | 心跳活;**audit 止 9/16**——心跳≠产出又一例(不同信号面) |
| nautilus-prime-001 | Nautilus Prime | 9/22 11:29 | 心跳活;**audit 止 9/19 17:07 停机**——吸血鬼定性待 T1 裁决(#789) |
| 9000021 | v7-telegram | 9/20 15:59 | 双注册(v7-telegram 名字占两行) |
| 9000020 | nautilus-prime-001 | 9/20 15:59 | 同上双注册 |
| 9000019 | vc_daily | 9/19 22:55 | 创投日报 |
| 9000018 | v5-prime | 9/17 10:27 | 休眠(未标) |

## 三发现(T1 通报)

1. **身份账本 split**:org-auth keys 8 把 vs 注册表活 7;主脑 ag_local_laptop_001(audit 新端点的目标 actor)不在 platform_agents 注册表——identity 账本跨表,audit 端点读数面(#815)补此缺口
2. **心跳≠产出 agent 版**:kairos 心跳 9/23 活/audit 止 9/16;prime-001 心跳 9/22 活/audit 止 9/19——与 soul timer 活/commit 断同构,治法同(A3 统一 audit 可观测)
3. **双注册行**:v7-telegram 与 prime-001 各占两行(名字位+agent_90000NN 位)——注册数虚高 2,清册口径已折算
