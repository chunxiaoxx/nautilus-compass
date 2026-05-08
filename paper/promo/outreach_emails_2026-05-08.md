# Outreach Emails · nautilus-compass v1.0.0 · 2026-05-08

> 8 drafts · user review + send manually · adjust personalization before sending.
> Facts to keep stable across edits: LongMemEval-S 56.6% (n=500, locked at v0.8) ·
> EverMemBench-Dynamic n=500 5-topic, two independent runs of identical pipeline:
> Run 1 = 44.4% (n=500), Run 2 = 47.3% (n=497, 3 transient API skips); both
> above MemOS 42.55, cross-run mean 45.84% (+3.29 vs MemOS) tops every reported
> Table 4 baseline · drift detector AUC 0.83 held-out, 0.92 in-set · V4-pro
> full-500 came back at 56.4% (−0.2 vs v0.8, 8× compute, shipped as
> negative-result appendix). Repo public + MIT-licensed at github.com/chunxiaoxx/nautilus-compass.

---

## 1 · Anthropic alignment team

**To:** alignment@anthropic.com · [TODO: confirm correct address — possibly `interpretability@anthropic.com` or a contact form]
**Subject:** Black-box drift detection · adjacent to Persona Vectors

Hi team,

The Persona Vectors paper (arXiv:2507.21509) showed activation-space directions
for sycophancy and hallucination — white-box, requires weights. We've shipped
a black-box prompt-text analogue that runs in a Claude Code hook, and the
results held up on real traffic, not just synthetic.

- LongMemEval-S n=500: 56.6% e2e, locked at v0.8
- Drift detector AUC 0.83 held-out (0.92 in-set), anchor design dominates
- Caught real prompt-injection prompts in production at cos=0.585+ vs negative anchor set

Would your team have 30 min for a walkthrough of the anchor schema? Specifically
how task-styled anchors moved AUC from 0.50 to 0.84 with no model change.

Repo: https://github.com/chunxiaoxx/nautilus-compass · MIT.

—chunxiao

---

## 2 · Lilian Weng

**To:** [TODO: cite specific work — confirm reachable email; lilianweng.github.io has no listed contact, may need Twitter DM or OpenAI relay]
**Subject:** Drift detection · extrinsic-hallucination adjacent

Hi Lilian,

Your "Extrinsic Hallucinations in LLMs" post (lilianweng.github.io, July 2024)
framed hallucination as a retrieval/grounding failure rather than a generation
defect. We built a black-box detector along that seam — comparing each prompt
against an anchor set of prior failure patterns — and it works in a
production hook, not just offline eval.

- AUC 0.83 held-out (0.92 in-set), 50/50 aligned/deviation prompts
- LongMemEval-S n=500 e2e: 56.6%, locked
- Real production catches: prompt-injection samples flagged at cos=0.585+

Is there prior work on prompt-text drift detection you've come across that we
should be citing? We've covered Persona Vectors and DPT-Agent; suspect we've
missed something obvious.

—chunxiao

---

## 3 · Sander Dieleman

**To:** [TODO: confirm reachable email · sander.ai has no listed contact, may need DeepMind relay or Twitter DM]
**Subject:** Anchor-based drift · feedback on §3 method

Hi Sander,

Your "Generative modelling in latent space" post on sander.ai argued the hard
work is choosing the right representation, not the right loss. Our drift
detector confirmed that empirically in an embarrassing way: random anchors
gave AUC 0.50 (coin flip), task-styled anchors gave AUC 0.84 — same model,
same scoring rule, +0.34 from anchor design alone.

- AUC 0.83 held-out (50 aligned + 50 deviation prompts)
- BGE-m3 embeddings, top-3 mean over 60 anchors, no fine-tuning
- LongMemEval-S e2e n=500: 56.6%

Would you have 10 min to look at §3 of the paper draft (anchor schema +
weighting)? The contrastive framing feels naive and I'd like to know what
we're missing before posting to arXiv.

—chunxiao

---

## 4 · Jay Alammar

**To:** [TODO: confirm email · jalammar.github.io contact form or Twitter DM]
**Subject:** Illustrated NautilusCompass? Drift detection has a clean visual

Hi Jay,

Your Illustrated Transformer made the K/Q/V projections concrete in a way
the original paper never did. Black-box drift detection has a similar gap:
the mechanism is one cosine comparison against a 60-vector anchor set, and
yet every paper I've read makes it sound like a research stack. It would
benefit from your treatment.

- Drift detector AUC 0.83 held-out, 0.92 in-set
- LongMemEval-S 56.6% n=500 (locked), EverMemBench-Dynamic 44.4-47.3% n=500 (2 independent runs, mean 45.84%, top of reported baselines)
- Anchor schema is one JSON file; the visual writes itself

Would you consider an illustrated post if we provide the diagrams, real
anchor samples, and a working repro notebook? No expectation either way.

—chunxiao

---

## 5 · Charles Frye

**To:** charles@modal.com · [TODO: confirm address]
**Subject:** MCP A2A stack · 5 min review of the protocol surface

Hi Charles,

Your Modal posts on agent infra — particularly the "agents as services, not
notebooks" framing — match what we've been wrestling with on the MCP side.
We just shipped v1.0.0 stable with the full A2A surface: stdio + TCP + TLS +
mTLS, RBAC scopes, token-bucket rate limit with `-32029 retry-in`, plus a
pure-stdlib third-party client shim (zero compass imports) so anything
speaking JSON-RPC can connect.

- 215+ pytest tests pass, 0 flake
- Examples/a2a_tls_demo.py runs full self-signed mTLS round-trip in one command
- LongMemEval-S 56.6% n=500, drift AUC 0.83 held-out

Would you have 5 min to look at the RBAC scope design (`tools.read` /
`tools.write` / `resources.read` / `*`)? Specifically whether we got
fail-closed semantics right on malformed tokens.

—chunxiao

---

## 6 · OpenAI memory team

**To:** research-relations@openai.com · [TODO: confirm address — may need to route via specific researcher]
**Subject:** Independent EverMemBench reproduction · 44.4-47.3% n=500 (2 runs)

Hi team,

We ran an independent end-to-end reproduction of EverMemBench-Dynamic
(Hu et al. 2026, arXiv:2401.13961) on the full 5-topic n=500 suite. An
open-source MIT pipeline (BGE-m3 + bge-reranker-v2-m3 + 3-angle rewrite)
landed at 44.4% (Run 1, n=500) and 47.3% (Run 2 independent rerun, n=497), both above the four reported Table 4 systems including MemOS
(42.55) by +1.85 pts.

- EverMemBench-Dynamic n=500: 44.4% (Run 1) + 47.3% (Run 2 replication, n=497); cross-topic CV ~4% within each run, cross-run delta 2.9 pts (LLM-judge variance)
- LongMemEval-S n=500: 56.6% (v0.8 locked)
- V4-pro experiment (8× compute) came back −0.2; shipped as negative result

Are you tracking EverMemBench internally? Happy to share per-question
results, the three eval-infra bugs we fixed during reproduction, and the
CSV — useful as third-party calibration regardless of how OpenAI's memory
work compares.

—chunxiao

---

## 7 · LangChain / LlamaIndex maintainers

**To:** harrison@langchain.com, jerry@llamaindex.ai · [TODO: confirm both]
**Subject:** MCP-native memory backend · 1-page integration?

Hi Harrison and Jerry,

LangChain's `BaseChatMemory` and LlamaIndex's `BaseMemory` both abstract
over a backend that has to do retrieval, summarization, and persistence.
nautilus-compass is MCP-native and already wired to Claude Desktop, Cline,
and Cursor — could plug under either abstraction as a memory backend with
drift detection bundled in.

- LongMemEval-S 56.6% n=500 (locked), EverMemBench-Dynamic 44.4-47.3% n=500 (2 runs)
- 5 slash commands: /compass-recall, /compass-search, /compass-drift, /compass-verify, /compass-status
- Local-first, MIT, no external API for retrieval (BGE on disk)

Would either of you have interest in a 1-page integration guide? I'd write
it; you tell me whether the abstraction fits or where it leaks.

—chunxiao

---

## 8 · EverMemBench paper first author (Hu et al. 2026)

**To:** [TODO: confirm corresponding-author email from arXiv:2401.13961 abstract page]
**Subject:** Independent reproduction of your benchmark · methodology check

Hi [Name],

We ran your EverMemBench-Dynamic suite end-to-end on the full 5-topic n=500
set as third-party calibration before publishing our memory system's paper.
An open-source MIT pipeline landed at 44.4% (Run 1) and 47.3% (Run 2 independent replication on the same pipeline), both above your reported MemOS
number (42.55) by +1.85 pts. We want to cite your benchmark correctly and
flag any methodology drift before we go to arXiv.

- BGE-m3 dense + bge-reranker-v2-m3, GPT-4.1-mini answerer (matching your Table 4)
- 5-topic CV 4%: 44/46/42/45/45 across topics 01–05
- Recall@30 retrieval = 97.6% (BM25 baseline 38.1%)

Did we score within your acceptable methodology — particularly the answerer
config and the topic-id mapping? Three eval-infra bugs surfaced during
reproduction (documented in our paper §6.5); flagging in case any are
upstream issues you'd want to know about.

—chunxiao

---

## Notes for the sender

- Subject lines stay under 60 chars and avoid clickbait. None use exclamation marks.
- Each body is 7–12 lines, three numeric claims max, one specific ask.
- The V4-pro negative result is mentioned in #6 (OpenAI) as the strongest signal of methodological honesty — it works there because the audience evaluates eval rigor. Omitted from #4 (Jay) and #7 (LC/LI) where it's noise.
- TODO placeholders flag every email address that needs manual confirmation. Do not send any of these without verifying the recipient's address — most public figures route through assistants, contact forms, or DMs rather than guessable addresses.
- No promises of publication, endorsement, or collaboration — every ask is bounded (5 min, 10 min, 30 min, 1-page guide, pointer to prior work).
