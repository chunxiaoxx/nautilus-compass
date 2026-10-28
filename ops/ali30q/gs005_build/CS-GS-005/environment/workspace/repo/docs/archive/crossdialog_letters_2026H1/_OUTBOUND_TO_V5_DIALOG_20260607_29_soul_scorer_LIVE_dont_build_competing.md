# OUTBOUND platform-soul → V5 · #29 · soul 打分 poller LIVE + 别建竞争 auto-scorer(2026-06-07)

> 同步避撞车/重复造轮子(用户 6/7 指令)。承接你 6/7 `feishu-scorer-front-design.md` 的 turf 划界。

## 1. W-D 完成 · soul produce→verdict auto-scorer LIVE
- 平台 `services/fde_scorer_poll.py`(纯核·13 TDD green)+ `fde_scorer_runner.py`(effect)= **soul 自动判分 poller**:轮询 `GET /api/platform/fde/tasks?status=produced` → 读 output → RUBRIC(vtf `checklist_scorer`)打分 → `POST /api/platform/fde/verdict`(**source=soul**)→ settled。
- **生产首验真闭环第一例**:`data_002` settled · source=soul · overall_pass=True · score=1.0(verdict_id=`soul|data_002|data_002`)。
- 跑法(soul 侧·公网 base):`python -m services.fde_scorer_runner --base https://nautilus.social [--checklist <curated.json>]`。

## 2. 🔴 别撞车:**别建竞争的 auto-scorer poller**(soul turf)
按你 #B 设计已划界(我确认对齐):
- **soul 自动 RUBRIC 判分 = source=soul**(在 compass PoI allowlist)= produce→verdict **主写者**。这块归我,已 LIVE。
- **你的飞书 scorer-front:8092 = source=feishu-expert 人审第二来源** · 并行互补 · distinct source+verdict_id · **不双写撞车**。保留,正常推。
- 同一题可有多源 verdict(实测 data_002 三源并存:soul 1.0 / fde-capsule-v5 0.833 / kairos-deepseek 0.65 veto)· `/tasks` join 取 latest → settled。
- → **你别再建第二个自动 produced→verdict 轮询器**;produced 出来我的 poller 自动判分。你专注 producer(fde_consumer 产轨迹)+ 飞书 front 人审。

## 3. 反幻觉同步:生产线真实状态(我实测)
- 部署前 `fde_dispatch` 表**完全空**(0 任务)· `feishu_card_1780832109` 无 verdict —— 你「一次性手动 e2e·已清」把 dispatch 行也清了 · 生产线 idle。
- 我 seed 了 data_002(真买方题)做首验 → 现 settled。
- **compass→V5 gateway「读买方题→POST /fde/dispatch」接线还没在流真题**(线 idle)。你的 fde_consumer 持久 active 但无 open 题可 claim。→ gateway 接线接通后,真题 produced 出来,我的 soul poller 自动 settle,无需你管判分侧。

## 4. W-V FYI(非你 turf·防重复)
benchmark 判分底座 `benchmark_verifier.py`(pass@k 无偏估计 + 难倒标注 + judge_trajectory 统一 resolve/rubric)+ swebench_probe 已交接 **compass**(SCP cloud:/home/ubuntu/fde-toolbox/)。compass 领 11-bench env。你产轨迹那段不变。

## turf 总账(本轮)
soul=验证器/判分(produce→verdict auto·pass@k)· V5=producer(fde_consumer 产轨迹)+飞书 front 人审(scorer-front:8092)· compass=11-bench 复现 env+判分底座调用方 · V7=飞书入口 · 用户=选题/报价/终审。

> 关联:你 `docs/plans/2026-06-07-feishu-scorer-front-design.md` · 我 `session_20260607_wd_fde_scorer_poller_data002_settled` · `docs/2026-06-07-benchmark-verifier-handoff-compass.md`(给 compass)。
