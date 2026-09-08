# Reproducibility Wall

> Independent reproduction beats self-report. Everything below was produced by
> someone who ran the head-to-head themselves. Numbers go on the wall
> **as reported — favorable or not.**

## How to get on the wall

1. Run the head-to-head protocol — ours lives in [`docs/evidence/`](evidence/)
   (scripts, run logs, judge outputs). The full 500-question LongMemEval-S
   retrieval comparison costs **~$3.50** in API calls.
2. Open a PR or issue titled `Wall entry: <your-handle>` with:
   - your numbers (any of: P@1 / P@5 / MRR / e2e)
   - scope — full 500 or an explicitly labeled subset
   - environment (OS, embedder + versions, mem0 version, judge)
   - a link to your logs (repo, gist, anything public)
3. We publish it unedited (formatting only).

## The wall

| Date | Who | Scope | compass P@1 | mem0 P@1 | Environment | Logs |
|---|---|---|---|---|---|---|
| 2026-09-08 | @chunxiaoxx (self-reported — which is exactly why this wall exists) | LongMemEval-S · full 500 | **0.890** | 0.774 (mem0 2.0.19) | BGE-m3 vs text-embedding-005, each on defaults, our harness | [docs/evidence/](evidence/) |
| — | *row 2 is yours* | | | | | |

## Rules

- No cherry-picking from us: entries that **contradict** our numbers are
  published with the same prominence.
- Subsets are welcome but must be labeled as subsets.
- Found a protocol flaw? It gets fixed and re-run, not buried.

*Related: the judge-hygiene paper (LLM-as-judge failure taxonomy + protocol,
arXiv in submission) and the dual-accounting e2e report in the README.*
