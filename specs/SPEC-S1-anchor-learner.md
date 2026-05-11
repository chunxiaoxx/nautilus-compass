---
spec_id: S1
suggested_owner: V5
effort: 3 days
gh_issue: (not opened · waiting L2 evidence gate)
thread_id: spec-S1-anchor-learner
status: draft
created: 2026-05-11
---

# Goal

每周扫 `verification_log.jsonl` · 自动生成 `anchors_*.json` PR · 收紧 FP 锚点 · 提取 FN 信号 · 把 v1.3 手动校准变 cron。

# Why V5

- V5 是营销域 agent · `anchors_compass_marketing.json` 正是 V5 域的 prompt 锚
- V5 已经在做 verification_log 类似的分析 (`v5_daemon.py` 跑 monitor)
- 派 V5 实现就是延伸现有工作 · 不是凭空新建

# Acceptance criteria

- [ ] `tools/anchor_learner.py` · 输入 7 天 `verification_log.jsonl` + Telegram `/approve`/`/reject` 日志 · 输出锚点 diff 建议
- [ ] FP 检测: 锚点 cos ≥ 0.65 且 24h 内对应行动**没被 reject** → 收紧锚点 (提 +0.05 阈值或重写措辞)
- [ ] FN 检测: 锚点全 < 0.5 但对应行动 24h 内被 `/reject` → 从 reject reason 提取新负锚点 candidate
- [ ] GitHub Action · 每周一 00:00 UTC 跑 · 生成 PR 标题 `anchors: weekly auto-tune {date}` · base anchors_compass_marketing.json
- [ ] PR body 含 metrics 表: `before_fp_rate / after_fp_rate / anchors_added / anchors_modified`
- [ ] PR body 跑过 `compass.drift_check` · 无 over-claim
- [ ] 单测 ≥ 80% 覆盖 `tools/anchor_learner.py`
- [ ] 不自动 merge · 需 review (我把关)
- [ ] CHANGELOG 写入 v1.4 entry

# Files touched

```
tools/anchor_learner.py                       (new · ~300 lines)
tools/tests/test_anchor_learner.py            (new · ~200 lines)
.github/workflows/weekly-anchor-tune.yml      (new · ~40 lines)
docs/ANCHOR_LEARNER.md                        (new · ~100 lines · how it works · how to interpret PR)
CHANGELOG.md                                  (add v1.4 entry)
```

# Compass self-use requirements (V5 必须证明)

- [ ] V5 拾起 spec 时跑 `compass.recall(thread_id="spec-S1-anchor-learner", agent_type="v5")` · 拿前案
- [ ] V5 PR body 引用至少 1 条 recall top-3 + 片段 (e.g., "v1.3 calibration round 2 教训: extreme-literal phrasing 必要 · cite session_20260511-1750")
- [ ] V5 PR body 跑 `compass.drift_check(prompt=PR_body)` · 截图贴 PR comment · alert == false
- [ ] V5 实现完成 `compass.ingest_obs(thread_id="spec-S1-anchor-learner", content="实现要点 + 测试结果 + 留给 v1.5 的待办")`

# Review gate (我看)

按 DISPATCH_PROTOCOL.md §3 五条 checklist:

1. drift_check PR body alert == false
2. proof-of-recall: cite ≥ 1 条 top-3 + 片段
3. tests ≥ 80% + green CI
4. CHANGELOG bump v1.3 → v1.4
5. 5 个 agent_type 客户端 E2E 不破 (跑 `python _test_wrapper_agent_type.py` × 5 token)

# Out of scope (V5 不要 over-engineer)

- ❌ 不要改 daemon.py / mcp_server.py · 锚点是数据 · 不动协议
- ❌ 不要自动 merge · 必须 PR + review
- ❌ 不要 cover anchors_platform_base.json · 这份不是 V5 域
- ❌ 不要做 ML 模型微调 · 仅基于阈值/cos/reject 信号的规则学习
- ❌ 不要加 LLM API 调用提取新锚点 · 用现有 BGE-m3 embedding 找最近邻就够

# Implementation hints

```python
# tools/anchor_learner.py 主框架
def collect_signals(log_path, days=7):
    """读 verification_log + telegram_log · 返回 (anchor_id, hit_cos, action_taken, was_rejected)"""
    ...

def detect_fp(signals, fp_threshold=0.65):
    """高 cos · 行动通过 → FP · 建议收紧"""
    ...

def detect_fn(signals, reject_log):
    """reject 但锚点都没命中 → FN · 建议加锚点"""
    ...

def propose_diff(fp, fn, current_anchors):
    """返回 anchors_*.json 的 JSON patch"""
    ...

def open_pr(diff, metrics):
    """gh CLI · 不 auto-merge"""
    ...
```

# Risk

- FP/FN 信号弱 (early days · 不够多 reject) → 第一次 PR 可能改动很小 · 这是 OK 的
- V5 实现可能过度依赖 LLM · 用 hints §5 阻止
- 锚点过度收紧导致漏检 (FN 增) → review gate 要看 metrics 表趋势 · 不只看单次

# Success metrics

- 第一次 PR: 至少 1 个 FP 锚点收紧 + 至少 1 个 FN candidate · 总改动 ≤ 5 行
- 8 周后: 无人工校准前提下 · v14-style 13-段文章 drift_check FP rate < 15% (基线 v1.3 7.7% · 不退化)
