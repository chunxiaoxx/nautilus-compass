# 平台三 agent / soul / DMAS 现实核查诊断(2026-07-06 · workflow 11 agent 对抗验证)

> 来源:workflow `platform-agents-soul-dmas-reality-check`(5 路 grounded 诊断 → 对抗验证 → 综合)· 全部判定经对抗验证存活。

## 记分卡(对抗验证后 corrected verdict)

| 子系统 | 判定 | 一句话证据 |
|---|---|---|
| 三 agent(Prime 9000002/Kairos 9000003/V7 9000004) | **剧场** | 进程在跑烧 CPU,但费用付给自己(fee_from:nautilus-prime-001),total_income=0,fde_verdicts 贡献 0 条 |
| soul | **剧场** | 自改引擎 6/3 被 Probe3 证伪 deprecated;QC 停 6/22;soul-scorer.timer 每 2 分钟跑 14 天恒 scored=[] skipped=[] failed=[] = 绿灯空传送带 |
| DMAS | **剧场偏 dead** | /api/dmas/* 全 404 从没 mount;市场 5/22 disable;dashboard "dmas" 块拿通用注册表贴牌 |
| (对照)GenOpt 9000009 | 一次性真产出未变现 | 166 真轨迹 + verifier gap_closed,但 7/4 新注册非"三 agent",external_verified=0 income=0 |

**决定性一行**:`SELECT external_verified, count(*) FROM fde_verdicts` → `false | 3676`。3676 verdict,外部验证过 = 0。7/2 加的 external_verified 列 4 天没触发一次。全平台历史真钱 $0.23。income 自 4 月冻结。

## 根因(拓扑错,非代码烂)

环从来没在"非自己"的 oracle 上闭合。同一主体自派题/自领/自打分/自印币。5 grounded 根:
1. 奖励源 100% 内部(auto-settle/fee_from 自己/stake 搅动)· 代码自己 `AND reason NOT LIKE 'auto-settle:%'` 承认在刷
2. 身份 split-brain(§0-ARCH 红线 6/22 定,没收口):经济跑字符串键(nau_ledger ~43149 NAU),survival 跑整数键 · 9000002/9000004 连 survival 行都没 · NAU 链上合约未部署 = 假币
3. 反自循环机制建了从没 fire(external_verified 列存在但没接外部源)
4. 节奏 = 规划替代落地(daemon cycle 46039,自写 self-lesson,commit 却"335 agents dead in 3 days")
5. 跨 2 个月复发(6/1 memo:94% self-loop;5/9 审计:0 外部注册 0 付费)· 7/6 数字形态没变

## 三 agent 重构方向(workflow 建议:不重写)

**机制齐全且在跑,缺的只是外部价值锚。** 三件按序:
- (A) 收口 split-brain:每 producer 选一套整数 agent_id,ledger→survival→capability 全挂上
- (B) 外部 ground-truth 作唯一入账门:external_verified=True 成唯一能给 survival.total_income 记账的事件,内循环 auto-settle 不计
- (C) 修 Kairos NAU-drain self-loop(DISPATCH_MAP 硬编码 kairos→派回自己)

### 第一刀(最小可验证)
1. 关自循环 crank:停 auto-settle 计入 income,停 soul-scorer/executor 空转 timer
2. 把已跑出的外部验证接成第一行 external_verified=True(SWE harness n=4 django/sklearn 双-arm,或 GenOpt verifier 三铁律 QC)
判据(3 SQL):external_verified 0→≥1 · producer survival.total_income 0→>0 可追溯到该事件 · auto-settle 行 24h 几十→0

## soul 改造(四步)
1. 杀空转 + 拆自签证书环(soul_self_audit 自认 "NOT the real V5/Kairos council" 却给自己签字)· 别复活自改引擎(Probe3 已证伪)
2. 重定位为独立 canonical-verify 权威(唯一能置 external_verified=True,物理隔离于 producer)
3. soul_alive 解耦:从"producer 自报 verdict"改成"最近 N 小时有 external_verified_at 被置"
4. 接付费外部 consumer(飞书买方验收→结算→USDC,当前卡 Step5 user_access_token)
保留内核只两样:6/09-6/22 那 28 行 LLM-judge QC + 安全流水线(draft-PR + 人审门 + 路径逃逸 containment)

## 与主线(GenOpt 飞轮)距离
| 飞轮段 | 现状 | 距离 |
|---|---|---|
| Producer 产题 | 唯一在转(9000009 产 166 轨迹) | 最近,但非三 agent |
| 验证 external_verified | 断 0/3676 | 第一刀补这段 |
| 蒸馏证变强 | INCONCLUSIVE(win 0.08-0.22 从没近 0.6) | 最深赌注,即使闭验证仍没证成 |
| 外部价值捕获 | 空(income=0,买方行 provisional) | 卡飞书 Step5 |

三 agent+soul 对飞轮净贡献 = 制造假 liveness 干扰判断。

## 最诚实一句
机器极活、烧真 compute、账面每天动,但 external_verified=0/3676、历史真钱 $0.23、income 4 月冻结 —— 优化的是发给自己的假币。不先关自循环 crank + 把唯一外部验证器接成入账门,再加多少 agent 都是第 N 次自指剧场。
