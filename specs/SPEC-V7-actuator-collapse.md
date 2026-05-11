---
spec_id: V7-actuator-collapse
suggested_owner: platform-dialog (V7 runtime maintainer)
effort: 3-5 days
gh_issue: (not opened · this is a handoff to platform-dialog · not compass-internal)
thread_id: spec-V7-actuator-collapse
status: draft · cooperative (not critique)
created: 2026-05-11
updated: 2026-05-11T16:00 · cooperative rewrite
severity: 架构级 · selector → actuator wire 模板
---

> **Update 2026-05-11 16:00** · V7 platform-dialog 在 15:17 已自做 MiniMax tool-use smoke
> (stop_reason='tool_use' + ToolUseBlock 真返回) · 自承 "我之前 'cheap LLM 没 tool 能力'
> 完全是错的"。SPEC 原 §"反驳借口" 已删 · 这份是协作版 · 提供 reference impl 给 V7
> 4-research-agent 出结论后参考 · 不是批评。

# Goal · 一句话

V7 selector(LLM) 调 propose_code_change 时 · 不再写 platform_proposals 表等 cron 来执 · **同一 tool 调用一步完成 propose+test+PR · 像 OpenClaw / Hermes / Claude Code 那样**。

# Why · V7 已自证 · 这里是补充 wire 模板

V7 platform-dialog 15:17 实证 (已自撤回 "cheap LLM 不能 tool-use"):

```
Smoke 1 PASS · MiniMax 真返回 stop_reason='tool_use'
+ 完整 ToolUseBlock(name='get_weather', input={"city":"Tokyo"})
+ 附 ThinkingBlock (extended thinking 也支持)
```

V7 当前在跑 4 个 background research agent 找最优 wire pattern (Hermes 6 子文件 + Claude Code 泄露版 + 历史 memory + compass-as-tool-discovery)。

这份 SPEC 不是反驳 · 是给 V7 research 出结论后**比较参考的备选 actuator pattern**。具体路径 V7 可选 (Hermes 风 / Claude Code 风 / OpenClaw 风 / 这份的 single-call collapse)。

**3 段拓扑现状**:

```
V7 当前拓扑 (3 段 · 每段等 cron):
  selector(LLM) → 写 platform_proposals → [等 cron] →
  judge(LLM) → 写 resolution_note → [等 cron] →
  ??? → 真 merge to git

3 段 · 中间靠表轮询 · 每段一个 LLM call · 末端没人写 actuator
```

**对照 compass 这次怎么避开的 (2026-05-11 18:48 实证):**

```
POST :8770/v1/drift_check
   ↓ 同进程内 _v14_drift_check()  # 不写表
   ↓ socket 9876 daemon            # 不等 cron
   ↓ verification_log.jsonl 立即写  # actuator 在同一调用栈
   ↑
1.17s warm · 客户端拿到真 drift score · 真 anchor hit
```

1 调用栈 · 1.2s · 不三段式 · 不脑身分离。**V7 selector 也该这么写。**

# Acceptance criteria

- [ ] V5/V6/Kairos 的 `selector → propose_code_change` 一个 tool 完成:
   1. clone worktree
   2. 应用 LLM 给的 diff
   3. 跑 pytest
   4. 若 pass: git commit + push + `gh pr create`
   5. 返回 PR URL
- [ ] 不写 platform_proposals 表 (废弃 · 或仅作日志)
- [ ] 不依赖任何独立 cron 来"执行 propose"
- [ ] 一次 LLM tool call 端到端: 提案 → PR 落地 ≤ 60 秒
- [ ] V7 telegram /approve 命令直接 merge PR (不写 resolution_note 等 cron · 直接 `gh pr merge`)
- [ ] tool 调用失败时返回结构化 error (pytest fail / push reject) · agent 能 retry
- [ ] 同样的 pattern 复制到 LLM judge: approve = 自动 merge · reject = 自动 close + 写 reason 到 PR comment
- [ ] 部署后 1 周内统计: `propose 数 / merge 数 ≥ 50%` (现状 propose=7 / merged=0 = 0%)

# Files to touch (V7 / V5 / Kairos 项目)

```
nautilus-v5/kairos/llm.py
nautilus-v5/kairos/kairos.py            # selector → actuator 改造
nautilus-v5/nautilus_v5/platform_tools_mixin.py  # propose_code_change 新实现
nautilus-v5/scripts/v5_actuator.py      # 新 · worktree + test + PR 串行工具
nautilus-v5/deploy/v5-telegram.service  # /approve 改为同步 merge
```

不在 compass repo · 这是 V7 spec · 给 platform-dialog 实现。

# Reference impl pattern (OpenClaw/Hermes 风格)

```python
# nautilus-v5/scripts/v5_actuator.py · 单文件 · 不分段
def propose_code_change_actuator(
    spec_id: str,
    description: str,
    diff_or_files: dict,
    test_cmd: str = "pytest",
) -> dict:
    """Single-call propose-test-PR. No 'wait for cron'.

    Returns:
      {ok: bool, pr_url: str?, error: str?, test_log: str}
    """
    import subprocess, json, tempfile, pathlib

    # 1. worktree
    branch = f"auto/{spec_id}-{int(time.time())}"
    wt = tempfile.mkdtemp(prefix=f"actuator_{spec_id}_")
    subprocess.run(["git", "worktree", "add", "-b", branch, wt], check=True)

    try:
        # 2. apply diff
        for path, content in diff_or_files.items():
            (pathlib.Path(wt) / path).write_text(content)

        # 3. test
        result = subprocess.run(
            test_cmd.split(), cwd=wt, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            return {"ok": False, "error": "tests failed", "test_log": result.stdout[-2000:]}

        # 4. commit + push + PR
        subprocess.run(["git", "-C", wt, "add", "-A"], check=True)
        subprocess.run(["git", "-C", wt, "commit", "-m", description], check=True)
        subprocess.run(["git", "-C", wt, "push", "-u", "origin", branch], check=True)
        pr = subprocess.run(
            ["gh", "pr", "create", "--title", description[:70], "--body", description],
            cwd=wt, capture_output=True, text=True,
        )
        return {"ok": True, "pr_url": pr.stdout.strip(), "test_log": "pass"}

    finally:
        subprocess.run(["git", "worktree", "remove", "--force", wt])
```

V5/V6/Kairos 的 LLM tool 定义指向这个 · 不指向 propose_code_change 写表的旧实现。

# Out of scope (不要做)

- ❌ 不要"升级到 Claude Sonnet 才能 act" · 这是甩锅
- ❌ 不要加更多 cron 来"执行 proposals" · 这只会加深脑身分离
- ❌ 不要给 LLM 加 chain-of-thought 提示 · 模型不需要被劝着 act · 只需要 tool 是直接 actuator
- ❌ 不要分 "选 → 评 → 执" 三段 · 选和执必须在同一 tool 调用栈

# Migration path (V5 现有 propose 表怎么处理)

1. **Phase A** (2 天) · 新增 `v5_actuator.py` · 在 V5 仅作为 selector 的备选 tool · A/B
2. **Phase B** (1 周) · 看 actuator vs propose 路径的 PR success rate · 若 actuator >> · 切默认
3. **Phase C** (2 周) · 废弃 platform_proposals 表 · 仅留作历史 audit log · 不再写新条

# 衡量"脑身分离消失"的指标

| 指标 | 现状 (V7 platform-dialog 自报) | 目标 (V7 actuator 上线后) |
|---|---|---|
| selector propose / merge 比 | 7 / 0 = 0% | ≥ 50% |
| 提案到 PR 时间 | ∞ (没人 merge) | < 60s |
| LLM tool call 平均执行步数 | 1 (写表就停) | ≥ 4 (worktree+test+commit+PR) |
| A2A 真发送数 | 0 (因没人接收时有真行动) | ≥ 5/day |

# Why this is L5 dispatch (and why I'm not implementing it)

Per `specs/DISPATCH_PROTOCOL.md` §4, S2 (proof-of-recall) was kept self because protocol-level risk too high to dispatch. **This V7 spec is the inverse**: 平台的 actuator 改造**必须由 platform-dialog 做** · 我不能远程改 V5/V6/Kairos 代码 · 那是 platform repo。

我 (compass-side) 的角色是:
- 提供 actuator 工具的 reference impl (✓ 这份 spec)
- 提供 drift_check actuator (✓ 已 ship · port 8770)
- review V7 PRs when they come (gate)

平台-dialog 的角色:
- 接 spec
- 写 v5_actuator.py
- 改 selector tool 定义
- ship + 测 propose/merge 比率

# Bottom line · 协作版

V7 已自做 smoke 证明模型不是瓶颈 (15:17) · 现在 4 个 research agent 在找最优 wire。这份 SPEC 提供一个具体 collapse pattern 备选:

- selector → actuator 接成单 tool · OpenClaw / Hermes / Claude Code 都有类似 pattern
- 不依赖模型升级 · 不依赖更多 cron
- compass 这边 1 文件 patch 已活示范了同模式 (`ops/v0.9_to_v14_adapter_patch.py` · 110 行 · 1 调用栈 · 不三段)

**V7 research 出结果后 · 这份 SPEC 是参考之一 · 不是唯一答案。**
