# Outbound: ZenMind release readiness + Compass 2.3 borrow points

thread_id: platform_soul_to_compass_release_readiness_20260721
thread_role: outbound
from: platform-soul / codex
to: compass
created_at: 2026-07-21T01:45:00-04:00

## Why this is sent

The user explicitly asked that Compass-related findings be synchronized through the existing cross-dialog mechanism instead of manual copy/paste.

## Current ZenMind app release state

Fresh EAS evidence from `C:\Users\chunx\quantum-buddha-project`:

- Android domestic: build `05b4e72c-2585-4beb-93aa-c7c5047a1cc9`, `FINISHED`, AAB, `production`, app `4.23.12`, build `132`, completed `2026-07-18T17:11:06Z`.
- Android international: clean `production-intl` candidate is `206b9871-d038-4d42-a2b6-633ac0ae8cbd`, `FINISHED`, AAB, app `4.1.22`, build `131`, runtime `1.1.0`, completed `2026-06-23T18:12:34Z`.
- Warning: newer Android build `af395180-01d6-4530-b8a7-b4e640c5c37f` finished on `2026-07-18`, but it is `buildProfile=production`, `channel=production`, runtime `1.0.0`, while app version is `4.1.22`; do not treat it as a clean intl artifact without investigation.
- iOS international: build `9d6aeca5-7a3c-4233-a2fa-86296055332e`, `FINISHED`, IPA, `production-intl`, app `4.1.22`, build `2`, runtime `1.1.0`, completed `2026-06-24T16:27:02Z`.
- iOS domestic: no separate domestic iOS build/profile evidence found.

Live endpoint checks:

- `https://i.chunxiao.wang/api/health` returned 200.
- `https://zenmind.chat/privacy` returned 200.
- `https://i.chunxiao.wang/privacy.html` returned 200.
- `https://zenmind.chat/api/health` timed out after 15s.
- `https://zenmind.chat/api/trpc` returned 404.

Decision: proceed with internal track/TestFlight/store-review preparation, but do not claim public launch readiness until domestic API, store submission state, privacy consent, and real-device smoke pass.

## Model routing

- Domestic should use DeepSeek V4 Flash for the streaming path. Local code already defaults `callDeepSeekStream` to `deepseek-v4-flash`; production must set `DEEPSEEK_API_KEY` and `DOMESTIC_NO_GOOGLE=1`.
- International should move text/chat env from `gemini-2.5-flash` to `gemini-3.5-flash` and validate. Gemini 3.5 Flash is GA per Google docs; 2.5 Flash has a 2026 shutdown path.
- MiniMax remains useful as fallback. Non-stream `chat()` is still MiniMax-first, so DeepSeek-first everywhere requires code change.

## Compass 2.3 borrow points for ZenMind

- Semantic memory capsule quality gates: promote high-confidence user memories, reject weak/unsafe memories, tombstone bad memories.
- OKF-like export/validation: user memory export/delete and spirit reports need auditable structure, not just prose.
- GEP quality selection: approved reflections and lessons should feed future prompts; rejected ones should never silently re-enter.
- Durable transport: voice/chat should adopt event ids, resume, replay, no-gap tests, and watchdogs, matching Compass MCP durable lessons.
- Release capsule: build id, channel, runtime, backend endpoint, legal status, smoke result, and store state should be a single record.

## Files written by Codex

- `C:\Users\chunx\quantum-buddha-project\docs\release-readiness-2026-07-21.md`
- This outbound file.

