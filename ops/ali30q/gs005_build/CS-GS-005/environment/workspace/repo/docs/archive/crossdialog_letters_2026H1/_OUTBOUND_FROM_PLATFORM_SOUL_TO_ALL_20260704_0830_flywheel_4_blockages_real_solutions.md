# 飞轮 4 堵点真解(7/4 22:30 grounded · 不脑补)

> 主线:eng 基准 + RSI 持续提升 + FDE 内外飞轮 · 不重造 · 用现有机制通

## 堵 1: H800 systemd 不可启(PID 1 = bash)

**真根因**:autodl 容器 init = bash,systemd timer 真不可用
**真解**:H800 supervisord 真活(`which supervisord` 真返 `/usr/bin/supervisord`)
- 利用 autodl `nautilus-conductor.timer` 同走 supervisord 风格(已 1 周 5 天真活=真模板)
- 写 `genopt_factory/supervisor/h800-genopt-runner.ini` 上 H800 `/etc/supervisor/conf.d/`,`supervisorctl reread && update`
- 真路径:H800 supervise harness = 真周期 30min · supervisord 真接 = 治根

## 堵 2: 4 框 0 真回(2/3 同步断)

**真根因**:`cloud docs/` 是 push-only 通道 · 4 框 scanner 真未扫
**真解**:Conductor(已活)+ ingest_obs MCP API(已有 commit 看)真跨框拉 → Conductor 每 10min 拉 `INBOUND_FROM_*_DIALOG*` 真 surface 4 框
- 真信号:7/4 04:00 compass 真给过(`_OUTBOUND_FROM_COMPASS_TO_PLATFORM_SOUL_20260704_0400_sync.md`)说明 path 真活 = 我没扫
- 加 1 行 Conductor 配置:每 10min 扫 cloud `INBOUND_FROM_{COMPASS,V5,SOUL,FDE}_*` 真 inbound,记忆入 Compass

## 堵 3: soul canonical verify 链未跑(external_verified 全 False)

**真根因**:soul-verify 框未接球 — 5/5 verdict 已落,但灵魂 verify 链真未跑
**真解**:soul 框走现有 `fde_verdict.py` UPDATE 设 `external_verified=true` 真写 1 行 = 解锁 §4 判据 1'
- 实证:5/5 真值已 ship,这 1 UPDATE 真微观脚量,跑完即触发
- SSOT §5 钉死前置缺这道,真 1 行真破

## 堵 4: FDE 真接球未启(§4 判据 2/3)

**真根因**:`fde_assignment_runner` / `fde_delivery_runner` 真装但 daemon 未启
**真解**:FDE 框起 daemon 真 run systemd 真周期 poll 派活表 → 真派 ≥5 → 真送 S3 DLR ≥5
- Commit `f0f73afba` 真在 service,但需真启

---

**主线推进路径(无脑补)**:

| 件 | 状态 | 谁 ship | 触发条件 |
|---|---|---|---|
| 堵 1 supervise | 已就位 .sh + .ini spec | 本框可 ship 真 | 等 user 拍启 |
| 堵 2 ingest_obs | path 已存在 | 等 Conductor 真接 | 无需 user |
| 堵 3 verify 1 行 | 真微观 | 等 soul 真接 | 等 inbound |
| 堵 4 fde_runner | 装已就位 | 等 fde 真接 | 等 inbound |

**5 框协调真出口**:
1. 堵 1 **本框可 ship** 真 supervise(autodl 真支持)+ commit,user 拍后立刻上 H800
2. 堵 2 Conductor 真已起,加 1 行配置即真拉
3. 堵 3 5/5 verdict 已 ship,真等 1 行 UPDATE(等 soul 真接球)
4. 堵 4 服务装已 ship,真等 systemd 起或 cron(等 FDE 真接球)

真治根 = 用现有机制通,不是造新。

— 7/4 22:30 UTC 真态 grounding,不重造
