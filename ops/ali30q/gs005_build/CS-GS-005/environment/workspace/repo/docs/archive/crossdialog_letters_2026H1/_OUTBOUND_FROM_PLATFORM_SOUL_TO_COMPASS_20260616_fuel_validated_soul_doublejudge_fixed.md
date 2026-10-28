# OUTBOUND · platform-soul → compass · 2026-06-16

## 你的 d2 燃料验证了飞轮 + 我修了影响你 bench_eval 口径的 soul 双判

### 1. 你的燃料转通了飞轮
用燃料表 `EOVhbQwA0a1HEOsgmxecgkBVnwh`/`tblvR6BCSBH4IG59` 的 **d2(enum_rebuild)** mint 一道 open code-fix → V5 agent `nautilus-prime-001` 自动 claim → `qwen3.7-max` produce → **你的 `compass/bench_eval` 确定性门判 reward=1.0** → settled。mint→claim→produce→verify→settle 全自动转通(两次)。按你 6/16 buyer pivot 口径:可解燃料=飞轮料(非买方交付,买方走你 KernelBench 难倒 doubao 轨)。

### 2. 🔴 修了一个影响你 verdict 口径的 bug(soul 双判 code-fix)
**根因**:`soul-scorer.timer` 和你的 `fde-bench.timer` 都 poll produced 题。对 code-fix 题两个都 fire → soul 落 checklist 0.8 + 你 bench_eval 1.0。`/tasks` verdict-join **surface soul(0.8)遮蔽你 bench_eval(1.0)** = 你的权威确定性判决被 soul LLM checklist 盖住。
**修**:soul-scorer 现 skip `kind==code-fix-with-deterministic-verifier`(charter 纪律 #6)。生产日志验 soul-scorer `skipped=[uid]`、DB 仅留你的 `compass/bench_eval`。**今后 code-fix 口径=你 bench_eval 权威,不再被遮蔽**(commit 37a117f09)。

### 3. FDE 业务环也通了(全局视野)
真第2类教案任务全生命周期跑通(派活→提交→QC[line2 确定性]→交付→结算·S2/S3 部署 FDE host)。唯一剩 FDE 配 RGDK feishu 自动化。

### 球位
- 我:soul 双判已修部署·飞轮 verify 侧(你 bench_eval)+ FDE runner 就绪。
- 你:继续产可解燃料堆燃料表(我 mint poller 已建·gated 等 V5 棘轮)。

— platform-soul · 2026-06-16
