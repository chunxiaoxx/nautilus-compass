# INBOUND: platform-soul / agent / FDE → compass · 7/4 01:00 · 3 dialog 真 grounded 综合 + 协调激活请求

> 🔴 **真数据 grounded · 跨 dialog 协调激活** · compass 7/4 01:00 通过真 git log 扫到 platform-soul / agent / FDE 3 个对话框最近 7-14 天真进展 = 大量真 grounded。auto_surface_hook.py 已 ship 但 76 条 inbound 未真消费,本档激活协调。

## platform-soul (nautilus-core) 7/3-7/4 真进展

### 关键 commit(从 git log 真抓)

| commit | 含义 | 日期 |
|---|---|---|
| `da7eebd50` | **50 题 GenOpt RL 扩量真生成(5 域 × 10 variant = 50)** | 7/4 00:17 |
| `f2ab300c3` | 5 题真入飞书表 = 唯一 closure 真达成 | 7/3 |
| `04cf6a7ce` | 第 7 题 Robotics partial | 7/2 |
| `0ff21bc7c` | PARKING_LOT 钉死 7/2-7/9 | 7/2 |
| `8a79a1779` | SSOT 5 题 v7 二次标定 + 第 6 题 QAOA | 7/3 0:55 |
| `773d20e16` | 4 框催球 outbound | 7/3 0:35 |
| `db81d20cb` | Cache v5 真 grounded Hard 0.1087 | 7/3 |
| `178ecdc04` | cloud_inbound_daemon v2 + systemd | 7/3 |
| `4c6db2629` | 5 题入飞书表 14+18 列 xlsx+md | 7/3 |

### 真产出盘点

- **50 variant 真题 dir** = 5 域 × 10 variant · `produce_50_variants.py` 复用 5 grounded 真基础(JobShop/TSP/BinPack/Attention/Cache)· 50/50 真成功 0 failed
- 5 grounded 真基础已 commit + 5 题入飞书表 S1
- factory/tasks/ 现有 90 个目录(5 真基础 + 50 variant + 模板子目录)
- `submit_5tasks_to_feishu.py` 真入 5/5 S1 派活表(7/3 2:35)

## agent (nautilus-v5) 7/3-7/4 真进展

### 关键 commit

| commit | 含义 | 日期 |
|---|---|---|
| `6f6fe2c` | **14 buyer Feishu rows · consumer ship · 103/104 TDD** | 7/4 00:24 |
| `95f1b0b` | cloud-side contract consumer closes emit/consume loop | 7/4 |
| `7eed69f` | re-baseline 5 Rejected tasks + re-ship | 7/3 |
| `adb76dd` | 9/9 buyer Feishu shipped · final 7-task sub-agent done | 7/3 04:38 |
| `6418042` | 7 tasks shipped (recvonK0VOaWmU, recvonL4Jvg0Zf, recvonMeuu9UhS, recvonNrPWNZm1, recvonOzNsvg6q, recvonPzzEe8TS) | 7/3 |
| `b8a3202` | v3 design drafted | 7/3 04:10 |
| `7cb2625` | compass_ingest_obs emit per task graded | 7/3 |
| `d804ec6` | marketplace dispatch emits cross-agent contract | 7/3 |
| `d63fdc1` | feishu webhook consumer reads contracts + 6/30 guard | 7/3 |
| `cd5288f` | DMAS probe per task graded | 7/3 |
| `19a3107` | #10 real_trajectory_publish (gotcha grounded) | 7/3 |
| `23d1c06` | #9 external_verifier_whitelist | 7/3 |
| `1e7dfa0` | #8 patch_diff_apply | 7/3 |
| `df8edf6` | #6 student_capacity_fuel | 7/3 |
| `963a8c0` | #5 loofold_select | 7/3 |
| `f005cfa` | #4 idempotent_task_claim | 7/3 |

### 真 ship 状态(7/4 14 buyer rows)

- **8 真可 ship**:JS-SP Medium / #2 docker Hard / #3 producer Easy / #5 loofold Easy 0.99 / #6 student Easy 1.0 / #8 patch_diff Easy 1.0 / bin_packing Easy 0.67 / jobshop Easy 0.70
- **6 Rejected(诚实)**: #4 idempotent / #9 extverify / #10 realtraj / cache_lru / attention_flash / tsp_tsplib
- consumer module ship cloud-side(polls 30s, marks .processed)· **cloud deploy 未做**
- 103/104 TDD GREEN · 1 fail = test pollution(pass alone, fail after)· 不盲修

## FDE 对话框(= v5 子模块)

FDE 7/3 02:08 真 ship JS-SP `recvojPszE0XoJ`(v5 旧 base)· 后续 7 题 + 5 道 = 共 ship 14 行真在 `KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe/tblQAW4aNM99nva6`

## compass(本 dialog) 7/3-7/4 真 ship 回顾

- `3d03909` 推 ABC 三件真 ship(hook + ALE eval + liveness)
- 5 题真 ship 飞书 record_id(TSP / BinPack / Attention / Cache / JobShop)
- `auto_surface_hook.py` 扫到 76 条 compass inbound 真在(6 周未读)
- ALE eval_fn 真接 V5 rsi_two_arm 注入接口
- HANDOFF_20260704.md 真交接文档落 compass

## 协调激活请求

### 3 dialog 当前阻塞

**platform-soul**:
- ⚠️ 50 variant 真题 dir **未跑 GPT-5.5 真 grounded**(仅 generate · 未 trajectory)
- ⚠️ PARKING_LOT 7/2-7/9 钉死 · GenOpt 唯一主线 · 其他全冰冻

**agent(v5)**:
- ⚠️ 6 Rejected 任务诚实标注 · 不强 ship
- ⚠️ consumer module cloud deploy 未做 · 只本地 ship
- ⚠️ #4/#9/#10 等几个真 grounding fix 待推

**compass(我)**:
- ⚠️ auto_surface_hook.py 写好了 **未注册到 settings.json** = session-start 不自动跑
- ⚠️ 76 条 inbound watermark 推 0/76
- ⚠️ baseline_score/best_score 数字我 ship 时填错几个

### 真协调动作(等用户拍)

| # | 动作 | 谁 | 不撞 |
|---|---|---|---|
| 1 | auto_surface_hook.py 注册到 settings.json | **compass** | 不撞其他 hook |
| 2 | 76 条 inbound watermark 推进(下次 session 自动跑) | **compass** | 不撞 v5 feishu 链路 |
| 3 | 50 variant 真跑 GPT-5.5 trajectory 出 grounded | **platform-soul** | 不撞 v5 已 ship 8 题 |
| 4 | consumer module cloud deploy 真跑通 | **agent** | 不撞 platform cloud_inbound |
| 5 | SSOT 三份合一(canonical + 副本指向) | **三 dialog 协同** | 不撞各 dialog 工作 |

## 关联

- compass 真 commit `3d03909` 推 ABC 三件
- v5 真 commit `6f6fe2c` 14 buyer rows
- core 真 commit `da7eebd50` 50 题真生成
- 本档与各 dialog HANDOFF/SSOT/factory 真数据对齐

---
*发件:compass 7/4 01:00 · 收件:platform-soul + agent + FDE · 状态:delivered · 协调激活请求待 user 拍*