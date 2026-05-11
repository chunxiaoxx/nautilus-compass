# Compass Spec Dispatch Protocol

> 把 compass 升级任务派给平台 agent (V5/V6/V7/Kairos) · 由 compass-side 维护者 (我) 把关 review。
> 这是 L5 dogfood: agent 实现 compass · agent 用 compass 自查 · compass 把关 agent。

## 0. 前置 (DO NOT skip · 否则同 P1-1 fake-closure)

派任何 spec 之前必须达到 **L2 evidence gate**:

- `verification_log.jsonl` 显示 `agent_type: vN ≥ 10/day` 持续 **3 个连续日**
- `grep -E 'compass|recall|drift_check' nautilus-v5/deploy/*.py` 非空 · 说明 agent 真在调
- 三件都齐 · 才有资格谈派活

监控: `ops/monitor_l2_evidence_gate.sh` cron 6h 一跑 · 未达标 Telegram alert。

## 1. Spec 文件结构 (specs/SPEC-SN-name.md)

```yaml
---
spec_id: S1 / S2 / S3 ...
suggested_owner: V5 / V6 / V7 / Kairos
effort: 2-5 days
gh_issue: (filled when dispatched)
thread_id: spec-SN-{name}
status: draft / dispatched / in_progress / review / merged
---

# Goal
1 句话 · 不超过 25 字

# Acceptance criteria (可验证 · 不抽象)
- [ ] 具体测试用例 1
- [ ] 具体测试用例 2
- ...

# Files touched
- path/to/file.py
- path/to/test_file.py

# Compass self-use requirements (agent 必须证明)
- [ ] 拾起 spec 时跑 `compass.recall(thread_id="spec-SN-name")` · 拿前案
- [ ] PR body 引用至少 1 条 recall top-3 + 片段
- [ ] PR body 跑 `compass.drift_check` · 无 over-claim
- [ ] 实现完成 `compass.ingest_obs(thread_id="spec-SN-name", content="实现要点+教训")`

# Review gate (我看)
按 DISPATCH_PROTOCOL.md §3 五条 checklist · 任一不过 = request changes

# Out of scope (避免范围蔓延)
- 列具体不做的事 (V5 容易 over-engineer)
```

## 2. Agent 拾任务流程

```
[on platform-dialog cron · 每 24h]
  for spec in compass.recall(scope=spec_open, agent_type=V5, k=5):
      if spec.suggested_owner == "V5" and spec.status == "draft":
          accept(spec)            # → status: in_progress
          break
  else:
      idle()                       # 没合适的 · 继续 marketing 主业

[on accept]
  1. 拉 nautilus-compass repo (worktree · 独立分支)
  2. compass.thread_recall(spec.thread_id) → 拿全文 spec
  3. compass.recall(spec.goal, k=5) → 拿历史相关 PR / 教训
  4. 读 spec.files_touched · 读现有代码
  5. 实现
  6. 跑 pytest → 必须过
  7. drift_check(PR body) → 必须 alert == false
  8. PR 提交 · body 含: recall top-3 cite + ingest_obs 凭证 ID
  9. compass.ingest_obs(thread=spec.thread_id, content=PR summary)
```

## 3. 我的 Review gate (5 条 · 全过才 merge)

```yaml
review_checklist:
  1_drift_check: PR body 跑 compass.drift_check · alert == false
  2_proof_of_recall: PR body cite ≥ 1 条 recall top-3 + 引片段 (proof-of-recall 自证 · 防 fake-closure)
  3_tests: 新增功能 ≥ 80% 覆盖 · 全 green CI
  4_changelog: CHANGELOG.md 写清 + 版本号 bump (semver)
  5_no_regression: 现有 5 个 agent_type 客户端 (claude-code-compass-dialog / V5 / V6 / V7 / Kairos) E2E 不破
```

任一不过 = `request changes` · 不 merge · 不强行通过。

## 4. 派活节奏 (不是一次性 dump 3 个)

```
T0  L2 evidence gate 达标 (3 天 ≥ 10/day × 3 agent)
T0  → 派 S1 (anchor_learner) to V5 · 单个 · 5 天
T+5 → 看 V5 PR 质量 · 不过 = 把 S1 收回自己做 · 不再派
T+5 → 通过 = 再考虑派 S3 (cross-project) to V6 · 注意 S2 留我自己 (协议级风险高)
```

**绝不一次 dispatch 3 个**。一次一个 · 走完看质量 · 再决定下一个。

## 5. Anti-pattern · 不做的事

- ❌ 派 spec 前没等 L2 evidence (305 / P1-1 模式)
- ❌ 一次派 3+ 个 · 平台没那么多并发能力
- ❌ 用 platform-dialog (人) 转手实现 · 这是 L5 的反面 · 失去自动化意义
- ❌ Spec 写得太抽象 (`make it better`) · acceptance criteria 必须可测
- ❌ Review 标准放水 · 一次放水 · 下次全部 dump 给我 review
- ❌ V5 派去做 S2 (协议级) · 域不匹配 · 必出 P1-1 fake-closure

## 6. Spec inventory (T = 2026-05-11)

| spec | suggested_owner | effort | status | blocker |
|---|---|---|---|---|
| S1 anchor-learner | V5 | 3d | draft | L2 evidence gate not hit |
| S2 proof-of-recall | (我 · 不派 · 协议级) | 5d | draft | 等 V5 S1 跑通后再评估 |
| S3 cross-project recall | (我 · 不派 · 短平快) | 2d | draft | 立即可做 |

S3 我自己做 · S1 等 L2 达标后派 · S2 看 S1 结果再说。

## 7. 升级此协议本身

当我们发现这个协议有漏洞 (例: agent 学会绕过 drift_check) · 写新 session 到 thread `compass-dispatch-protocol-evolution` · 不直接改这份文档 · 走 review。

协议本身也走 dogfood。
