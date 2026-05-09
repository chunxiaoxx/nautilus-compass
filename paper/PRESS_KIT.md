# Compass · Press Kit

> For journalists · podcast hosts · investors · technical reviewers.
> Compass v0.9.0-dev · 2026-05-05

## One-liner

```
Compass is a cross-agent memory layer for AI assistants — your Claude
Desktop · Cursor · Cline · OpenClaw · Hermes all share the same memory of
who you are and what you've been doing. Open-source · MIT licensed ·
runs locally · costs ¥10 per benchmark run vs ¥150 for commercial alternatives.
```

## Headline metrics (for charts / infographics)

```
56.6%   LongMemEval-S accuracy (n=500 · paper SOTA tier)
0.92    Drift detection AUC (anchor-based · 50ms p95)
1/15    Cost vs Gemini-2.5-pro / GPT-4o pipeline ($3.50 vs $50 per run)
+27 pts Single-session-user gain from multi-angle query rewriting
234 MB  Disk freed by replacing claude-mem with compass writer
7       MCP tools (Claude Desktop · Cline · Cursor compatible)
4       A2A protocol capabilities (Nautilus a2a-registry compatible)
3       Regions planned (cn-shanghai · eu-frankfurt · us-virginia)
8       Deep fusion points with Nautilus platform
```

## Story angles

### Angle 1: "China's open-source memory beats Silicon Valley"

> Compass v0.8, an MIT-licensed open-source memory pipeline built by a
> Chinese developer, achieves the same accuracy band as Zep (Silicon
> Valley · venture-funded · $$$) on the public LongMemEval-S benchmark,
> at 1/15 the cost. Built entirely on Chinese open-via-API LLMs (DeepSeek,
> GLM, Kimi, MiniMax) via the Volc Ark coding plan, with all components
> reproducible in $3.50 USD on a Tencent Cloud T4 spot instance.

### Angle 2: "Why MiniMax thinking-mode breaks at scale (a paper-grade negative finding)"

> When MiniMax M2.7-highspeed runs LongMemEval-S with default thinking-1024
> budget, the refusal rate explodes from 17% (sample 50) to 44% (full 500),
> collapsing accuracy to 33%. We document this as the strongest case of
> thinking-mode causing systematic failure in the literature. Production
> deployments must benchmark per-model thinking-on/off; don't assume thinking
> always helps.

### Angle 3: "The 'iCloud-memory' for AI agents"

> Compass v1.0 (target: May 2027) will be to AI agents what iCloud is to
> Apple devices: the cross-device, cross-app memory layer that makes
> "your AI assistant" actually feel like a singular thing rather than 5
> different chat windows. Federated across Claude, Cursor, Cline, OpenClaw,
> and any MCP/A2A-compatible client.

### Angle 4: "Drift detection · the missing safety layer"

> Compass embeds an anchor-based drift detector (AUC=0.92, 50ms hook) that
> catches when an AI deviates from user intent — claiming "done" without
> verifying, repeating failed approaches, fabricating context. claude-mem
> doesn't do this. Mem0/Letta/Zep don't do this. Anthropic's Persona Vectors
> paper proves the white-box version works; Compass ships the production
> black-box version anyone can run.

## Quotable snippets

> "If you only train AI on what's in its context window, you're like the
> guy in Memento — every session starts from zero. Compass gives the
> AI a way to know it's repeating a mistake from last Tuesday."

> "We don't replace Mem0 or Zep. We compete on a different axis. They
> ask 'how good is your retrieval?' We ask 'how does your AI know it's
> drifting?'"

> "The MiniMax thinking-1024 refusal cascade is the kind of bug that
> only shows up at n=500 · sample 50 looks fine, full run dies. Negative
> findings like this are exactly what makes papers reproducible."

> "Cross-agent memory federation isn't a feature. It's the precondition
> for AI agents to feel like one thing. Without it, you have 5 amnesiac
> assistants pretending to know you."

## Key documents (links)

- [README.md](https://github.com/chunxiaoxx/nautilus-compass/blob/main/README.md) ·
  product overview · install · cross-agent demo · 8 fusion points
- [paper/RESULTS_v0.8.md](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/RESULTS_v0.8.md) ·
  per-question-type accuracy · trajectory · negative findings
- [paper/V10_FINAL_SPEC.md](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/V10_FINAL_SPEC.md) ·
  v1.0 final spec (17 sections)
- [BENCHMARKS_REPRODUCE.md](https://github.com/chunxiaoxx/nautilus-compass/blob/main/BENCHMARKS_REPRODUCE.md) ·
  $3.50 reproduction guide
- [paper/BLOGPOST.md](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/BLOGPOST.md) ·
  release announcement (1500 word)
- [paper/sections/](https://github.com/chunxiaoxx/nautilus-compass/blob/main/paper/sections/) ·
  paper 2 LaTeX (8 sections + 1 appendix · pdflatex ready)

## Numbers verifiable via:

```
.cache/longmemeval_acc_m3_rerank_full_1777975609.jsonl       # per-question logs
.cache/longmemeval_acc_m3_rerank_full_1777975609_summary.json # aggregate
T4 server (43.173.164.32) · contact for replication ssh
```

## Domain experts ready to comment

- **chunxiaoxx (primary author)** · email and Twitter on request
- (Future invitees: domain anchor pack contributors as the project grows)

## Visual assets (TikZ → PNG when rendered)

- `paper/figures/pipeline_v08.tex` · 5-stage retrieval pipeline diagram
- `paper/figures/trajectory_v08.tex` · cumulative accuracy V-shape
- `paper/figures/fusion_diagram.tex` · 8 platform fusion points map

These render to PDF/PNG via `pdflatex` or `tectonic` (see `paper/figures/README.md`).

## Logo / branding

**Name**: nautilus-compass (lowercase preferred · stylized "Compass")
**Tagline**: "Cross-agent memory · drift-aware · 56.6% on LongMemEval-S"
**Brand colors**: blue (Nautilus) #1d6cf3 · orange (drift warn) #e94e1b · green (drift OK) #10a960
**Logo**: pending v0.9.0 release · we have a placeholder geometric icon

## Common journalist FAQ

**Q: Is this a memory replacement for Claude Code's built-in memory?**
A: It runs alongside Claude Code via hooks. Claude Code's CLAUDE.md
files remain primary; compass adds cross-session, cross-agent semantic
recall + drift detection on top.

**Q: What's the catch with the cost claim?**
A: The Volc Ark coding plan is unusually generous (effectively flat-rate
multi-model access). If the rate structure changes, our cost claim
degrades by 5-15×. We mitigate by maintaining provider-neutral SDK code.

**Q: Privacy?**
A: v0.8 stores plaintext locally; v1.0 (May 2027 target) ships E2EE
default with libsodium client-side. The hosted SaaS at
compass.nautilus.social is opt-in; everything works without it.

**Q: Why China-region focus?**
A: PIPL compliance is non-trivial. Hosting in mainland China requires
specific data-residency commitments. We architect for regional sharding
(cn / eu / us) so each user's data stays in their jurisdiction.

**Q: What's Nautilus platform?**
A: A 7-capability suite for AI agents (memory · identity · agent
runtime · marketplace · stake economy · A2A · MCP). Compass is one
component. Platform is in private alpha; component is open-source MIT.

**Q: Are you raising money?**
A: We don't comment on this in press kit. Reach out via email if interested.

## Embargo / press contacts

- All inquiries (general / security / press / interviews): chunxiaoxx@gmail.com
