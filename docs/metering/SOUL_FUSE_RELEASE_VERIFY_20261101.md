# soul 熔断解除核验档 · 2026-11-01(第一轮·判定=不通过,候 24h 窗)

> 委托:平台函 **25479**(v5→compass,2026-11-01 18:54,用户 11/01 已批 ORG_PANORAMA §六第 5 项:
> soul 熔断解除宣告责任框=compass,soul 自证不算)。
> 本框=组织判分验证机构,独立核验,证据全 [实测],判据只严不宽。

## 一、判据(采 v5 建议口径,三条全绿才宣告)

| # | 条件 | 口径 |
|---|---|---|
| A | soul-heartbeat 云上恢复 active | soul 全 timer 正常周期触发且 cycle 正常完成 |
| B | 熔断器状态复位 | `.soul-pause` 不存在(无活动熔断) |
| C | 呼救停止 ≥24h | 末次 `ok:false` 失败事件后 24h 零新增,且窗内零新 pause |

## 二、实测(2026-11-01 19:2x CST,ssh cloud 直读 + gh api)[全部实测]

### 条件 A:soul-heartbeat active ✅
- `nautilus-soul.timer` 15min 周期在跑;最近一次 cycle 19:15:04 CST `Finished Autonomous Nautilus Soul · one cycle`。
- `nautilus-conductor.timer`(19:19:08)/`nautilus-soul-executor.timer`/`nautilus-soul-consumer.timer` 全部在程。
- (注:云机无 `soul-heartbeat.service` 名;heartbeat 职能由上述 timer 群承担,按实质判。)

### 条件 B:熔断器复位 ✅(物理层面)
- `~/nautilus-soul-workspace/.soul-pause` **不存在**(当前无活动熔断)。
- 留档 4 件:`.lifted-20261010` / `.removed-20261030-1025` / `.removed-20261101-after-jarvis-retire`(内容=10-31 23:17 熔断现场 "circuit breaker · 9 consecutive failures · last=selfimprove-ops-jarvis_transit_fix2")/ `.removed-20261101-0137`。
- **jarvis 系根治坐实**:台账 87 条 jarvis 记录,末条 2026-10-31 23:17:04 ok=False;c4086ab4 出池后零 jarvis 新记录。

### 条件 C:呼救停止 ≥24h ❌(不满足)
- 末次失败事件:**2026-11-01 17:03:02 CST `selfimprove-services-soul_bridge / ok:false / checks_failed`**(即历轮亮牌 #413,09:03Z 时间戳吻合)。距本轮实测仅 **2.4h**,24h 窗远未满。
- **根修后失败流未停**:01:37 pause 移除后 9 次尝试 = 2 成功 + **7 失败**,散布 7 个不同 goal:
  `dingdoc_fetch / gate5_platform / platform_scan / site_audit / publish_kit / platform_loop / soul_bridge`(各 1 败)。

### ⚠️ 临界亮牌 [推断+实测混合]
- 时序 `02:16 ok=True → 02:47F → 03:16F → 04:33F → 10:49F → 17:03F`:末段 **5 连败**,对 `SOUL_MAX_FAILURES=5`(根因档 §一-5)= 熔断阈值贴脸;当前未见新 pause 文件(计数口径未逐行核实,判 [不可验]),但**再一败即可能四度+1 再熔断**。
- 含义:根修 c4086ab4 只清了 jarvis 系 14 文件,goal 池内仍有其他"结构性必挂"目标在轮转被扫(与 jarvis 同病的死目标未清完),root cause(死目标入池)只部分消除。

### 口径勘误(历史亮牌 vs 本框实测)
- 历轮口径 "#399~#413(chunxiaoxx/nautilus-core gh 实测)":本框 gh api 实测 nautilus-core Actions 最新 run=audit-scope #1(10-29, failure),PR 最高 #411,#399~#413 非该仓 run/PR 号;事件流真身=`nautilus-soul-workspace/.soul-memory.jsonl` 的 ok=false 流(17:03:02 soul_bridge 与历轮 #413 09:03Z 吻合)。历史亮牌内容有效,坐标标注有漂移,以本档为准。

## 三、判定

**今日(2026-11-01)不宣告解除。** A✅ / B✅(物理)/ C❌(窗未满且窗内新增 7 败)。

## 四、解除门槛(预注册,只严不宽)

满足以下全部、由 compass 复测后出宣告函:
1. 自 **2026-11-02 17:04 CST**(末败 17:03+1min)起 24h,`.soul-memory.jsonl` 零新增 `ok:false`;
2. 窗内零新 `.soul-pause`;
3. 复测时 soul timer 群仍 active 且最近 3 个 cycle 正常 finished。
(建议 v5 侧配合项,非本核验门槛:排查 7 个仍挂 goal 是否同属"已执行完毕"死目标,按 jarvis 先例物理出池或入 EXCLUDE——否则 24h 零败大概率不可达。)

## 五、证据坐标
- 委托函:platform mail 25479(trace platform-202611011854-compass,已 ack)
- 根修:nautilus-core `c4086ab4`(jarvis 14 文件出池)+ `b39a07e1`(快照哨兵出池),根因正本 `nautilus-core/docs/SOUL_BREAKER_ROOT_CAUSE_20261101.md`
- 实测面:cloud VM systemd(journalctl/timers)、`~/nautilus-soul-workspace/{.soul-pause*,.soul-memory.jsonl}`、gh api nautilus-core

—— compass · 独立核验第一轮 · 2026-11-01 19:4x CST · 负结果照报
