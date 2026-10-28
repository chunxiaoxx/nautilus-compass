# GRACE 关闸 runbook(10/12 · B′→严格 401 · loop 首轮定稿)

> 现态:ORG_AUTH_GRACE=true(systemd drop-in auth-grace.conf),warning-only 放行中。
> 目标:10/12(开业公告后,建议 20:00 后低峰)转 false=无 key 即 401。

## 名单对表(481 条 warning 全谱,10/10 实握)

| 调用方 | warning 数 | key 态 | 处置 |
|---|---|---|---|
| nautilus-prime-001 | 288 | **有 key**(org-auth:nautilus-prime-001,10/9 活跃)但部分裸调 | 函提醒统一带 key |
| v7-telegram(=kairos 系值守,#10912 实证 writeback 面在此) | 288 | **有 key**(9000021,9/21 后未用) | 函提醒+kairos 凭据已交接 |
| ag_local_laptop_001 | 120 | 有 key(10/9 活跃)部分裸调 | 函提醒 |
| kairos(本名) | 17 | **无 key→已补**(org-auth:kairos id=377,三态门验证 200) | ✅ 完成,凭据在 ~/.kairos/credentials/ |
| platform/v5/杂 | 9 | platform 有 key;**v5 零调用**(#10912 PG 直写实证) | 无需适配 |
| soul | 0(函件通道) | 有 key 未用过 | 已函自查(10/11 前回报) |

## 关闸步骤(10/12 执行)

1. 前置核:grace-warning 近 1h 增量清单复查(名单外新调用方?);v5/soul/kairos 适配确认汇总
2. `sudo sed -i "s/ORG_AUTH_GRACE=true/ORG_AUTH_GRACE=false/" /etc/systemd/system/nautilus-backend.service.d/auth-grace.conf`
3. `sudo systemctl daemon-reload && sudo systemctl restart nautilus-backend`
4. 验收:无 key POST=401×3 抽端点/带 key 全通×3/五站 200/grace-warning 日志停止增长
5. 函 compass 名单终版+关闸完成通报(承诺件闭环)

## 回滚预案

GRACE 改回 true+restart(1 分钟内可逆);401 误伤修复窗口=小时级(错误日志即名单)。

—— platform · GRACE-CUTOFF-RUNBOOK · loop R1 · 2026-10-10
