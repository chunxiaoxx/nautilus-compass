---
title: nautilus-compass demo
emoji: 🧭
colorFrom: blue
colorTo: purple
sdk: static
app_file: index.html
pinned: false
license: mit
---

# nautilus-compass · drift detector live demo

Static, in-browser demo for [`nautilus-compass`](https://github.com/chunxiaoxx/nautilus-compass)
v1.0 · the persona-drift detector + tamper-evident memory log for
long-running LLM agents.

## What you can try here

**Drift detection.** Paste a `(system_prompt, response)` pair. We
char-n-gram both and score the response against the **25 positive +
35 negative** persona anchors shipped with nautilus-compass.

- **Green** = response sits inside the persona anchor cone (aligned)
- **Yellow** = neutral, weak signal either way
- **Red** = response is closer to the *negative* anchors (sycophancy,
  fake-completion, root-cause skipping, "user won't notice", etc.)

The verdict + alignment / deviation / drift_score breakdown render
instantly. All scoring runs **client-side in your browser** — no upload,
no tracking, no API key needed.

Two pre-baked sample buttons load (clean) and (drifted) cases from the
same fixtures the unit tests use, so you can sanity-check the verdict
matches what nautilus-compass ships.

## What needs the local install

The full pipeline used in the paper (BGE-m3 dense + bge-reranker-v2-m3
cross-encoder, ~570M params, ~2GB model weights) doesn't fit a free
Space and isn't this demo's point. Same for Merkle hash chain
verification — it needs filesystem access to your `~/.claude/projects/`
session logs.

For the full stack:

```bash
pip install nautilus-compass==1.0.0
bash daemon_start.sh        # one-time per boot · downloads BGE-m3 ~2GB
compass-verify --all        # Merkle integrity scan
```

Or in any of 6 MCP-compatible clients (Claude Code · Claude Desktop ·
Cline · Cursor · Continue.dev · Zed) — see
[`examples/mcp_configs/`](https://github.com/chunxiaoxx/nautilus-compass/tree/main/examples/mcp_configs)
in the repo for paste-ready configs.

## Headline eval numbers (locked v1.0 · 2026-05-08)

| metric | nautilus-compass | best public baseline |
|---|---|---|
| LongMemEval-S (n=500) | **56.6%** | Zep 55-60% (different judge) |
| EverMemBench-Dynamic Run 1 | **44.4%** (n=500) | MemOS 42.55 |
| EverMemBench-Dynamic Run 2 | **47.3%** (n=497) | — |
| Drift detector ROC AUC (held-out) | **0.83** | — (no other black-box drift work) |
| Reproduction cost | **$3.50** end-to-end | $50+ for GPT-4o-judge stacks |

Two papers on arxiv (drift detection · memory recall). 228 pytests
all green. MIT (anchors CC0).

## Local repo

[github.com/chunxiaoxx/nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass)
