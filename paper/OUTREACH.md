# Outreach Email Drafts · Send T+24h after public launch

Four targeted emails. Each ≤ 150 words. No PDF attachments — link to repo + arXiv. No ask. Match the recipient's communication norms.

---

## 1 · Runjin Chen (Persona Vectors first author)

**Subject:** Black-box complement to Persona Vectors — open-sourced today

**To:** chenrunjin@utexas.edu
```
Hi Runjin,

I read your Persona Vectors paper (arXiv:2507.21509) carefully while
building a black-box analog over the past few weeks. We just open-sourced
it today as Nautilus Compass.

The core idea: at each user prompt, embed the prompt and compare to a
small set of behavioral anchor texts (positive task patterns vs negative
drift patterns), aggregated via weighted top-k cosine. ROC AUC 0.92 on
a 100-prompt synthetic test set; cross-vendor behavior A/B across 6
production LLMs (Gemini, MiniMax, Doubao, DeepSeek, GLM, judged by Kimi)
shows a statistically significant +0.07 improvement on fabrication
resistance (p<0.05, n=120). Detection layer that complements your
white-box steering layer for users without weight access.

Repo: https://github.com/chunxiaoxx/nautilus-compass
arXiv: https://arxiv.org/abs/2605.09863

No ask — just thought you'd want to see it given the topical overlap.
Happy to discuss methodology if useful.

Best,
chunxiao
```

---

## 2 · Jack Lindsey (Persona Vectors senior author, Anthropic)

**Subject:** Black-box complement to Persona Vectors

**To:** jackwlindsey@gmail.com
```
Hi Jack,

We open-sourced Nautilus Compass today — a black-box complement to your
Persona Vectors work, targeted at users who interact with closed LLMs
through APIs and can't reach activation space.

Method: cosine to anchor texts at the prompt layer, weighted top-k mean
aggregation. AUC 0.92 on synthetic test, with a four-step methodology
ablation. Cross-vendor behavior A/B (n=120 across 6 vendors, judge=Kimi)
shows significant +0.07 fabrication-axis improvement (p<0.05); destruct
axis trends nominally negative, possibly because alert text verbalizes
the matched anchor and primes the action as known-acceptable.

Honest framing throughout — the paper distinguishes detection from
steering and reports per-axis instead of just headline numbers.

Repo: https://github.com/chunxiaoxx/nautilus-compass
arXiv: https://arxiv.org/abs/2605.09863

If your team finds it useful as a benchmark or counterpoint, I'd be
delighted. No commercial pitch — MIT code, CC0 anchors.

Best,
chunxiao
```

---

## 3 · Anthropic Applied AI

**Subject:** Open-source persona drift detection for Claude users · feedback welcome

**To:** applied@anthropic.com

```
Hi Applied AI team,

I've spent two months building Nautilus Compass — a black-box persona
drift detector for production LLM agents. Built specifically because
I run Claude Code 8+ hours/day and kept hitting the same long-session
drift failures.

It ships as a Claude Code plugin (drop-in hook), an MCP stdio server,
and an HTTP gateway. ROC AUC 0.92 on a synthetic test; LongMemEval-S
P@5=0.86 on the full 500. Cross-vendor behavior A/B across 6 LLMs
(including via Anthropic-compatible proxy where available) shows a
statistically significant fabrication-resistance gain (p<0.05).

I'd love feedback in two areas:
  1. Is the alert text format we inject (cosine + matched anchor) the
     right shape, or would something more abstract steer better?
  2. The destruct-axis went nominally negative across vendors — we
     suspect the alert verbalizes the dangerous action and primes it.
     Has Anthropic's safety research seen this pattern?

Repo: https://github.com/chunxiaoxx/nautilus-compass
arXiv: https://arxiv.org/abs/2605.09863

Not asking for endorsement — just an extra pair of eyes from the people
who know Claude best.

Best,
chunxiao
```

---

## 4 · Taranjeet Singh / mem0 maintainers

**Subject:** Head-to-head numbers from your LongMemEval-S benchmark

**To:** founders@mem0.ai

```
Hey Taranjeet — chunxiao here. We just open-sourced a memory-and-drift
project that includes a head-to-head against mem0 on LongMemEval-S subset
12. Numbers below for transparency.

Setup: same dataset, same 12 questions (2 per type, balanced), mem0 with
Vertex AI text-embedding-005 and infer=False (raw session storage,
skipping LLM extraction for fair retrieval comparison).

  System                          P@1    P@5    MRR
  --------------------------------------------------
  mem0 (Vertex 005)              0.583  0.917  0.715
  nautilus-compass (bge-m3)      0.667  0.750  0.732
  nautilus-compass (m3+rerank)   0.750  0.917  0.837

P@5 ties at 0.917 with reranker. MRR is +0.122 in our favor (we suspect
because bge-reranker-v2-m3 is doing the heavy lifting; the bi-encoder
alone is comparable to mem0). Single-session-user is the type with the
biggest gap — we get MRR 0.522 vs mem0 0.250.

If the methodology has a flaw, please let me know. Full reproduction at:
https://github.com/chunxiaoxx/nautilus-compass/blob/main/tests/eval_mem0_headhead.py

Best,
chunxiao
```

---

## Sending checklist

- [ ] Verify each recipient's email address against current institutional/company page
- [ ] Replace `<handle TBD>` with actual arXiv ID once issued
- [ ] Send between Tuesday-Thursday, 10:00-12:00 recipient-local time (best open rate)
- [ ] DO NOT cc anyone · DO NOT add a tracking pixel
- [ ] Wait minimum 7 days for any reply before following up; one follow-up max, never two
- [ ] If a reply lands, reply within 24h and stay technical · zero pitching

## What to do with replies

1. **If positive technical reply** → engage on the technical content, share more data, ask their methodology in return.
2. **If "interesting, want to chat"** → propose 30-min video call, prepare 5 specific questions tailored to their work.
3. **If silent for 14 days** → that's fine. They saw it (most people read but don't reply to cold emails). Move on.
4. **Never escalate to multiple contacts at the same org** if the first didn't reply. That signals desperation.
