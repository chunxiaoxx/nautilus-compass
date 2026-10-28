# /goal 启动 prompt · compass fresh session · 2026-06-29 22:30

> **用途**: 新 session 第一句粘 `/goal` 触发·系统自动加载 SSOT + Charter + 本交接包·续推 P0-1→P0-4 + P1 → P2 → P3

---

## /goal 启动文本(粘贴即用)

```
/goal compass · 2026-06-29 22:30 状态续推

@LOOP_STATE_SSOT.md  # 当前闭环状态单一真相源(本 session-start 必读)
@FDE_BUSINESS_CHARTER.md  # FDE 三类业务基线(跨框必读)
@_HANDOFF_compass_fresh_session_20260629.md  # 本交接包(存档+审计+优先序)

session-start 5 必读:
1. SSOT 当前活状态四行:证或杀蒸馏(维①)·一条线·其余 parking
2. 守教训 5 件护栏(n≥12 才跑 LOO · 易 django PROVEN 须非易复证 · confound 先核 · SSOT 钉死+广播 · ship 必验活)
3. 3 A-class 已 ping soul:scikit-learn-10297 / sympy-20049 / django-13551
4. cloud divergent branches(本机 6/29 vs cloud 6/6+11k uncommitted)· 解法=手工 merge/rebase
5. distill_loo.py 不在 cloud· 部署=dry-run ship 必验活

本 session 主线(P0 蒸馏一条线 · 不分叉):
① 解 cloud divergent(本机领先 26 commits → 云盒 main)→ 部署 distill-venv → dry-run(踩教训5)
② soul canonical 复核 3 A-class → 借 GPU 跑 distill_loo --kind swe(决策 A · 预期 INCONCLUSIVE 守 n≥12)
③ H100 到位后真路径:V5 产 frontier-eng 等 5 类→soul verify→distill→verdict

P0-1 / P0-2 / P0-3 / P0-4 待 ship 清单(详见交接包):
- P0-1: 推代码 + 发 GitHub Release(本 session 未做)
- P0-2: 云服务更新 v2.3.0(healthz 当前 v1.0.1)
- P0-3: MCP 协议端点暴露(/mcp + /.well-known/mcp.json 当前 404)
- P0-4: GEP P0 防退化(W1 verdict 元数据 + serving quality + revoke API)

分叉铁律:任一件 0 贡献=不做。SSOT 改四行前必先改 SSOT。
球在 soul(LOO verdict) / platform-soul(cloud divergent 解法 + FDE 切飞书表)。
```

---

## 📂 文件位置速查

| 文件 | 路径 | 用途 |
|---|---|---|
| SSOT | `nautilus-core/LOOP_STATE_SSOT.md` | 当前闭环状态(权威) |
| FDE Charter | `nautilus-core/FDE_BUSINESS_CHARTER.md` | 业务基线 |
| 本交接包 | `nautilus-core/_HANDOFF_compass_fresh_session_20260629.md` | 本文件 |
| v2.3.0 plan | `nautilus-compass-v230/docs/plans/2026-06-22-compass-v2.3.0-release.md` | 发版计划 |
| Memory 进化设计 | `nautilus-compass-v230/docs/plans/2026-06-21-memory-capsule-evolution-design.md` | GEP 设计 |
| 北极星 | memory `canonical_flywheel_convergence_northstar_20260622.md` | forcing function |
| Autodata 分析 | memory `reference_autodata_meta_agentic_data_scientist_20260629.md` | 借鉴参考 |

---

## 🎯 P0-1 → P0-4 优先 ship 清单

| 序 | 项 | 价值 | 难度 | 球在 |
|---|---|---|---|---|
| P0-1 | 推 feat/v2.3.0-release → origin + merge main + GitHub Release | 高 | 低 | compass(我) |
| P0-2 | 云服务更新 v2.3.0(healthz → 2.3.0) | 高 | 中 | platform-soul |
| P0-3 | MCP 协议端点暴露(/mcp + discovery + 0.0.0.0) | 极高 | 中 | compass(我) |
| P0-4 | GEP P0 防退化(W1 verdict 元数据 + serving quality + revoke API) | 极高 | 高 | compass(我) |

---

## 🛡️ SSOT 护栏(粘进每个 /goal)

```
1. n≥12 才跑 LOO(verdict-gate 拦 n<12 · 防 whipsaw 教训2)
2. 易 django PROVEN → 须非易料复证(排 over-fit 假迁移·教训3)
3. confound 先核再下结论(教训3)
4. SSOT 钉死+广播四框(治精神分裂·教训4)·本协议严格执行:任一框改 SSOT 四行→先改 SSOT→再写 FRESH_PROMPT/广播
5. ship 了必验活(教训5)
```

---

## 🅿️ Parking Lot(不碰)

- 维②经济环(credit 口径/结算腿 liveness)
- compass MCP 耦合(Phase 1-4)· 平台 mint_mcp_token
- FDE 招募/RBAC/4 skill 发版
- content-engine 命名合约
- 维① KILL 资产保留(未来上 H800/换真难料重启)

---

## 🚦 当前球(下一动作)

**球在 soul(主)**: 接 3 A-class · canonical 复核 · 借 GPU 跑 distill_loo · 出 verdict

**球在 platform-soul**: cloud divergent branches(本机 6/29 vs cloud 6/6+11k uncommitted)· 解法=手工 merge/rebase · 部署 distill-venv · dry-run

**球在 compass(我·下 session)**: P0-1 → P0-2 → P0-3 → P0-4 顺 ship · 每件验活

**球在 V5**: 等 H100 到位 · 产 frontier-eng 等 5 类 H100-gated 燃料

---

## 📊 当前数据(6/29 22:30)

| 指标 | 值 |
|---|---|
| V5 候选总产 | 37(去重 34) |
| STRONG 解决率 | 5/16(31%) |
| DOUBAO 解决率 | 2/23(9%) |
| A-class 数 | 3 |
| distil 训练 loss | 待跑 |
| held-out win_rate | 待跑 |
| PoI 账本行数 | 1507 |
| PoI 飞轮 liveness | GREEN |
| compass.nautilus.social version | 1.0.1(应 2.3.0) |
| GitHub latest release | v2.1.0(应 v2.3.0) |
| PyPI version | 2.3.0 ✅ |

---

## 🔴 风险与提醒

1. **R3 · 4h 硬限**: 本 session 已用相当长时间 · 下 session 启动后 4h 内 ship P0-1→P0-4 勿拖
2. **R4 · ship 前必 git 状态检查**: P0-1 推前必查 `git status` · 26 commits 领先 · 无未提交
3. **R5 · ship 必验活**: P0-2 部署后必 healthz 200 + version=2.3.0;P0-3 必 curl /mcp + discovery 200
4. **anti-7 · 不用"真"作强调副词**: 见 global memory `feedback_avoid_zheng_emphasizer`

---

## 关联

- LOOP_STATE_SSOT.md · FDE_BUSINESS_CHARTER.md
- memory `session_20260629_v230_audit_unlanded_designs_handover.md` · 本 session 存档
- memory `session_20260629_verify_34_candidates_3_aclass_n12_blocked.md` · verify 存档
- memory `canonical_flywheel_convergence_northstar_20260622.md` · 北极星
- memory `reference_autodata_meta_agentic_data_scientist_20260629.md` · Autodata 分析

---

*最后更新:2026-06-29 22:30 · compass · 用户拍"做好存档+交接+梳理新会话 /goal 机制"*