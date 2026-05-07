# Email · npm support · @nautilus org name resolution

> **不要** 直接发这封 · 先发 EMAIL_TO_IGNIGENA.md · 给 Albert 14 天回复时间
> 仅在 Albert 不回 OR 友好交涉失败后再发
> 走的是 npmjs disputes policy · 不是 takeover policy
> 长度 · 400-500 词 · 准备好 supporting evidence (links · screenshots)

## 何时发

仅当满足以下任一:
- ✅ Albert 14 天没回 EMAIL_TO_IGNIGENA · 且我们之后真的需要 @nautilus
- ✅ Albert 拒绝但场景不合理 (比如他根本没在用)
- ✅ Albert 回复同意 transfer 但 npmjs UI 卡住 · 需要 npm staff 协助

不发的场景:
- ❌ Albert 拒绝且态度合理 · 我们维持 nautilus-compass-mcp
- ❌ Albert 14 天没回但我们没真需要 @nautilus

## 收件信息

- **收件人** · `support@npmjs.com`
- **抄送** · `disputes@npmjs.com` (二者目前是同一渠道 · 都 cc 增加优先级)

## 主题 (Subject)

`Package name dispute · @nautilus scope · active project request`

## 正文

```
Hello npm support team,

I'd like to open a package name dispute under the npm dispute policy
(https://docs.npmjs.com/policies/disputes), specifically requesting
that the @nautilus org be transferred to me.

## Project I'm shipping

  · Project: Nautilus Compass — open-source memory layer for LLM agents
  · Repo: https://github.com/chunxiaoxx/nautilus-compass
  · License: MIT
  · State: active development, 100+ commits in 6 months, CI green,
    published peer-reviewable paper, ~10K real prompts in production
  · Current published package: nautilus-compass-mcp@0.9.5
    (unscoped because @nautilus is taken)
  · Sister Python package: pypi.org/project/nautilus-compass

## Current state of @nautilus scope

To my knowledge:
  · Sole package: @nautilus/config v1.3.1
  · Last published: 2022-04-06 (about [N] years ago)
  · Maintainer: ignigena (Albert Martin)
  · Origin project: github.com/dadi/nautilus-config (DADI Engineering,
    a content platform that has stopped operations)

The @nautilus/config package is a configuration utility for an
abandoned platform; it has not received updates in 4+ years.

## Why I'm asking

I have an active, growing open-source project that ships under the
"Nautilus" name, and have already attempted to coexist on the npm
ecosystem by publishing as the unscoped `nautilus-compass-mcp`. I
believe @nautilus would be a more fitting and discoverable namespace
for the project's expanding package set (e.g., @nautilus/compass-mcp,
@nautilus/compass-cli, @nautilus/a2a-adapter).

## What I have already tried

I reached out to Albert Martin (ignigena) via [GitHub / email] on
[YYYY-MM-DD] to ask if he'd consider any of:
  1. Transferring the @nautilus org to me
  2. Granting me publish rights to the @nautilus/compass-* prefix
  3. Or simply declining

[Outcome — fill in based on actual response, e.g.:]
  · He has not responded after 14 days. (Original message attached.)
  · He declined but indicated the scope is no longer in active use.
  · He agreed in principle but would need npm staff assistance to
    transfer the org.

## What I'm requesting

Per npm dispute policy, I'm asking npm support to evaluate this
case and consider one of:
  · Transferring @nautilus org admin to me, with @nautilus/config
    preserved at its current version under my maintenance, OR
  · Mediating a transfer of @nautilus org with Albert's consent, OR
  · Granting me publish rights scoped to @nautilus/compass-* package
    names without disturbing existing @nautilus/config maintenance.

I'm equally happy with any of those outcomes; the goal is being able
to publish my project's packages under @nautilus while leaving the
existing maintainer unaffected.

## Documentation

  · Project repo (active): https://github.com/chunxiaoxx/nautilus-compass
  · Current npm package: https://www.npmjs.com/package/nautilus-compass-mcp
  · Existing @nautilus/config: https://www.npmjs.com/package/@nautilus/config
  · DADI Engineering status (source of @nautilus/config): [link to confirmation]
  · My communication with ignigena: [attach forwarded email or GitHub
    issue link]

I'm happy to provide additional context, documentation, or
clarification. Thank you for considering this request — I appreciate
how non-trivial these dispute decisions are, and I'd rather work
within npm policy than try anything outside it.

Best regards,

Chunxiao
github.com/chunxiaoxx
chunxiao.wang@npmjs.com [or whichever email is your registered npm account]
```

## 邮件附件

发送前准备好以下证据 (附件 · 不要 inline 大段贴):

1. **`evidence_1_project_activity.png`** · GitHub repo screenshot · commit count + CI badge + paper link
2. **`evidence_2_dadi_inactive.png`** · `dadi.tech` 或 `dadi.engineering` returning 404 / archived screenshot
3. **`evidence_3_communication_attempt.png`** · 你发给 Albert 的 email/issue 截图 + 14 天 silence 时间戳
4. **`evidence_4_paper_draft.pdf`** · 我们的 paper PDF · 证明这是 academically active project

## 取消条件

不要发的情况:
- Albert 友好回复 (任何 case A/B/C 都不发)
- 我们决定维持 `nautilus-compass-mcp` (已 live · ship 不阻塞)
- v1.0 launch 前 1 周不发 (临门一脚不要节外生枝)

## npm support 期望响应时间

- 自动回复 · 24h
- 第一次人工回复 · 3-7 工作日
- dispute 决议 · 2-4 周
- 转交流程完成 · 4-8 周

## 失败应对

如果 npm support 拒绝:
- 不要重发 / 不要 escalate / 不要在 Twitter 发酵
- 维持 `nautilus-compass-mcp` 当 v1.0 final
- 6 个月后 retry · 那时候我们应该有更多 traction (downloads · stars · paper citations)
- 或 · 直接迁到 `@chunxiaoxx/compass-mcp` (你 user scope) · 不再考虑 @nautilus

## 后续

不发这封 = 不需要回头看。发了 = 等 1 个月再决定下一步。
