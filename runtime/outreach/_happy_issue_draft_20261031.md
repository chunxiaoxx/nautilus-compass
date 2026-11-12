# happy issue 英文稿(候发)· 目标仓库:slopus/happy · 2026-10-31

> 使用:以 GitHub 账号在 slopus/happy 开 issue,标题+正文照贴;数据均实测,推测段已标注。

---

**Title:** Remote sessions: compact threshold collapses to ~65k tokens and loops every few minutes on third-party models (glm-5.3[1m]) — desktop CLI unaffected

**Labels suggestion:** bug, remote-session

## Environment

- happy CLI: **1.2.5** (macOS, Apple Silicon; installed via happy's own installer — note: npm `happy-coder` latest is 1.1.9, so 1.2.x seems to ship outside the npm latest channel)
- Control machine: Windows 11, happy **1.2.0** (same relay, same model)
- Underlying agent: Claude Code native 2.1.299, model `glm-5.3[1m]` via a third-party Anthropic-compatible relay
- Session entrypoint: `remote_mobile` (session started/managed from phone)

## Symptom

Every long-running **remote** session enters an auto-compact death loop:

1. First compact fires when the context is genuinely full (~317k tokens)
2. **After that first compact, the effective compact threshold collapses to ~65k tokens** and stays there
3. The session then re-compacts every 3–10 minutes indefinitely, at 61–76k tokens each time — the context "refills to the limit within 3 turns" after every compact

Desktop sessions on the same machine, same model, same relay (`entrypoint: cli`) do **not** show this behavior.

## Data (single worst session, 15 MB transcript)

34 compact events, chronological (UTC):

```
2026-10-31T07:00:56Z  compact #1  @ ~317,646 tokens   ← genuinely full
2026-10-31T07:04:54Z  compact #2  @ ~66,719 tokens   ← threshold collapses, 4 min later
2026-10-31T07:06:45Z  compact #3  @ ~61,126
2026-10-31T07:09:20Z  compact #4  @ ~70,390
... (30 more) ...
2026-10-31T10:35:56Z  compact #34 @ ~67,628
```

Aggregate across recent sessions on this machine:

| Entrypoint | Sessions | With ≥3 compacts (thrashing) |
|---|---|---|
| `remote_mobile` | 3 | **3 (100%)** |
| `cli` | 9 | 1 (mild, different cause) |

Cross-machine control: Windows box, happy **1.2.0**, same relay, same model, same `remote_mobile` entrypoint — **142 remote sessions, 1 thrashing (0.7%)**.

## What we ruled out

- The relay's per-request `usage` is well-formed (`input_tokens`/`cache_read_input_tokens` accurate on spot checks) — server-side token accounting looks sane
- Hook injections are small (~2.6 KB) — not an injection-size problem
- Desktop Claude Code 2.1.299 with the same model resumes and runs long sessions fine

## Working hypothesis [inferred, not confirmed]

The remote-session runtime estimates context size for models it doesn't recognize (third-party `glm-5.3[1m]`) instead of using the model's real context window, and **over-estimates for CJK-heavy content by ~3×**. After the first real compact, the post-compact context (~60k real tokens, mostly Chinese) is estimated as near-limit, so compact fires again immediately — and the loop never exits. This would explain:

- why the loop threshold sits at a flat ~65k regardless of the model's actual window
- why CJK-heavy sessions are the worst affected
- why desktop `cli` sessions (different code path) are unaffected
- why happy 1.2.0 (Windows) mostly avoids it

## Expected behavior

Compact threshold for remote sessions should be derived from the model's actual context window (or an explicit per-model config), not a collapsed fallback estimate — and should not re-fire minutes after a compact.

## Workarounds we use meanwhile

- Run long sessions in desktop CLI; keep phone/remote for light interaction only
- Abandon looped sessions and restart fresh (post-compact sessions never recover)

Happy to provide the full 15 MB transcript (redacted) or any additional telemetry.

---

*文件坐标:runtime/outreach/_happy_issue_draft_20261031.md(仓外发前留档)*
