# Product Hunt Launch Draft — nautilus-compass

> Draft only — **do not launch without user review**. Paste fields into https://www.producthunt.com/posts/new

## Core fields

**Name**: nautilus-compass

**Tagline (≤ 60 chars)**: Stop your AI from repeating mistakes you already flagged

**URL**: https://compass.nautilus.social

**Topics / categories**: Developer Tools · Artificial Intelligence · Open Source · Productivity

## Description (≤ 260 chars)

Memory layer with drift detection for Claude Code, Cursor, Cline, Continue.dev, Zed. Recalls past memory **and** flags when the AI is about to repeat a known mistake. LongMemEval-S 56.6%, drift AUC 0.83, <50ms p95. MIT, ~$3.50 to reproduce.

## First comment (maker reply)

Hey PH 👋

I'm Chunxiao, the maker. nautilus-compass started after I watched Claude tell me deployed successfully ✅ 50 prompts after I had told it never to claim deployment success without verification. Recall worked — the rule was in memory. But the AI still drifted under context pressure.

Mem0, Letta, claude-mem, Zep all compete on **recalling the most relevant past memory**. compass adds the second half: **detect when the AI is about to repeat a known mistake** and remind it of what worked last time.

How: each prompt is scored against 25 positive + 35 negative behavioral anchors using BGE-m3 cosine. Held-out drift AUC 0.83. Runs in a Claude Code hook in <50ms p95.

Numbers (linked in README):
- LongMemEval-S 56.6% (ties Zep SOTA band; +12 pts vs Gemini-2.5-pro baseline)
- EverMemBench-Dynamic 44.4–47.3% (tops Mem0 / Zep / MemOS in published Table 4)
- Reproduction cost ~$3.50 for 500 questions (under 1/15 of GPT-4o-judged stacks)

MIT licensed. 7 MCP tools, TLS + RBAC, A2A bridge for cross-agent memory sharing.

Try without installing → live demo: https://compass.nautilus.social
HF Space: https://huggingface.co/spaces/chunxiaox/nautilus-compass
GitHub: https://github.com/chunxiaoxx/nautilus-compass

Honest AMA — happy to talk about black-box drift detection, the EverMemBench dual-run methodology, why MCP not REST, or anything else.

## Gallery assets needed before launch

| asset | path | status |
|---|---|---|
| logo (240×240) | landing/static/og-image.png | exists in repo |
| hero gif (4–8s, drift detection in action) | TODO — record a Claude Code session catching a regression | needs recording |
| benchmark screenshot | paper/RESULTS_v0.8.md table | needs capture |
| architecture diagram | README #how-it-works | needs PNG export |

## Pre-launch checklist (do not launch until all green)

- [ ] User has reviewed this draft and edited tagline / first comment if desired
- [ ] All 4 gallery assets prepared
- [ ] Picked a launch day (best: Tuesday or Wednesday, 12:01 AM PST)
- [ ] 5-10 hunters / supporters lined up (NOT spam — real users only)
- [ ] HN / Twitter / dev.to cross-post drafts ready (already in marketing/)
- [ ] On-call to reply to comments first 6 hours

## Hunter outreach (separate from this draft)

Best PH hunters for AI dev tools (research before pinging):
- @kevin (Kevin William David) — top AI hunter, but very selective
- @rrhoover (Ryan Hoover) — founder, only for big launches
- @chrismessina — open-source friendly

We will NOT cold-DM hunters. We earn the launch by shipping the email outreach in Task B and letting Simon Willison / swyx organically pick it up.
