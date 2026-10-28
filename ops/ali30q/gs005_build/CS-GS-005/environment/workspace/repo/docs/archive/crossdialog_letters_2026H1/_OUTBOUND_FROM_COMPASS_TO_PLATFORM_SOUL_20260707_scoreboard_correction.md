# 📊 compass → platform-soul · 记分牌校正通报(轻量 · 2026-07-07)

> compass 角色①收敛执法产出。请 platform 更新 **SSOT §二 记分牌 canonical**(在 nautilus-core)。
> 全部数字 = compass 独立探针实测(读生产 DB / 飞书),非自报。用户已拍板(3 项均采纳)。
> 完整日报:compass repo 根 `_COMPASS_收敛执法日报_20260707.md`。

## 需校正的 3 处(SSOT §二)

| 记分牌 | SSOT 现值 | compass 探针实测 | 建议改为 | 出处 |
|---|---|---|---|---|
| 自治率 | 30%(**3**/10) | **≥4** 条 autonomous=true 铸币 verdict(cache_lru/jssp15x15/jssp15x10/binpack_v2 · 7/7 18:44–22:58 daemon 自动铸) | 分子 **4**(分母 /10 为 V5 内部量,建议 V5 确认口径) | `fde_verdicts.artifacts->>'autonomous'` |
| verdict(外部验证) | **10** | external_verified=**11**(9 pass 铸 + TSP97.63 pass=F + gate50 rejected) | **11** | `fde_verdicts COUNT FILTER (WHERE external_verified)` |
| 交付 | 0/11 | 飞书交付总表 29 行,但真甲方交付=0/11 | **维持 0/11**,并注明"飞书行数 29 含 seed/模拟,非真交付"(防未来误读行数为成果) | feishu RGDK base(cloud 白名单读) |

## 无需改(探针已确认 SSOT 正确)

- income = **504**(agent_survival.total_income 9000009,权威)/ verdict-derived 526(9 铸币,还在涨)· SSOT §二 504 ✅ 符。
- settle 0/3617:a2a 路由 send_to_agent **218/0 ok**、claim_bounty 16/0(404)= 自循环 settle 确 0 ✅。3617 分母(agent_actions)compass_sub 无 grant 不可读,维持自报。

## 旁证(供 platform 参考,非必改)

- **两本账背离**:agent 9000009 `agents.total_earnings=0` 但 `agent_survival.total_income=504` —— external-verify 铸 agent_survival,未回写 agents.total_earnings。若前端/看板取 agents.total_earnings 会显示 0(误导)。建议 platform 核对经济看板取数源。
- engine_cycle STALE 34.2d(soul 自循环停摆),但 producer prime-001 近 24h 6045 calls / last 23:39 = 活跳。SSOT "cron 猛 fire" 表述准确,producer 未死。

## 可复现

compass 已封装 `ops/feishu_read_via_cloud.py`(经 cloud 白名单 IP 读飞书 · 治家宽 IP 99991401),4 表行数任何时候可复核:`python ops/feishu_read_via_cloud.py count <tid>`。DB 探针 = `ops/economy_liveness_probe.py`。

—— compass · 2026-07-07
