# ICLR 2026 Workshop on LLM Memory · Submission Plan

> **Companion / source paper**: `paper/paper2_main.tex` · 27 pages · LongMemEval-S 56.6% + EverMemBench-Dynamic 44.4% + 6-LLM thinking-mode benchmark + Neo4j graph rerank negative finding.
> **Audit anchor**: `paper/PAPER2_ARXIV_READINESS_2026-05-07.md` (3 P0 blockers · ~2 h to fix · arXiv submission planned 2026-05-12 to 2026-05-14).
> **Status of this document**: Plan only · NO submission performed · all venue facts marked `[TODO]` are awaiting human verification.

---

## CFP recon

> **Honest finding** (2026-05-07): I have **no offline-verifiable evidence** that an "ICLR 2026 Workshop on LLM Memory" has been formally announced under that exact name. The reference in `paper/OUTLINE_PAPER2.md:6` ("Target: ICLR 2026 Workshop on LLM Memory · or arXiv preprint") and in `PAPER2_ARXIV_READINESS_2026-05-07.md:89` ("CFP not re-verified — confirm before workshop submission") are both internal aspirations, not citations. The agent that wrote those lines did not link to an OpenReview venue page or an iclr.cc workshops page. Treat the workshop's existence as an unverified hypothesis until a human confirms via OpenReview.net or iclr.cc/Conferences/2026/Workshops.

| Field | Value |
|---|---|
| Workshop name | `[TODO verify]` · candidate names: "Workshop on LLM Memory" / "Workshop on Memory in Foundation Models" / "Workshop on Long-Context and Memory" / "MemBench Workshop". Search OpenReview for `venue:ICLR.cc/2026/Workshop` once page is live. |
| Workshop URL | `[TODO]` · expected pattern: `https://iclr.cc/Conferences/2026/Workshops` (workshops list) or `https://openreview.net/group?id=ICLR.cc/2026/Workshop/<short-name>` |
| Submission deadline | `[TODO]` · ICLR 2026 main conference is in Vienna · ICLR 2026 main paper deadline was 2025-09-24 with notification 2026-01-22 · workshop CFPs typically open Dec-Jan and close **Feb-March 2026**. As of 2026-05-07, most workshop deadlines have **already passed**. This is a serious risk to the timeline; see "Risk assessment" below. |
| Workshop date | `[TODO]` · ICLR 2026 conference dates `[TODO confirm via iclr.cc]` · workshop day is typically the last day of the main conference. |
| Page limit | `[TODO]` · ICLR workshop standard is **4-page short** (typical) or **8-page extended**, both excluding references. Some memory-themed workshops accept up to **9 pages** (NeurIPS-style). Assume 4-page short until verified. |
| Format | `[TODO]` · ICLR uses `iclr2026_conference.sty` for main · most workshops use the same template with a `\workshoptrue` flag or a workshop-specific class. Some workshops adopt OpenReview's generic `template.zip`. |
| Anonymous? | `[TODO]` · ICLR workshops are split: roughly half are double-blind, half are single-blind or non-archival. Memory/long-context workshops in 2024 and 2025 trended **double-blind**. Assume **double-blind** until proven otherwise. |
| Archival? | `[TODO]` · non-archival workshops allow concurrent arXiv + journal submissions; archival ones may not. Critical for the TMLR plan. |
| Reviewer pool size | `[TODO]` · workshops typically get 2 reviewers per submission vs main track's 4. |
| Submission portal | `[TODO]` · expected OpenReview, but venue ID won't exist until CFP is posted. |

**Action**: One human-driven 15-min web search at `iclr.cc/Conferences/2026/Workshops` and `openreview.net` (search for "memory" or "long-context" venues with `ICLR.cc/2026/...`) will resolve every `[TODO]` above. Until then, this entire submission package is hypothetical.

---

## Submission strategy

### High-level

We submit a **SHORT** version of paper 2, **not** the 27-page arXiv version. The workshop wants the punchline + 1–2 figures, not the appendix-heavy story. Target length: **4 or 8 pages** depending on `[TODO page limit]`.

The paper2 27-page → workshop 8-page (or 4-page) shortening is feasible and is, in fact, a better paper at workshop length. See "Strongest argument for SHORTENING" at the end.

### Cuts from `paper2_main.tex` → workshop short

- **DROP** §6.5 EverMemBench appendix (`paper2_06_5_evermembench.tex` · 272 lines) — move headline 44.4% number into §4, drop the rest. If the workshop allows supplementary, attach as `supplementary.pdf`.
- **DROP** V4-pro negative-result appendix (`paper2_v4_appendix.tex` · 161 lines) — save the V3.2-vs-V4-pro tied-accuracy story for the full paper. The workshop short version mentions V4-pro in one sentence at most.
- **DROP** cross-judge appendix (`paper2_appendix_crossjudge.tex` · 163 lines) — keep `κ=0.772` as a single sentence in §4, not a full appendix.
- **DROP** drift appendix (`paper2_appendix_drift.tex` · 151 lines) — drift detection is paper-1's contribution; workshop short version cites paper-1 in 1-2 sentences and links the AUC=0.92 figure to it, no own appendix.
- **DROP** §3 BM25 inconsistency paragraph (P1 in audit, `paper2_03_method.tex:7,16-20`) — fix while shortening since we're rewriting §3 anyway.
- **TRIM** §4 evaluation: keep the 6-LLM thinking-mode table (this is the workshop's main draw) + per-type breakdown for v0.8 vs Gemini baseline. Drop refusal-cascade trace plot (Figure 2 alt) — one sentence about MiniMax 44% refusal is enough.
- **TRIM** §5 discussion to 0.5 pages: keep "why per-model thinking varies" + "graph rerank fails on closed haystack" mechanisms; drop future-work bullets.
- **KEEP** abstract (already 189 words, fine for workshop) · §1 intro · §3 method (slimmed) · §4 eval (1 table + 1 figure) · §5 discussion (1 paragraph each on the two negative findings) · §6 limitations (1 paragraph).
- **KEEP** Figure 1 (pipeline) — this is the visual punchline.
- **KEEP** the 56.6% / 44.4% / +27 pts ssu / κ=0.772 / 1/15-cost numbers in the abstract.

Estimated post-cut length: **8–10 pages with refs** for full short version, or **4–5 pages** if the page-limit is the 4-page short format (in which case we further drop §6 limitations and the per-LLM thinking ablation table compresses to 2 rows).

### Workshop-specific framing

The workshop is on **memory**, **not** on benchmarks. The 27-page paper2 is structured as "we built a benchmark contribution + a pipeline contribution + a platform contribution." For a memory workshop, only **one** of those three is the right anchor:

> **Reframed thesis for the workshop short**:
> *"Multi-angle query rewriting — not reranking, not graph augmentation — is the dominant lever for sub-paragraph memory recall in conversational agents. We show this with a controlled ablation across 6 LLMs and a closed-haystack benchmark, and we publish a negative result for graph reranking that the workshop community should care about before reproducing."*

This framing prioritizes the **architectural insight** (what to do at retrieval time for memory) over the **benchmark numbers** (we got 56.6% on LongMemEval-S). The 56.6% becomes the witness for the architecture, not the headline.

Concrete workshop-friendly emphasis shifts:
- §3 method now leads with **why each component is in the pipeline**, in dependency order: *dense recall (bge-m3) → cross-encoder rerank (bge-reranker-v2-m3) → query rewriting (the load-bearing piece) → type-aware prompting (a polish layer)*. Each component has a 1-paragraph "why this and not the alternative."
- §4 evaluation leads the "Mem0 / MemOS / Zep architectural comparison" table (which currently sits in §6.5 EverMemBench) — at the **architectural** level, not just benchmark numbers. E.g., "Mem0 stores fact-extracted summaries; we store turn-level chunks. MemOS uses an LLM-driven importance scorer at write time; we defer all ranking to read time." This is exactly the kind of comparison a memory workshop reviewer wants.
- §5 discussion makes the open-source positioning explicit: "all four prior systems we compare against are either closed-source or partially closed; this paper's pipeline is bge-m3 + open-source LLM-via-Ark + MIT code, replicable for ¥10."

### Cover letter (200–300 words · NOT counted toward 8 pages)

```
Dear ICLR 2026 [TODO workshop name] organizers,

We submit "[TODO workshop-tailored title — see below]" as a short paper. The
work investigates which retrieval-pipeline components actually move the
needle on long-conversation memory recall, with a focus on results that
practitioners can reproduce on commodity hardware.

The paper makes three contributions that we believe fit the workshop scope:

(1) Architectural ablation. Across the 5-stage pipeline (dense recall →
    cross-encoder rerank → multi-angle query rewriting → type-aware
    prompting → judge), we show that multi-angle query rewriting accounts
    for +27 points on the single-session-user subset — larger than the
    reranker. This is, to our knowledge, the first systematic isolation of
    rewriting from reranking in a memory-recall context.

(2) Negative finding on graph augmentation. Adding a Neo4j entity-rerank
    layer reduces accuracy by 6 points on the closed-haystack regime of
    LongMemEval-S. We publish this so the community does not repeat the
    integration work; we discuss why open-haystack regimes likely behave
    differently.

(3) Open-source reproducibility. The full pipeline replicates 56.6% on
    LongMemEval-S for ~$3.50 in API costs using DeepSeek V3.2 + bge-m3,
    1/15 the cost of Gemini-2.5-pro stacks. Code, scripts, and raw
    question-level outputs are MIT-licensed.

This is a shortened version of an arXiv preprint we plan to release as
[TODO arXiv ID once issued, expected 2026-05-13]. The arXiv version
contains additional appendices on V4-pro negative results, cross-judge
replication, and a multi-party benchmark (EverMemBench-Dynamic 44.4%,
beating MemOS); we would prefer to highlight the load-bearing memory
architecture insights at the workshop and refer reviewers to the arXiv
version for the broader benchmark story.

We declare no conflicts of interest with the workshop organizers.

Best regards,
chunxiaoxx
Nautilus Platform
```

> Cover letter caveats:
> - Do not submit cover letter unless the venue requests one. Most OpenReview workshops accept it as the "Submission notes" textarea.
> - If the workshop is double-blind, **redact** the GitHub URL and the "Nautilus Platform" affiliation from the cover letter. Keep them in the camera-ready version only.

### Workshop-tailored title candidates

Pick one based on `[TODO workshop name]`:

- A. *"Multi-Angle Query Rewriting Is the Dominant Lever in Conversational Memory Recall: A Controlled Ablation on LongMemEval-S"* — leads with the architectural finding, hides the benchmark.
- B. *"What Memory Architectures Get Wrong: A Reproducible Pipeline Achieving 56.6% on LongMemEval-S at 1/15 Cost"* — provocative, puts numbers up front, more HN-friendly.
- C. *"Compass: Open-Source Memory Recall for LLM Agents · Architectural Lessons from Six Models and Two Benchmarks"* — leans on the platform narrative; weakest because it forces the V4-pro and EverMemBench results in.

**Recommendation**: A for double-blind / archival workshops · B for non-archival / lighter venues · C only if the workshop explicitly invites system-builder narratives.

---

## Risk assessment

### R1 · Workshop may not exist
**Likelihood**: Medium-high. As noted above, no offline-verifiable reference. **Mitigation**: human runs the 15-min CFP search on iclr.cc / OpenReview before any work happens on the short version. If the workshop does not exist, jump to the "Backup if ICLR Memory Workshop doesn't exist" section.

### R2 · Deadline already passed
**Likelihood**: Medium-high. ICLR 2026 workshop deadlines historically close **Feb-March 2026**; today is 2026-05-07. **Mitigation**: confirm current deadline state. If passed, immediately pivot to one of the backup venues. The 8-page short version is reusable across all of them with minor edits.

### R3 · Double-blind anonymity vs paper1 cross-citation
**Likelihood**: High if double-blind. Paper1 (`paper/PAPER1_ARXIV_READINESS_2026-05-07.md`) is the same author and is already on track for arXiv 2026-05-12. The drift-detection AUC=0.92 number is paper1's contribution; paper2's §3.5 cites it. **Mitigation**: Three options:
1. Fully redact paper1 references for the anonymous submission; cite as "[anonymous companion preprint, 2026]". Restore in camera-ready.
2. Replace paper1 cross-cite with a one-paragraph paraphrase of the drift-detection method, attributed to "concurrent work" without naming paper1.
3. Drop the drift detection mention entirely (it's not the workshop's focus anyway). **Recommended**: option 3 — the workshop short version doesn't need drift detection at all, since the framing is purely about retrieval pipelines.

### R4 · Parallel submission rule conflict with TMLR / arXiv
**Likelihood**: Low for arXiv (most archival workshops permit arXiv preprints) · Medium for TMLR (some non-archival workshops disallow journals submitted in parallel). **Mitigation**: confirm parallel-submission policy in the workshop CFP. If TMLR is in the publication plan, **delay TMLR submission until workshop notification** to avoid policy violations. The arXiv preprint itself is generally fine (most ML workshops have explicitly carved out arXiv).

### R5 · Workshop is poster-only or has no proceedings
**Likelihood**: Low-medium. Some ICLR workshops accept submissions but produce only posters, no paper proceedings. **Mitigation**: prepare a 36×48 inch poster in parallel with the short paper. The pipeline figure (`figures/pipeline_v08.pdf`) is already poster-quality; expand to a single-panel poster with the per-type breakdown table + the +27 pts callout. Estimated effort: 4–6 hours after the short paper is final.

### R6 · 27→8 page reduction loses too much
**Likelihood**: Low. The 27-page paper has clear "appendix-grade" content (V4-pro, cross-judge, drift, EverMemBench detail) that is genuinely supplementary. The core architectural argument fits in 8 pages. See "Strongest argument for SHORTENING" below.

### R7 · Reviewer might want the full LongMemEval table (all 6 LLMs × all 6 question types = 36 cells)
**Likelihood**: Medium. Memory-workshop reviewers often want exhaustive ablations. **Mitigation**: include the full table as a supplementary file. Workshop short paper carries only the 1-table summary; supplementary is the full benchmark.

---

## Action items (in dependency order)

1. **`[user, 15 min, non-blocking]`** Verify CFP at iclr.cc/Conferences/2026/Workshops and OpenReview · resolve every `[TODO]` in the CFP recon table above. This is the single gating step for the entire plan.
2. **`[user, 0 min, decision]`** Confirm whether to submit at all, given (a) deadline status from step 1, (b) anonymity rules from step 1, (c) parallel-submission policy from step 1.
3. **`[agent-able, 6–10 hours]`** Once CFP is verified and submission is approved, write the 8-page (or 4-page) short version. Source: `paper2_main.tex` minus the 4 dropped sections, plus reframed §3 + §5 per the "workshop-specific framing" guidance above.
4. **`[agent-able, 1 hour]`** Build the short PDF on the workshop's `.cls` template. Verify page count matches limit. Verify references render cleanly (no placeholder bib notes — same P0 fix as the audit).
5. **`[user, 30 min]`** Create OpenReview account if needed (most users have one already from prior ICLR submissions). Register for the venue.
6. **`[user, 30 min]`** Submit the short paper + supplementary + cover letter via OpenReview. Take screenshots of the submission confirmation.
7. **`[agent-able, 4–6 hours, parallel to step 3]`** If R5 is confirmed (poster-only), prepare the 36×48 inch poster in parallel.
8. **`[user, ongoing]`** Monitor reviewer comments; respond within 48 hours.

Critical-path estimate **assuming the workshop exists, deadline has not passed, and parallel-submission is allowed**: ~12 hours of agent work + ~1.5 hours of user work, spread over 1–3 days.

If any of the three "assuming" clauses fails, total wall-clock cost is: 15 min user web search → realize the workshop is dead/closed → pivot to a backup venue (next section) → reuse 80%+ of the short version.

---

## Backup if ICLR Memory Workshop doesn't exist

> **Fact check**: I cannot verify any of the workshop names below either, since I have no live web access. Treat them as **plausible placeholder venues** the user should look up. Each is annotated with what we know vs what is `[TODO]`.

### Tier 1 (best fit · memory / long-context themed)

- **NeurIPS 2026 — workshop track** · `[TODO]` verify whether a memory-themed workshop is in the 2026 lineup. NeurIPS 2025 had several memory- and long-context-adjacent workshops; 2026 likely has at least one. Workshop CFPs typically open July–August 2026 with Sept–Oct deadlines; conference is December 2026. **Best primary fallback** if ICLR workshop is dead.
- **ACL 2026 Industry Track** · `[TODO]` verify deadline. ACL 2026 is typically held in summer; industry track deadlines are around February–March. As of 2026-05-07, **likely already passed** for ACL 2026 itself, but ACL has a rolling Findings track that may absorb shorter contributions.
- **EMNLP 2026 Findings** · `[TODO]` verify deadline. EMNLP main paper deadline is typically June; Findings rolls along. The 56.6% LongMemEval-S result is competitive at EMNLP Findings difficulty.

### Tier 2 (workshop-style venues that often run alongside main confs)

- **COLM 2026** (Conference on Language Modeling) · `[TODO]` verify · COLM is a relatively new venue with a memory-adjacent track. Open-source-friendly and typically has rolling workshop submissions.
- **NeurIPS 2026 — Foundation Model Interventions Workshop or successor** · `[TODO]` exact name. The 2024/2025 versions of this workshop accepted memory-system submissions. Look for `iclr-fmi.cc` or successor URLs.
- **TMLR direct** · TMLR is a journal, not a workshop, but it has rolling submissions and a friendly review process. The 27-page version of paper2 fits TMLR formatting cleanly. The workshop short version does **not** preempt TMLR submission of the long version, since TMLR considers long-form contributions. **Strongly recommended as the long-form home regardless of workshop outcome.**

### Tier 3 (lower-fit but available)

- **AAAI 2026 Workshop on Memory and Reasoning in LLMs** · `[TODO]` likely exists, deadline likely passed. AAAI 2026 is February 2026.
- **A Chinese-LLM-themed workshop at NLPCC 2026** · `[TODO]` · the per-model thinking-ablation results are particularly valuable for a Chinese-LLM-focused audience and might play better at NLPCC than at a Western-LLM-defaulted venue.

### Backup workflow

1. Run the 15-min web search step from "Action items" #1 against **all** Tier 1 venues, not just ICLR.
2. Pick the venue with the (a) earliest open deadline ≥ 2 weeks out, (b) compatible parallel-submission policy with arXiv + TMLR plan, (c) stated memory/long-context scope.
3. The 8-page short version is **reusable across all backup venues** with minor template substitution (NeurIPS uses `neurips_2026.sty`; ACL uses `acl-style-files`; EMNLP shares ACL's; COLM has its own). Estimated template-port cost: 30 min per venue.

---

## Strongest argument for SHORTENING vs SUBMITTING-FULL-AS-IS

> **Verdict: SHORTEN.** The workshop is the wrong forum for the 27-page paper. Submitting full would be a methodological mistake and a strategic mistake.

### Methodological reasons to shorten

1. **The 27-page paper is three papers stitched together.** §1–§5 is the LongMemEval-S retrieval-pipeline paper. §6.5 EverMemBench is a separate multi-party benchmark contribution. Appendix C (V4-pro) is a sample-size methodology essay. Each is independently publishable; combining them is what the arXiv preprint is for, not a workshop short. Workshop reviewers will **rightly** ask "what is this paper about?" if all three are present at workshop length.
2. **Reviewer attention budget at workshops is ~30 minutes per paper.** A 27-page paper at workshop submission gets the same 30 minutes as an 8-page paper, which means appendices are skimmed at best. The architectural insight (multi-angle query rewriting > reranker) needs to land in the first 4 pages to survive. In the current 27-page structure, that finding is in §4.3 (around page 8) — past the reviewer's attention budget for skim-grade reading. Shortening forces the lead-with-insight discipline.
3. **The "1/15 cost" claim is more credible at workshop length.** In the 27-page version, 1/15 is one bullet among many, easy to dismiss as an over-claim. In an 8-page version focused on architectural choices, the cost argument becomes the natural "and-here's-why-this-matters" closer. Same number, different rhetorical weight.
4. **Negative-result publication is more visible at workshops than in arXiv preprints.** The graph-rerank-fails-on-closed-haystack finding is exactly the kind of contribution that workshops were designed to surface and that gets buried in an appendix on arXiv. Lifting it from §4.5 (appendix-adjacent in current draft) to a §3 motivating example in the workshop short makes the negative result a first-class contribution.

### Strategic reasons to shorten

5. **The arXiv version is the long form.** We will already have the 27-page version on arXiv (per the audit, planned 2026-05-12). The workshop is the **second** appearance of the work, and its job is to drive workshop reviewers and conference attendees back to the arXiv version. A shortened, sharper, more accessible paper is a better entry point than a re-submission of the long form.
6. **Workshop acceptance signals are more useful at workshop length.** A 4-page or 8-page paper accepted at an ICLR workshop is a credibly reviewed contribution. A 27-page paper accepted at a workshop is, frankly, a weird fit and signals that the authors did not respect the venue's conventions.
7. **The shortened version is reusable across all backup venues.** As noted in the backup section, we will likely need 2–3 venues over 6–12 months: workshop (visibility) + TMLR (long-form citation home) + arXiv (preprint). The 27-page version goes to arXiv and TMLR; the 8-page version goes to the workshop and to any backup venue. Investing once in the shortened version pays out at every workshop / industry track downstream.

### What we lose by shortening (honest accounting)

- The V4-pro tied-accuracy + sample-size lesson (appendix C) does **not** appear in the workshop version. This is the highest-quality ablation in the whole paper and is a genuine loss. **Mitigation**: arXiv version retains it; we can write a "tweet-thread" version of the V4-pro lesson as standalone communication later. Sample-size discipline is a contribution we can talk about for years.
- The cross-judge replication (κ=0.772, appendix B) is reduced to one sentence in §4. Reviewers who care about evaluator robustness will not see it. **Mitigation**: include the full cross-judge appendix as supplementary material.
- The drift-detection AUC=0.92 cross-cite to paper1 is dropped entirely. **Mitigation**: paper1's own preprint is on arXiv; readers find it via the cover letter's "[TODO arXiv ID]" reference.
- The 8 fusion-points platform diagram (Figure 3 in the long version) is dropped. **Mitigation**: the platform integration story is not the workshop's point; this was the right cut.

### Verdict

**Shorten.** The workshop short version is a *better paper for the workshop audience* than the 27-page version. The 27-page version has a different home (arXiv preprint, TMLR long submission). They serve different purposes; submitting the 27-page version to a workshop is conflating purposes and would weaken both papers.

---

## Self-check (per `verification-mandatory.md`)

- [x] All `[TODO]` markers explicitly flagged; no fabricated workshop URLs or dates.
- [x] No claim that a workshop "exists" without checking; the recon section explicitly disclaims this.
- [x] Risk section enumerates the realistic possibility that the workshop doesn't exist, deadline has passed, or anonymity rules conflict.
- [x] Backup venues are flagged as plausible-but-unverified, not asserted.
- [x] The "shorten" recommendation is reasoned from the workshop's audience and attention budget, not from a generic "papers should be short" prior.
- [x] No `[TODO]` is hidden inside prose; every unverified fact is bracketed.
