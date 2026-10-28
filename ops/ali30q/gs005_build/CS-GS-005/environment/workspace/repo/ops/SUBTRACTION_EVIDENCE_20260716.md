# 🔪 减法证据清单(2026-07-16 生产只读采证 · 用户已拍板 · 平台 turf 已执行)

> **执行记录(7/16)**:平台 turf 25 个死 unit(§3 前两组)已物理删除——50 个文件(service+timer 成对)tar 备份至 `/root/dead_units_20260716.tar.gz`(5.4KB),`daemon-reload` 后残留 0/25,记分牌复验无倒退(income 703 / verdict 65 / 自治率 89.2%)。跨框 13 个 + 存疑 5 个已发 outbound(`_OUTBOUND_FROM_PLATFORM_TO_COMPASS_20260716_*` / `_OUTBOUND_FROM_PLATFORM_TO_V5V7_20260716_*`),等对方确认。

> 采证方式:`systemctl list-unit-files` + `is-enabled/is-active` + `journalctl -u <unit> -n 1`(最后日志时间)+ `list-timers` + `git status`。全部只读,未删任何东西。
> 拍板规则:只有「判死」列打 ✅ 且 turf 归属确认后,才物理删 unit 文件(脊柱3:不留 .disabled)。

## 0. 好消息:`.bak/.env` 垃圾已清零

7/15 锚记录的 21 个未跟踪垃圾已不在(porcelain 仅剩 `CLOUD_STATE_20260715.md` 一份状态文档)。减法只剩死服务。

## 1. 活的,勿动(常驻 active 9 + timer 驱动 22)

**常驻**:compass-bge-daemon / compass-mcp-http / compass.service / nautilus-backend / nautilus-v5 / v5-brain / v5-reborn-shadow / tat_agent(腾讯云)/ lxd-agent(系统)。

**timer 驱动(最后日志均 7/16 当天)**:compass-fleet-capsule、compass-keeper、compass-mcp-watchdog、fde-assignment、fde-bench、fde-janitor、genopt-auto-verify、genopt-mint、nautilus-conductor、nautilus-site-watchdog、nautilus-soul-executor、nautilus-sot-reconcile、soul-scorer、v5-cron-tick、ecc-fde-scanner、platform-results-emit、v7-llm-judge、v7-monitor、v7-registry-export、v7-spool-monitor、agent-evolution-dryrun、nautilus-truth-weekly(周任务,7/12 正常)。

## 2. ⚠️ 存疑:active 但日志长期停滞(剧场化嫌疑,先查再判)

| unit | 状态 | 最后日志 | 疑点 |
|---|---|---|---|
| genopt-contract-consumer | enabled+active | **7/4**(12 天无日志) | 活着 ≠ 有产出;consumer 是否还有上游? |
| nautilus-kairos | enabled+active | **6/29**(17 天) | kairos 框 turf;是否僵尸进程 |
| v7-telegram | enabled+active | **6/27**(19 天) | V7 框 turf;telegram 链早已弃用? |
| compass-mcp-tcp | **disabled**+active | 6/25 | 手动起的孤儿:重启后不会回来;要么 enable 要么停 |
| nezha-agent ×2 | enabled+**inactive** | 6/16(一个月) | 外部监控 agent,装了没用起来;删或修 |

## 3. 判死候选(disabled/static + inactive + 无 timer · 按 turf 分组)

**平台框 turf(20 个,可先删)**:nautilus-a2a-sla-enforce、audit-selftest、bounty-deliver-poll、capability-probe、chaos-weekly、claimed-bounty-timeout、daemon-progress、ext-events-consumer、handoff-scan、handoff-stale-alert、loop-health-verify(最后 6/15)、morning-ritual、nau-drift-alert、nau-reconcile、outreach-dashboard、outreach-rewarder、schema-review(7/1)、stale-monitor(6/15)、stale-tier-downgrade、todo-promoter。
共同证据:全部 disabled+inactive,多数最后日志停在 7/15 18:xx(= 当日被批量 stop 的时刻),无 timer 指向。多属 5 月"13 trigger/11 cron 缝补物"审计([[session_b0f08cac]])遗骸。

**a2a/drift 族(5 个)**:a2a-delegation-timeout、a2a-drain、a2a-pulse、behavioral-drift、drift-threshold-alert——timer 已不存在,7/15 后无活动。

**compass 框 turf(2 个,请 compass 确认)**:compass-gateway(无日志)、compass-t4-tunnel(T4 已关停,7/7 后死)。

**V5/V6/V7/kairos 框 turf(11 个,请对应框确认后删)**:nautilus-v5-api、nautilus-v5-telegram、nautilus-v6、v5-daemon、v5-heartbeat、v5-wave-kairos、v6-a2a-handler、v7-aligned-tick、v7-audit-24h、v7-singleton-audit、kairos-cron-tick——全部无日志或 disabled+inactive。

**冻结随存疑项(2 个,不删)**:swe-automint(SWE 链在 parking lot 等 A800)、fde-double-gate(distill 子系统,存疑#1)。

**系统级(1 个)**:barad_agent 已 masked(腾讯云组件),维持现状。

## 4. 拍板后执行规程

1. 平台框 turf 20 + a2a/drift 族 5 → `systemctl disable --now <u>`(已 disabled 的跳过)→ `rm /etc/systemd/system/<u>.service`(先 `tar` 打包备份到 `/root/dead_units_20260716.tar.gz`)→ `daemon-reload`。
2. compass/V5/V7 turf 13 个 → 发 outbound 让对应框确认,确认一个删一个。
3. 存疑 5 个 → 逐个查上游/产出后单独判。
4. 删完后记分牌复验(income/verdict 不倒退)+ 更新本文件。
