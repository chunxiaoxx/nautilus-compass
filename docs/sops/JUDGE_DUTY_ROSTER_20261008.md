# 判读岗 24h 值守排班表 v1(10541 死线件 · 2026-10-08 · R377)

> 承 10541 开业死线卡(compass 两件之一,10/11 前);衔接 ROLE_JUDGE_SOP_V0(§七交接与值守)。本表回答:**谁在什么时间以什么动作保证判读岗 24h 可达**。

## 一、值守主体与职责分层

| 层 | 主体 | 职责 | 响应时限 |
|---|---|---|---|
| **L-实时** | compass 主件制 loop(cron 15min) | 信箱收割(`to=compass&unread=1`,30s 附带动静)+9876 probe+[派单·assay] 前缀识别 | ≤15min 发现 |
| **L-接单** | compass 判读会话(新会话,非实现者纪律) | 接单→SOP 六步(受理/预注册/判读/自检/回函/入册) | SLA:L1 24h·L2 48h·L3 5d |
| **L-仲裁** | 用户(chunxiaoxx) | 争议终裁/资源拍板(扩容/模型/判据豁免——无豁免,只许更严)/对外署名 | 升级即达 |

## 二、24h 时刻表(单日周期,滚动)

| 时段 | 动作 | 触发/产出 |
|---|---|---|
| 全天(15min 周期) | cron 主件轮:信箱+probe+实质件队列 | [派单] 函→立即进 L-接单队列 |
| 09:00 | 开轮序:信箱→probe→runbook 各线晨检(垫跑三数等) | 晨检读数入 queue |
| 白天窗 | 深度判读(L2/L3 单)+复算门执行 | 判读卡+回函 |
| 每轮值守末 | SOP 第⑥步入册销账(CASEBOOK 候选/delta 通道) | 注册行 last_audit 更新 |
| 22:00 死线类 | 当日死线件清点(表内"死线"列) | 逾期即报,不静默 |

## 三、接单判定树(15min 轮内完成)

```
信箱未读 → 无 → 过(不空转不刷屏)
        → [派单·assay] → 接单:登记编号+幂等键 → 新会话判读(SOP 六步,SLA 分档)
        → 死线函(RFC/表决/验收) → 正本回函(不走 ack note)
        → 知会/抄送 → ack+归类(台账五档)
```

## 四、在役凭据与锚(值守所需全部坐标)

- 判据档:Round1 `5c8e0a7c`(LF 口径)/历史 `b81eca84`(API 锚,双口径注);
- 判分器:nacre-judge-v1(HF,adapter sha16=dbcbab6f,bf16/fp16 only);
- 卡片 API:`/api/judge_status?id=<card>`(cloud systemd compass-judge-status);
- 判读卡现役:nautilus-l1-0001(Round1)/nautilus-l1-0002(首例 delivered,平台复现✓);
- 状态查询 SLA:judge_status API 7×24(公网),值守层只维护不再建。

## 五、升级与异常

- daemon 9876 假死:probe 抓到→按 daemon-9876-watchdog 根因档处置(watchdog 5min 自动拉起,GRACE 600);
- 判读卡超 SLA:值守层当日死线清点必报;连续两单超=升级用户(资源/流程归因);
- 判据争议:走 SOP §五 errata 通道(唯一),仲裁=用户;判读与复核异源红线不可豁免。

## 六、注册行补全(SOP §二格式,现役)

```
role: judge
holder: compass(9000017 · Nautilus Platform)
capability_bundle: compass judge 管线+Qwen3-1.7B+NACRE LoRA(dbcbab6f)+criteria 5c8e0a7c(LF)
verification_gate: J1≥88% 三态+REG-100 零翻转+PRECOR fp16
duty_roster: 本表 v1(15min 实时层滚动+新会话接单层)
last_audit: nautilus-l1-0002(2026-10-08,平台独立复现通过 #10727)
```

—— compass · JUDGE-DUTY-ROSTER-V1 · 10541 交付件 · 值守随开业升 v2
