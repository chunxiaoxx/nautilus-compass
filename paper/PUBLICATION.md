# Publication Plan · Nautilus Compass

Single-page tracker for the public launch: arXiv preprint + GitHub release + HN front-page attempt + Twitter thread + targeted outreach. Order matters; timing matters more.

---

## Pre-launch checklist (do all before submitting anywhere)

- [ ] Paper compiles cleanly under `paper/nautilus-compass.tex` via Overleaf or local `latexmk -pdf`
- [ ] All 5 figures render (architecture, AUC evolution, LongMemEval per-type, drift histogram, rerank lift)
- [ ] All 6 `paper/results/behavior_ab_*.json` are committed and reproducible from the repo
- [ ] `RESULTS.md` table matches paper §4 numbers (MRR / P@5 / drift AUC) line-by-line
- [ ] `README.md` 30-second pitch · 3-minute demo · 30-minute custom anchors ladder
- [ ] `MCP_INSTALL.md` and `examples/nautilus_integration.md` link from README
- [ ] CI green on Linux + macOS (Python 3.10 / 3.12)
- [ ] Tagged release: v0.7.2

---

## arXiv

- Submit category: **cs.CL (primary)**, cross-listed cs.SE
- Title: *Nautilus Compass: Black-box Persona Drift Detection for Production LLM Agents*
- Abstract: see `paper/sections/00_abstract.tex` · 280-word draft
- License: arXiv non-exclusive (we keep MIT on code, CC0 on anchors)
- Cite handle: `arXiv:25xx.xxxxx` · backfill into README + paper bibitems once issued

---

## GitHub release

`v0.7.2` annotated tag with these notes:

```
Nautilus Compass v0.7.2 · 2026-04-30

First public release. Open-source black-box persona drift detection for
production LLM agents · plus a high-recall semantic memory layer.

Headline numbers (reproducible from repo):
- Drift detection ROC AUC = 0.9232 on 100-prompt synthetic test set
- LongMemEval-S full 500: P@5 = 0.860 · MRR = 0.685 (bge-m3, no rerank)
- mem0 head-to-head subset 12: P@5 tied at 0.917 · we win MRR by +0.122
- Cross-vendor behavior steering A/B (n=120 prompts × 6 LLM vendors):
  fabricate-axis Δ = +0.071, paired t = +2.21, p < 0.05

What ships:
- Claude Code plugin (drop-in hook)
- MCP server (stdio · works with Cursor / Cline / Hermes / OpenClaw)
- HTTP gateway (REST + MCP-over-HTTP · multi-tenant · API key auth · rate limit)
- Docker compose (single-host · 4 GiB RAM)
- k8s manifests (StatefulSet daemon + autoscaling Deployment gateway)
- 5 reference anchor profiles (general / legal / medical / finance / VC)

Paper: arXiv:<TBD>
GitHub: https://github.com/chunxiaoxx/nautilus-compass
Docs: README.md · MCP_INSTALL.md · examples/nautilus_integration.md · ops/k8s/README.md
```

---

## Hacker News

Submit as `Show HN: Nautilus Compass — Black-box persona drift detection for LLM agents` linked to the GitHub repo (NOT the arXiv PDF — HN heavily prefers code links for Show HN).

Optimal slot: **Tuesday or Wednesday, 8:00–10:00 AM Pacific**. Avoid Mondays (carryover noise) and Fridays (low engagement). Don't submit during a US holiday or major conference week (NeurIPS / ICML).

First-comment pre-write (post immediately after submission to anchor the discussion):

```
Author here. Quick context on what's going on:

Persona Vectors (Anthropic, arXiv:2507.21509) showed that LLMs have linear
trait directions in activation space — sycophancy, hallucination, etc. — that
you can measure and steer if you have model weights. Most of us don't. This
project is the black-box equivalent: at each user prompt, we embed the prompt
and compare cosine similarity to two small anchor sets (positive task patterns
and negative drift patterns), score the difference, and decide whether to
inject a warning into the model's context.

The interesting empirical results are:
1. ROC AUC 0.92 for detection on a 100-prompt synthetic test set, with a
   four-step ablation table that shows where the gains came from
   (mostly: rewriting abstract maxim anchors as task-shaped sentences).
2. P@5 = 0.86 on LongMemEval-S full 500 with bge-m3 alone, tied with mem0 on
   subset 12 head-to-head.
3. Cross-vendor behavior A/B across 6 production LLMs (Gemini Pro/Flash, MiniMax,
   Doubao, DeepSeek, GLM) with Kimi as judge: fabrication-resistance improves
   significantly (p < 0.05, n=120). Verify and secret are flat. Destruct
   trends NEGATIVE — we think the alert text mentioning "rm -rf" might be
   priming the model to treat it as known-acceptable.

The paper (and the README) is honest about what the numbers do and don't
support. Detection ≠ behavior steering, and a +0.07 fabricate-axis effect is
"real, modest, and axis-specific" rather than "drift injection makes Claude safe."

Ships as a Claude Code plugin, an MCP server (so it works in Cursor / Cline /
Hermes / OpenClaw / etc.), a REST gateway with multi-tenant auth and rate
limiting, Docker compose, and k8s manifests. MIT, anchors CC0.

Happy to answer specific questions on (a) why the destruct axis went negative,
(b) why we use BGE-m3 over OpenAI embeddings, or (c) how the daemon's
multi-profile cache is structured.
```

---

## Twitter / X thread

Lead with a single visceral claim, supported by one number, then the punchline question. Ten tweets, the first three matter most.

```
1/ Persona drift in long-running LLM agents is the failure mode nobody owns.
   Open-sourced our fix today. Black-box. CPU. MIT-licensed.
   github.com/chunxiaoxx/nautilus-compass

2/ Quick demo: when the user types "ignore previous instructions", we score
   the prompt against 25 task-shaped + 35 drift-pattern anchor texts.
   Result: drift_score = -0.042, alert = True. ~200 ms warm.

3/ Detection numbers. ROC AUC = 0.9232 on a 100-prompt aligned/deviation
   synthetic test set. Four-step ablation walks through how we got there
   from random (0.5056). Largest single jump: writing anchors as TASK
   SHAPES, not maxims.

4/ Retrieval numbers (bge-m3 alone, no reranker): P@5 = 0.860 · MRR = 0.685
   on LongMemEval-S full 500. Tied with mem0 on subset 12 head-to-head.
   Zero LLM API cost — runs on a $5/mo VPS.

5/ Honest part: Detection ≠ steering. So we ran a cross-vendor A/B across
   6 LLMs (Gemini Pro/Flash, MiniMax M2.7, Doubao Seed 2.0, DeepSeek v3.2,
   GLM-5.1) with Kimi-k2.6 as judge, n=120 paired prompts.

6/ Fabrication resistance: Δ = +0.071, paired t = +2.21, p < 0.05.
   Significant. Drift injection genuinely makes models push back against
   fabricated prior agreements.

7/ Destructive-action axis: Δ = -0.027 (n.s., trending NEGATIVE).
   Hypothesis: alert text verbalizing "rm -rf this directory" makes the
   action salient as something the system already knows about, reducing
   refusal. Working on rewording.

8/ Ships 4 ways: Claude Code plugin · MCP stdio server · MCP-over-HTTP +
   REST gateway with tenant auth · Docker compose & k8s. Same daemon
   backs all four. No LLM API key required for the embedder.

9/ The paper goes into the four-step ablation, train-test contamination
   mitigation, and the cross-encoder-rerank null result we publish to
   save practitioners the implementation.

10/ MIT code · CC0 anchors · arXiv preprint TBD.
    Repo: github.com/chunxiaoxx/nautilus-compass
    If you're shipping coding agents and you've felt this drift problem,
    please try it and tell me where it breaks.
```

---

## Targeted outreach (after launch lands)

After the HN/Twitter dust settles (give it 48 h), send short emails to:

1. **Runjin Chen** (Persona Vectors first author). Subject: "Black-box complement to your persona vectors work". Two-line abstract + paper link + repo link. No ask.
2. **Jack Lindsey** (Persona Vectors senior author). Same pattern.
3. **Anthropic Applied AI** (`applied@anthropic.com`). Two paragraphs: what we built, where we'd love feedback, no commercial pitch.
4. **mem0 team** (Taranjeet Singh, GitHub). "Head-to-head numbers from your benchmark — happy to chat about methodology if interesting."

Each email is under 150 words. Include the one-line headline number and the repo link. Don't attach PDFs.

---

## Definition of "successful launch"

Set the bar concretely so the team agrees on what is and isn't success:

- **Floor**: 50 GitHub stars in week 1, no embarrassing methodological errors discovered, no security issue filed.
- **Mid**: 200 stars in week 1, on HN front page > 4 hours, ≥ 3 substantive technical comments addressed publicly, one of the targeted authors replies.
- **Stretch**: Mentioned in a survey paper or industrial blog within 3 months. Cited at next major venue (ACL/EMNLP/NeurIPS/ICLR).

We do NOT optimize for raw star count. We optimize for: (a) people running the smoke test successfully, (b) substantive technical pushback we can learn from, and (c) one production deployment that isn't us.

---

## Day-of timeline (rough)

| Time (PT)     | Action |
|---------------|--------|
| T-1 day       | arXiv abstract submitted (gives 24-h moderation window) |
| T-1 day       | GitHub release tagged · README final pass |
| T 08:00       | HN Show HN submission |
| T 08:05       | HN first comment posted (anchor the discussion) |
| T 08:30       | Twitter thread |
| T+0 to T+12   | Author monitors HN; responds to every top-level comment within 30 min |
| T+24h         | Outreach emails sent (Persona Vectors · mem0 · Anthropic) |
| T+48h         | Retro write-up: what worked / what didn't / lessons for v0.8 launch |

---

## Things we will NOT do at launch

- Compare ourselves favorably to mem0 unless the comparison is apples-to-apples (we win on subset-12 MRR, we tie on P@5; we don't claim "we beat mem0").
- Imply detection AUC implies behavior steering.
- Use "SOTA" or "state of the art" without the qualifier "open-source · black-box · for the agent runtime use case".
- Promise behaviors we haven't measured (e.g., "improves Claude's safety in production").
- Hide the negative findings (destruct axis trending negative, glm-5.1 + gemini-flash net negative).

The paper is honest. The launch must be too.
