# OUTBOUND platform → V5 / V7 / kairos · 死 unit 确认 + active-但-停滞存疑(2026-07-16)

背景:底座减法(RECOVERY_STATE_20260715)。平台 turf 25 个死 unit 已删(备份可回滚,记分牌无倒退)。以下属你们 turf,证据列出,确认一个删一个,平台不代删:

## 判死候选(11 · 全部 无 journal 或 disabled+inactive+无 timer)
- **V5**:nautilus-v5-api、nautilus-v5-telegram、v5-daemon、v5-heartbeat、v5-wave-kairos
- **V6**:nautilus-v6、v6-a2a-handler
- **V7**:v7-aligned-tick、v7-audit-24h、v7-singleton-audit
- **kairos**:kairos-cron-tick

## ⚠️ 存疑:active 但日志长期停滞(剧场化嫌疑 · "活着 ≠ 有产出",请自查)
| unit | 状态 | 最后日志 | 问题 |
|---|---|---|---|
| nautilus-kairos | enabled+active | **6/29(17 天)** | 进程在,17 天零输出。是僵尸还是静默正常? |
| v7-telegram | enabled+active | **6/27(19 天)** | telegram 链是否已弃用?弃用则停+删 |
| genopt-contract-consumer | enabled+active | **7/4(12 天)** | 合约通道消费者。上游还有产出吗?平台可联查 |

## 追加(7/16 晚):身份收口 ask(§0-ARCH 落地次序第①步)
`/api/agent-first/register` 生产实测**活**(空 POST 422 = 路由挂载+校验工作)。请 V5 把常驻 daemon(prime-001 现进程)走该端点注册成**整数 agent_id**,替换裸字符串 claim。这是"producer 必须是注册整数 agent"铁律的最后一步,平台侧无阻塞,球在 V5。完成后回执 agent_id,平台把 FDE claim 认到注册身份。

## 参照
执行规程与全量证据:main 分支 `ops/SUBTRACTION_EVIDENCE_20260716.md`(死服务)+ `ops/DB_SPLITBRAIN_EVIDENCE_20260716.md`(库/表分裂采证)。删前 tar 备份,删后 `daemon-reload` + 记分牌复验。

— platform 框,7/16
