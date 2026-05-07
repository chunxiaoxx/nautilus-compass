# Email · Albert Martin (Ignigena) · @nautilus npm scope

> 目的 · 友好商讨 · 不 demand · 不 dispute · 给他充分 opt-out 空间
> 长度 · 250-300 词 · 发完等 7-14 天 · 不催

## 收件信息

- **收件人** · Albert Martin
- **邮箱** · 没在 GitHub profile 公开 · 走 GitHub 留言
  - 最佳路径 · `https://github.com/Ignigena/nautilus/issues/new` · open polite issue
  - 或 · `https://github.com/Ignigena` 主页有 personal site · 找联系方式
- **若必须邮件** · 可能在他 npm profile · `https://www.npmjs.com/~ignigena` 有公开 email
- **抄送** · 无 · 单线

## 主题 (Subject)

`Possible coexistence on @nautilus npm scope · friendly inquiry`

## 正文

```
Hi Albert,

I'm Chunxiao, an independent dev based in China. I'm reaching out
because I'm shipping an open-source memory layer for LLM agents called
Nautilus Compass, and I'd love to talk about a possible coexistence
on the @nautilus npm scope.

A bit of context on what I'm building:
  · Open-source MIT · github.com/chunxiaoxx/nautilus-compass
  · Paper-grade benchmarks · 56.6% on LongMemEval-S (ties Zep SOTA at 1/15
    cost) · 41% on EverMemBench-Dynamic
  · Already 100+ commits · CI green · about to ship v1.0
  · Currently published as the unscoped `nautilus-compass-mcp` on npm
    because @nautilus is taken

I noticed @nautilus/config (v1.3.1, 2022) and your separate
github.com/Ignigena/nautilus framework. I want to be upfront: I'm not
asking you to give up that work, and I have no interest in disrupting
your project. The namespace collision is purely accidental — your
Nautilus is a JS framework, mine is a Python LLM memory layer, and
the audiences don't overlap.

A few options I wanted to put on the table — please pick whichever
(or none) you find acceptable:

1. **Org transfer** · If you no longer plan to publish under @nautilus,
   would you be open to transferring the org? I'd happily migrate
   @nautilus/config to a fork or to you personally so it stays live.
2. **Granted scope** · Could you add me as a publish-restricted
   collaborator on @nautilus, scoped to packages prefixed
   @nautilus/compass-*? Your existing config and any future packages
   stay yours, mine stay clearly mine.
3. **Status quo** · If neither works, I'll keep using `nautilus-compass-mcp`
   (already live). No bad feelings — I just wanted to ask before doing
   anything else.

Happy to send more details on the project (paper draft, benchmark
methodology, etc.) if useful. I won't escalate to npm support or do
anything you'd be uncomfortable with — this is purely a friendly
inquiry.

No rush at all. If you'd rather decline outright, a one-line "thanks
but no" is totally fine and I'll take it from there.

Best,
Chunxiao
github.com/chunxiaoxx
```

## 发送时机

- **不要** 周五下午 / 周末 / 美国节假日
- 周二 / 三 · 美国时间 9-11 AM PT (Albert 在 Austin, TX · CT 时区 · 11-13 中部)
- = 北京 周三 / 四 · 凌晨 0-3 点 (定时发)

## 回复处理 playbook

### Case A · 同意 transfer

- 立刻感谢 · 问他 transfer 流程偏好 (npmjs UI 还是 npm support 协助)
- transfer 后 24h 内 · publish `@nautilus/compass-mcp@1.0.0` (跟 unscoped 同 code)
- `npm deprecate nautilus-compass-mcp@* "renamed to @nautilus/compass-mcp"`
- README + docs 改回 @nautilus/compass-mcp
- 给他公开致谢 (paper 致谢页 + GitHub README contributors 区)

### Case B · 同意 granted scope (option 2)

- 感谢 · 接受
- 写明确的 ownership boundary · 我们的包都 prefix `@nautilus/compass-*`
- 他保留对 @nautilus org 的 admin · 我们做 maintainer of compass-* prefix
- 后续 v1.1 / v1.2 都用 @nautilus/compass-mcp · @nautilus/compass-cli 等

### Case C · 拒绝

- 一句话感谢 · 不追问 · 不 escalate
- 维持 `nautilus-compass-mcp` 这个名 · 当作 v1.0 final
- 半年后如果他放弃 @nautilus 再 retry

### Case D · 14 天没回

- 不重发 · 不发第二封
- 维持 `nautilus-compass-mcp` · ship v1.0
- 6 个月后 · 看他是否仍 active · 决定要不要发 npm support

## 不要做

- ❌ 不要 cc/bcc 别人
- ❌ 不要在邮件里提 dispute
- ❌ 不要 demand · "the right thing to do" 这种话不能写
- ❌ 不要假设他在维护 · 他可能已经放弃只是没删
- ❌ 不要给截止日期

## 启动 npm support 的条件

仅当 EITHER:
- (i) Albert 14 天后没回 · 且我们之后真的需要 @nautilus (商业理由)
- (ii) Albert 回复 "我也想要这个 org 但还没机会"

```
若 (i) 或 (ii) · 才发 EMAIL_TO_NPM_SUPPORT.md (姊妹文档)。
```
