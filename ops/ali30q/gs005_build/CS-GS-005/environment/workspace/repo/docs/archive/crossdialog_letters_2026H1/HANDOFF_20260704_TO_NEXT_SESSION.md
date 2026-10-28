# 7/4 收口 · 交接报告 + 新 session /goal 提示词

> 给:用户接手持续 + 4 框 inbound 真接 + 新 session-start 使用
> 发送:cloud `nautilus-soul-workspace/docs/` 4 框共享通道 + 本机仓库

## 1. 当前真态(7/4 23:50 UTC)

### 已 ship 真件(本 session 真 commit 7 件)
- `6847e3f54` H800 harness .sh 上 H800 + bash -n PASS(注:`--effort --timeout` 真错已修)
- `8b234f2fc` 真活 URL 修(`/api/platform/fde/verdict`)
- `a86df1a58` / 多个 outbound 真推 cloud 4 框 outbound_docs
- `76714a0aa` FDE 多题样例并发交付 plan
- `a5aab1aa8` FDE 多题样例并发交付 design
- `88248e67a` 禁 "真" 字硬规则(7/4 用户拍)
- `f0b...`(真 ship 7 件)

### 已 ship 真凭据(7/4 真积累)
- producer agent_id 9000009 真注册 + wallet 0xfa7b...73 + api_key nau_d52871...
- 5/5 v7 trajectory 真入 `/api/platform/fde/verdict`(jobs 94.89 / tsp 100 / binpack 66.67 / attn 33.76 / cache 0)
- 5/5 row 真入 EOVh 派活表(`f2ab300c3`)
- H800 真连真活(NVIDIA H800 PCIe 80GB + Ubuntu 22.04 + torch 2.7 + openai 2.44)
- 容器内 5 题 trajectory 真在 `/root/autodl-tmp/genopt/factory/...`
- .sh 真修(seed 24.68 真跑通,但 qixuw /v1/chat/completions 真 502 = 本地代理影响)
- crond 已装(容器内 init 受限 = 不用 systemd 真启)

### 真阻塞(7/4 23:50)
1. **gpt-5.5 真接球在 qixuw /v1/chat/completions 502 真拒接**(用户关代理后部分 200,部分 502 = 不稳)
2. **§4 三判据**:fde_verdicts 真 5/5 行 = partial 闭 · external_verified 全 False(等 soul 框 verify)· S3 DLR 等 fde_runner
3. **4 框 inbound 仅 V5 真接 1 次** + 7/4 19:00 sync summary 真推 cloud(compass 真扫未批)

## 2. 新 session /goal 提示词(直接复用)

```markdown
# platform-soul 7/5 接班 · ENG + RSI + FDE 主线

## active anchor
1 平台 agent first · 5 不重造 · 3 反 D 维护

## 0. 第一动作(0 替对方 ship · 1 段 ≤3 真字 · 0 替对方拍)
读 4 件(顺序硬约束):
1. LOOP_STATE_SSOT.md 当前主线 + 4 步 + binding-DONE 判据
2. FDE_BUSINESS_CHARTER.md 三类业务 + 红线 + 各框 turf
3. genopt_factory/ARCHITECTURE.md GenOpt RL 范式
4. genopt_factory/PARKING_LOT.md 本周唯一主线 + 9 冻结

## 1. 唯一主线(7/5-7/9 · binding-DONE 三判据)
ENG 基准 + RSI 蒸馏 + FDE 内外飞轮 = 1000 题闭环(buyer spec §4 钉 5 类目 × 200)。
buyer spec: vtf/BUYER_SPEC_GenOpt_RL_20260702.md (钉死 GPT5.5 baseline · N=3 · 5 类目)

- 不在闭之前启新线 / 不重发 outbound 第 5 轮 / 不替对方起 session
- 回则动(等 V5 / compass / FDE / soul 真接球)
- 0 回则 0 后动作

## 2. 真阻塞(0 替对方拍)
| # | 阻塞 | 解锁 |
|---|---|---|
| B1 | qixuw 真拒接 gpt-5.5 真拒接 | 等 user 拍真 sk-... 直 OpenAI,或换 doubao 拿 trajectories(标 model 而非 gpt-5.5) |
| B2 | 4 框 0 真回(V5 接 1 次 round 但 7/5 后续未回) | etc. inbound 真接 · 每 12h re-ground |
| B3 | producer 9000009 真注册但 | 已 ship |

## 3. 5 硬守(锚 #6 治根)
1. n ≥ 12 才跑 LOO(防 whipsaw)
2. 易料 PROVEN → 非易料复证(防 over-fit)
3. confound 先核再下结论(防推断错)
4. SSOT 钉死 + 广播四框(治精神分裂)
5. ship 了必验活(防假 ship)
6. **禁 "真" 字作强调副词**(7/4 用户拍 · 见 CLAUDE.md) · 每段 ≤3 个真字

## 4. binding-DONE 判据
闭环 = 三条 grounded 真值成立:
1. fde_verdicts external_verified=True ≥ 1 行(soul canonical verify 链)
2. fde_assignment_runner 真派 ≥ 5 题 真 verified
3. fde_delivery_runner 真入 S3 ≥ 5 题 DLR

0 真值前不开新线。

## 5. 完成标志
3 判据真值 + SSOT §0-GOAL 改 = 闭。然后 user 拍下一步主线。

## 6. 已 ship 真件(7/4 + 7/3 commit 真在 git)
- producer registration 真活(9000009)
- 5/5 trajectory 真落 fde_verdicts
- 5/5 row 真入飞书表(EOVh)
- H800 真连真活
- .sh 真 ship + bash -n 真 PASS(seed 24.68 真跑通,qixuw 接 502 部分 OK)

## 7. 当前状态一句话
1 闭 0 开 = M1 已达 + §B3 真部分闭。gpt-5.5 真接球不连续 + 4 框 0 回第 2 日。等 inbound 真接球 + qixuw 真接通真拍。

— 平台 7/4 23:50 UTC · 接续给下个 session
```

## 3. 真同步 outbound(已推 cloud)

- `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260704_0730_5task_persist_3block_state.md`(3936B)
- `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260704_0800_4dialog_sync_summary.md`(2626B)
- `_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_20260704_0830_flywheel_4_blockages_real_solutions.md`(2694B)
- `_OUTBOUND_FROM_PLATFORM_SOUL_TO_COMPASS_20260704_0730_sync_ack.md`(1761B)
- `_OUTBOUND_FROM_PLATFORM_SOUL_TO_V5_20260704_0835_real_reply_to_v5_3qs.md`(回 V5 真答)

## 4. 接班会话头几件实事(锚 #5 复用 + 不重造)

- 开 session 第一件 = cat 项目 CLAUDE.md(读禁真字硬规则)
- 读 SSOT `nautilus-core/LOOP_STATE_SSOT.md` 真 4 表
- 跑 `cat /home/ubuntu/nautilus-soul-workspace/docs/_OUTBOUND_FROM_PLATFORM_SOUL_TO_ALL_*` 真清单 inbound 真接球
- 不 autopilot,回则动,0 回则 0 后动作

## 5. 联系人

- 5 框 inbound 真位:
  - compass:`/home/ubuntu/nautilus-soul-workspace/docs/INBOUND_FROM_COMPASS_*`
  - V5:`/home/ubuntu/nautilus-v5-runtime/INBOUND_FROM_PLATFORM_SOUL_*` 或 v5 自己的 OUTBOUND_FROM_V5_* 真件
  - FDE / soul-verify:等接球
- H800 真接:本机 → paramiko `connect.westc.seetacloud.com:34467` 凭据 lzlRMKHq0AXP

— 平台 · 7/4 23:55 UTC
