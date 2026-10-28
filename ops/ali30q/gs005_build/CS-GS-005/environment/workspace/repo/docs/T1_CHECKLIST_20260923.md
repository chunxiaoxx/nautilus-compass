# T1 验收读数手册(9/23 会议用 · 判据全部可现场复算)

> 配合议程正本 docs/T1_AGENDA_20260923.md。原则:验收=读数,不是听汇报。

## A3 audit 路由统一 · **✅判据达成(9/23 09:52 主脑首条入 cloud)**

| 读数 | 命令 | 基线 | 判据 |
|---|---|---|---|
| 端点活 | `curl https://www.nautilus.social/api/platform/org/audit?hours=24` | 200 | 200 ✅ |
| 写入鉴权 | POST 无 key | 401 | 401 ✅ |
| **主脑改调** | 同 GET 加 `&actor=ag_local_laptop_001` | **1(probe:t1a3,09:52)** | **total>0 ✅** |
| 僵尸清册 | docs/AGENT_REGISTRY_ROSTER_20260923.md | 266=活7+休眠1+dead218+retired40 | 已呈 ✅ |

## A1 值守统一

| 读数 | 来源 | PASS 判据 |
|---|---|---|
| 三层节拍活 | systemctl list-timers(dispatch 5min/sentinel 15min)+ schtasks frame_worker | 全 active 按点 |
| 断供处置线 | soul #824(01:17 发) | T+26h=9/24 01:17 前三选呈报 |
| 日报全量 | 09:07 frame_snapshot | 今晨含钱箱/三盲区/云心跳/免疫年检四节 |

## A2 v5 活性协议五件套 · **✅PASS(10:15 全闭环)**

- v5 侧:三件代码✅(c24b54a/ce15764/1a3985f)+三实证✅(快照本地实测 09:50 四源矩阵/bootlog 09:59+audit probe 佐证/f3f848e 勘正认账→坐标三锚纪律);audit 改调 b3d402e(本地仓核,TDD 6/6,顺带修 b2e0a64e)
- 平台侧:P2 quota gate✅(b87682f0e)/P1 交付矩阵✅(7c5b50279+8a9bf2d16)/P3 契约单页✅(dbe7ba145)
- P4/P5 charter 条款:排下次协同讨论

## 通报件(只报 5 分钟)

1. RSI 北极星已亮(批一 45 条,#800);批二 14 条常规流转
2. 注册表清册(见 A3 表);组织度数口径改「活 8」
3. v7 runner active(9/22 13:54,#779②);清册实证其心跳即时恢复
4. Loop 协议 V1 归并正本(三家合成,#827/#828);今日起全框按 [loop-diff] 同步

## 用户面板(唯一动作)

**商户验证**:pay.weixin.qq.com → 账户中心→商户信息→完成法人/打款验证 → 告知 compass → 30min 内 ¥0.01 端到端 → 卡2 DCR 上墙(收钱线最后一米,#811)
