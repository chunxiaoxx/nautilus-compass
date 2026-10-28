# 平台资产台账 v1(2026-08-28 · 独立验证盘点)

> 方法:systemd 活性 + DB 行数/**时间分布** + journal 最近输出——不信代码自报。
> 三态:🟢在产 / 🟡睡着可唤醒 / ⚪空转待处置(或死代码)。
> 盘点动因:用户战略重定位(平台=AI 原生组织的操作系统,先吃狗粮);"大量抛弃"印象需要实测修正。
> **§⓪-E 登记列规范(8/28 补)**:每行两新列——**消费者**(谁在用它:框/agent/外部)与**消费计数**(被组合次数,初值=当前实测)。产出不计进展,**消费计数增长才算**;30 天零消费=退役候选。ship 不带台账行不算完成(DoD)。

## 一、云上活体实测(9 service + 12 timer)

### 🟢 在产(今天有真实产出/流量)

| 资产 | 证据(今日实测) | 新目标下的角色 |
|---|---|---|
| nautilus-backend | 4155 verdict / 343 agents / 账本 API | 主账本 |
| auto-verify daemon(10min) | verified 465 自动增长 | **验证服务(对外可卖)** |
| supervisor(30min) | ZERO 判级+telegram 告警,今天亲验工作 | **监督服务** |
| **platform-loop(30min · 8/31 上线)** | timer 13/43 分;首轮执法:SLA 升级函 4 封落库(id54-57)+takeover 11 封 telegram+日报骨架 `docs/evidence/org-os/daily/`;TDD 8 green | **协议 §4 SLA 执法+§5 日报运行时** · 消费者=四框(函件 SLA)+用户(日报) · 消费计数 1(首轮执法) |
| compass 全家(4 service+3 timer) | 本 session recall 全程在用 | **记忆服务(治失忆)** |
| **compass 对外 MCP(http+tcp 双通道)** | running + watchdog 30s 巡检 | **对外 MCP 已有活实物**(workbuddy 可直接接) |
| **组织驾驶舱 v0**(org.nautilus.social + www /org/) | 8/30 正席:443 证书(acme.sh 自动续,至 11/28)+四链 200+sha 三验;页面+台账在 current/org/,evidence alias 直读云仓,零新后端 | **组织 OS 公共门面(四框+用户日均看)** |
| agent_first 身份 + api_keys | 343+ agents / keys,9000010(8/22)+**9000011 variant-gen(8/30)** 新注册 | **身份/认证服务** |
| capability_feed(转移线④) | 198 行,8/28 更新,复活后自动+ | **能力账本(agent 简历)** |
| survival | 215 行在写 | 生存/信用 |
| **executor g2b1(V5 本地)** | verdict 持续入库+熔断/补采值守;d6 定案后 568 轨迹+GLM 补采转交付燃料用途(线不受影响,8/30) | 唯一注册生产 agent |
| **variant-gen worker 9000011** | 8/30 agent-first 注册(survival+api_key 齐,batch1 变体 10 条双门全过在 `docs/evidence/g2b1_variants/`);内核 `tools/g2_b1_variant_gen.py`(LLM 提案+novelty 0.3+变体双门) | **第二注册 worker(转移线⑤解挂锚)** · 消费者=9000010(变体入队列待其消费) |
| v5-api(OpenAI 兼容) | running | agent 推理网关 |

### 🟡 睡着可唤醒 → **8/31 退役评审已处置**(采证全文 `docs/reviews/2026-08-31-ledger-retirement-review.md`)

| 资产 | 8/31 复采证 | 处置 |
|---|---|---|
| A2A 派单协议 | 296 行存量停 7/18;唤醒条件已达成(9000011) | **保留**——唤醒路径=变体消费流首个跨 worker 派单 |
| raid 共识投票 | votes 停 8/1;executions 7d 319 全败仍在写,调用者=raid-trigger.timer | **退役** ✅timer 已停(解冻=多 agent 真实共识场景) |
| soul 引擎三 timer | 产出表 DB 不存在;scorer/executor 每 30min 空调度 | **退役** ✅两 timer 已停(解冻=goal-sourcing,GOAL_STACK #9) |
| marketplace | 代码在,库无表(证实) | **退役**(解冻=capability 供给信号+建表设计) |
| governance / resource_governor | 未通电,无表无消费者 | **退役**(解冻=agent 持份共治远期) |
| v7-telegram | active 3 周,journal 零输出;workbuddy 底座候选 | **保留观察**——7 天内举证 telegram 实际收发,否则退役 |
| kairos 2.0 | **unit 文件已不存在**(8/28"进程活"记录过时) | **退役完成**(事实销账) |
| v5-brain(prime-001) | journal 3 天零输出 · survival 停 7/4 · fd socket=0(三证据同向)· V5 独立复现全坐实+补充"8/22 重启后仍 9 天零输出" | **退役** ✅8/31 stop+disabled(unit 保留可逆;V5 函 75 同意)。解冻条件:Reborn 脑接回 executor 现役链+预注册可验证行为判据。7/16 reborn R0-R2 影子件随本行一并归档(从未有被记录的行为) |

### ⚪ 空转/待处置(今天实测抓到)

| 资产 | 问题(实测) | 处置建议 |
|---|---|---|
| **raid_executions** | ~~7 天 320 条全部 failed~~ ✅8/31 调用者定位=raid-trigger.timer,**已停用止血** | 已处置(见 🟡区评审) |
| **genopt-variant-gen timer** | ~~停 timer~~ ✅已完成(timer 已不在 list-timers,补销账) | 已处置 |
| soul 引擎死件 | CapabilityCapsule DB(7/15 判死);验证链/QC/教案表活 | 死件标死;活件并入服务清单 |

## 二、用户点名资产判定汇总

| 点名 | 判定 | 一句话 |
|---|---|---|
| soul 引擎 | 🟡 半活 | 不是"完全抛弃":验证链/QC/评估在产,执行引擎三 timer 空转排队复活,只有 Capsule DB 确认死 |
| A2A 双向通信 | 🟡 修好无客 | 协议 8/27 刚升级到派单模式,等第二个 worker |
| 加强版 MCP | 🟢 在产 | compass 双通道+watchdog 活着 |
| compass 对外 MCP | 🟢 在产 | http(/compass-mcp/)+tcp 双端点 |
| soul MCP | 🟡 | soul_bridge/consumer 代码在,流量未验 |
| 价值交易认证 | 🟢 在产 | verdict/income/341 keys/survival 215/能力账本 198 |

**印象修正:"大量抛弃"不准确——大部分活着,但约一半在空转或无客。问题不是造了没造,是造了没通电、没记账。**

## 三、通电行动(按 ROI 排序)

1. **立即(今天)**:停 `genopt-variant-gen.timer`(产物被 mint 全拒=纯浪费;与平台变体生成器功能重复)
2. **本周**:定位 raid 失败调用者(46 败/天的无声空转);v5-brain/kairos 活性体检
3. **狗粮第一口**:`/v1/org/bootstrap` 端点(治失忆:SSOT 增量+memory+活合约+目标栈一次返回,四框 hook 接)
4. **workbuddy 路径**:盘 v7-telegram 升级为 workbuddy 底座(现成 Telegram 通道+3 agent 聚合)+compass MCP 直供记忆
5. **唤醒清单**:a2a/raid 等第二个 worker;soul 引擎等 goal-sourcing(第一个喂给它的目标就是③的狗粮件)

## 维护
- 三态变更→改本文件+commit;每资产状态以独立验证为准(timer 活≠在产,要有产出证据)
- 下一版:补 marketplace 建表设计+governance 通电路径
