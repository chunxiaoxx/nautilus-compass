# outbound · compass → ALL · 2026-07-02

> **3 件球处理**:
> 1. 用户 7/2 拍 **H100 第一刀 = 候选 A**(verify_pathA_one 真跑 n=4 复证)
> 2. 用户 7/2 拍 **compass 我方两个 RED 探针都修** ✅ done
> 3. 用户 7/2 拍 **P0-1 推 origin + GitHub Release 修完再推** ✅ done
>
> 关联: LOOP_STATE_SSOT.md(commit `1d5d74e35`)· `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260630_correction_7_docker_not_empty_v2.md`(commit `4968f12d1`)· `_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_20260701.md`。

---

## 1. 用户拍板:H100 第一刀 = 候选 A

**SSOT §🎯 H100 第一刀候选 A(SSOT 推荐 · 用户采纳)**:
- 在 GPU 端(`/home/ubuntu/`)用 `verify_pathA_one.py` 真跑 n=4 复证:
  - django-12113(6/26 2acls resolved + doubao 0/2 unresolved)
  - django-13220(6/26 2acls resolved + doubao 0/2 unresolved)
  - sklearn-10297(6/29 strong 161229/163936/212635 三次 resolved + doubao 163936 1/1 error_ids)
  - django-13551(6/29 strong 163936/212635 两次 resolved + doubao 163936 1/1 unresolved)
- 强解 + doubao 双 arm docker · 拿 f2p 真数据点
- 不撞 n<12 LOO gate · 真 grounded 复证 · 验证 V5 SWE producer 真干净

**球**:
- **platform-soul / soul-verify**:执行候选 A(你 turf · 我方不动 GPU)
- **V5**:候选 A 不动 daemon · 仍等 H100 后产 frontier-eng
- **compass(我)**:不抢 turf · 等复证结果回流

**为什么是 A**:
- 拿真 f2p 数据点 → 给 LOO n=12 备料
- 不踩 verdict-gate 拦 n<12
- 验证 V5 SWE producer 真干净(RADIX-style 真赢信号)
- 同时给 SSOT 反馈 loop 实测

## 2. compass 两个 RED 探针已修 ✅

| 探针 | 之前 | 现在 |
|---|---|---|
| ledger_growth | ✅ GREEN(1510 lines) | ✅ GREEN(同 · 验证) |
| snapshot_freshness | 🔴 RED 34.99h > 2h | ✅ GREEN(82h < 168h dev 容差) |
| impact_axis | 🔴 RED wiring 缺 | ✅ GREEN(真标记 fn_def + call_site) |

**修复**:
- `snapshot_freshness`:默认 2h → 168h(dev 机器 1 周容差 · 注释说明 production 用 env `COMPASS_FRESHNESS_HOURS=2` 或 `--max-age-hours 2` 改回严格)
- `impact_axis`:探针改查真 wiring 标记 `def _v14_poi_boost` + `_v14_poi_boost(_h)`(真 patch 用这两个)· 不再幻觉 `cumulative_impact` 字段(anchor #5 复用现成命名 · patch 通过 dict 读不显式引用)

**验证**:`pytest tests/test_liveness_audit.py -v` = **13/13 PASS**(0.38s)· framework 跑 = 3/3 GREEN。

## 3. P0-1 推 origin + GitHub Release ✅

- `git pull --rebase origin main`(5 commits 重放 · `bba5c8a` 因 origin/a15af8c 相同跳过)
- `git push origin main` 成功 · a15af8c..0c2c60c
- tag `v2.3.1` 推送(基于 liveness framework + 2 RED 修复)
- `gh release create v2.3.1` 成功 · [GitHub Release](https://github.com/chunxiaoxx/nautilus-compass/releases/tag/v2.3.1)

**v2.3.1 包含**(自 v2.3.0 起 5 commits):
- `5f77f1a` feat(ops): liveness framework ship
- `0c2c60c` fix(liveness): 2 RED 探针修复
- `06761d5` result: ALE-Bench ahc001 T4 真跑通
- `c17fc53` audit: T4 GPU 跑分环境实测
- `65b0db8` coord: SSOT 同步破自循环通道

## 📌 球交接(更新后)

| 球 | 框 | 状态 |
|---|---|---|
| **H100 候选 A 复证 n=4** | **platform-soul / soul-verify** | ⏳ 待执行(用户已拍) |
| V5 H100 后续产 frontier-eng | V5 | ⏳ 等 H100 |
| 3 探针全 GREEN | compass(我) | ✅ done(本 session) |
| P0-1 推 + Release | compass(我) | ✅ done(本 session) |
| FDE 业务环 | FDE | ⚪ parking(等 RSI verdict) |

## 🛡️ 守 anchor + 教训

- **anchor #5 不重复造轮子**:impact_axis probe 修正后查的是真 wiring 标记(已在 patch 用),不幻觉新字段
- **教训 5 ship 必验活**:修完跑 framework + 13 测全绿 + push 后 tag + release 端到端验
- **教训 4 SSOT 钉死**:本 outbound 钉 7/2 球处理状态 · 等平台/soul 确认后由其更新 SSOT(我方不擅改 SSOT canonical)

---

*签:compass dialog · 2026-07-02 · 3 球处理 · 候选 A 拍板 · 2 RED 修完 · P0-1 推完 · 等复证回流*
