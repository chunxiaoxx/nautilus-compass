---
name: drift_summary
status: codified
version: 1.0.0
tier: episodic
description: Summarize last 7 days of compass drift events · alert distribution + top 5 negative drifts · pure read-only · NO LLM.
inputs:
  - lookback_days (int, default 7): days back to scan
  - drift_log_path (path, optional): override default .cache/drift_history.jsonl
outputs:
  - total_events
  - alert_counts (by level: green/yellow/red)
  - top_negative_drifts (list of {score, prompt_excerpt, ts})
  - first_seen_ts
  - last_seen_ts
---

# drift_summary

Read `~/.claude/plugins/nautilus-compass/.cache/drift_history.jsonl` (or
override path) and aggregate the last N days of drift events.

## When to use

- Weekly review: "where am I drifting recently?"
- Pre-ship audit: "any red alerts in the last 24h?"
- Anchor reset: "what's the top neg-hit signal across recent prompts?"

## Why codified (not prototype)

- 7+ runs over multiple weeks (5/04, 5/12, 5/17 etc · 每次 user 问 drift 摘要)
- Pure read-only · no side effects · cannot regress
- Deterministic output schema · easy to assert in smoke tests
