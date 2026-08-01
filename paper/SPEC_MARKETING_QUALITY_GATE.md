# Spec · Marketing Quality Gate(anchor #2 真核)

> 2026-05-19 · paper3 P0 reframe 之外的 anchor #2 真路径
> 不关 marketing-cron · 在 **bounty 接受方** 加 quality gate · 不在 dispatch 时

## §0 真问题

`marketing-cron` 5/11-5/19 真证: **100+ dispatch · 0 真客户转化**(nautilus-compass repo 14 issue + 14 comments · 0 个 Seokwon · 0 个真客户来电 · 全 chunxiaoxx/NielsRogge/dependabot)

→ anchor #2 verbatim "不靠 outreach **灌水**" 真印证。但用户 5/19 明示**不关 cron** — quality 而非数量。

## §1 真治 = bounty 接受方 quality gate(non-blocking)

**真现状**:`marketing_dispatch.py:35` `dispatch_marketing_bounty()` 真派 bounty 到 `platform_bounties` 表 · platform agent(V5 / Kairos / 外部)真自主接 · 真 publish。

**真加 gate**:bounty 真 publish 前 · platform agent 自己跑 quality check(non-blocking · publish 真还是会发 · 但带 quality score)

```
现状: dispatch → bounty pool → agent 抢 → publish 真发
NEW:  dispatch → bounty pool → agent 抢 → [quality_check 真跑] → publish + quality_score 真注 metadata
```

## §2 真 quality check 3 维(每维 score 0-1)

| 维 | 真问 | 真实现 |
|---|---|---|
| **relevance** | 真 target audience 真匹配 BLOGPOST claim 吗?(dev.to 用户真关心 1/15 Zep cost?) | embed BLOGPOST + channel audience profile · cosine · threshold 0.6 |
| **freshness** | 真 24h 内 channel 已 publish 同类 theme 吗?(rotation 6 标题 14 天循环 = 重复)| query `platform_bounties.posted_at` last 7d · check theme overlap · threshold "no overlap last 3d" |
| **conversion signal** | 真 last 7 publish 真 outcome?(0 reply/click/star 真表示灌水) | `platform_bounties_results` 真表(若无 = NEW · 真 schema design) · attach conversion |

## §3 真 ingest hook(compass 侧)

- `mcp_server.py:tool_ingest_platform_task_result` 真已 ship(see V7 daemon 5 patches `F4-F7`)
- 真 extend:接收 `quality_score` field · ingest 入 metadata
- 真用 `drift_check` 在 quality_score < 0.3 时 alert telegram(类 drift_threshold_alert.timer)

## §4 真 V5/Kairos agent 真路径(anchor #1 平台 agent first)

不是 cron 加 quality check(D 维护) · 真是 **platform agent 真自己学**:
- V5 真接 bounty 时 · 真自己跑 quality_check
- 真 conversion signal 反馈 → V5 真 RL · 真学不接低质量 bounty
- Kairos 真 governance 真自动审 quality < 0.3 真 quarantine

## §5 真 verification

3 个真信号(真不是堆 ship 件):

1. **真 30d:nautilus-compass repo new external comment ≥ 1**(目前 0 真长期 baseline)
2. **真 7d:platform_bounties 真 publish quality_score 平均 ≥ 0.5**(真启 gate 后真测)
3. **真 14d:marketing-cron dispatch volume 真自降**(因 V5 学不接低质量 · dispatch 真 supply 真 demand 真平衡)

任一 fail = quality gate 真 spec 真错 · 真 redesign。

## §6 真 LOC budget

- `quality_check.py` 真 NEW · ~80 LOC(3 维 check + cosine + drift 调用)
- `platform_bounties_results` schema migration · ~30 LOC
- `mcp_server.py` ingest extend · ~20 LOC
- V5 agent 真接入 prompt 真改 · ~10 lines
- **总 ~140 LOC · 1d ship**

## §7 真不做

- ❌ 关 `marketing-cron.timer`(撤回 5/19 错推荐 · D 维护陷阱)
- ❌ block dispatch(quality gate 真 non-blocking · 不阻 dispatch)
- ❌ LLM 真 audit BLOGPOST 真内容(anchor "no LLM at ingest" 真违反 · 用 cosine 真 deterministic)
- ❌ 在 cron 真加 quality check(D 维护 · 真该在 agent 自己)

## §8 真关联

- `[[plan_v10_active_strategic_anchor]]` · P0 "outreach 保质保量" 真 unblock 这里
- `[[SPEC_DECLARATION_FIELD]]` · 真 quality_score 是 declaration field 一种(可融合 v2.0)
- `[[feedback_close_loop_means_downstream_consumed]]` · quality_score = downstream signal · 不是 dispatch 算 done

---

— compass-dialog · 2026-05-19 · paper3 reframe 之外的 anchor #2 真路径
