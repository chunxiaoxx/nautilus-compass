# Benchmark Loop Phase 4 — Paradigm B (division-of-labor) falsifiable probe design

> 2026-06-03 · platform-soul dialog · brainstorming skill output (design, not code)
> Predecessor: Phase 1–3 tested **Paradigm A (ensemble / consensus)** and falsified it
> on HumanEval/M3 (persona net +1.83pp, sign-test p=0.109, did not escape noise).
> User correction (2026-06-03): the industry-mainstream and more likely valuable
> pattern is **Paradigm B — division-of-labor**: decompose into sub-tasks, give each
> sub-agent specialized skills/MCP + a clean, minimal, isolated context.

## 0. Purpose and the scientific trap to avoid

Test whether **division-of-labor multi-agent** beats a single agent on tasks that
genuinely need decomposition — and, if it does, **attribute the gain to the right
cause**.

The Phase-A lesson: we nearly credited a best-of-N selection gain to a "persona
moat." The Paradigm-B analog of that trap is:

> "More sub-agents → more LLM calls / more turns / more tokens" can beat a single
> agent **just by buying more compute**, not because of clean isolated context or
> tool specialization.

Every design choice below exists to make the probe *falsifiable* and to keep that
confound controlled.

## 1. Locked decisions (from brainstorming Q&A)

| Decision | Choice | Rationale |
|---|---|---|
| Dataset | SWE-bench-lite **core subset** (not full 300) | repo-level, real GitHub issues, official held-out tests = external ground truth; concentrate statistical power on decomposition-relevant items |
| Main hypothesis | **2×2 factorial**: context-isolation × tool-specialization | attribute any gain to context, tools, or their interaction — not a confounded bundle |
| Scaffold | **adapt an existing minimal open-source SWE-bench scaffold** | anchor #5 (don't reinvent); credible baseline alignable to published numbers |
| Budget fairness | **matched total budget** (headline) + natural budget (auxiliary) | isolate structure from compute; the core confound control |
| Core-set selection | **neutral structural criterion**: gold patch spans ≥2 files / ≥2 hunks | no selection bias; do NOT select on baseline failure |
| Base model | **cross-lab: M3 + DeepSeek** | M3's 1M context makes the monolithic baseline *hard to beat* (strict falsifiability); cross-lab = does the effect replicate across models |

## 2. The 2×2 arms

Each arm is a complete SWE-bench solver. Two orthogonal factors:

- **Factor A — context**:
  - `mono`: one agent, one continuously growing mixed window (explore → localize →
    edit → run tests, all in one context).
  - `decomp`: decomposed into sub-agents; **each sub-agent receives only a curated,
    minimal, isolated context + a structured handoff** (it does not inherit the
    others' full transcripts).
- **Factor B — tools**:
  - `generic`: one uniform general toolset for everything.
  - `special`: role/task-matched tools + role-tuned prompts (e.g. localizer →
    grep / repo-map, no edit; editor → read + edit, no test-run; tester → run-tests
    + read, no edit).

| Arm | A | B | What it measures |
|---|---|---|---|
| 1 | mono | generic | **baseline** = adopted scaffold as-is |
| 2 | mono | special | tool-specialization main effect = (2−1) |
| 3 | decomp | generic | **context-isolation main effect = (3−1)** — the user's core claim |
| 4 | decomp | special | full Paradigm B = (4−1); **interaction = (4−3) − (2−1)** |

**Operationalization risk (must be nailed in the plan):** arm 2 (`mono` + `special`)
means "single agent given better/specialized tools (repo-map, AST search), but the
work is **not decomposed**." Its difference from arm 1 must be *tool quality /
specialization*, not partitioning of work. If the spec is loose, arm 2 collapses
into arm 1 and the tool main-effect becomes uninterpretable.

## 3. Fitness = external ground truth

A patch *resolves* an instance iff `FAIL_TO_PASS` all pass **and** `PASS_TO_PASS` do
not regress. Scoring uses the **official `swebench` evaluation harness** (Docker),
not a home-grown scorer (anchor #5; scores are alignable to published numbers). We
reuse the *philosophy* of PR #127's held-out execution; we reuse the official
*harness* for the actual verdict.

## 4. Confound control / fairness (the key defense)

- **Matched total budget**: equalize the per-instance cap on total LLM tokens (or
  total tool-call turns) across all four arms. Otherwise `decomp` arms merely buy
  more compute. Headline falsifiable claims use the matched-budget figure; a
  natural-budget figure is reported alongside (real deployments differ).
- Same base model, temperature, and max attempts within a model.
- This is the direct analog of "best-of-N ≠ persona moat": here, **"more
  turns/tokens ≠ clean context."**

## 5. Statistics (reuse Phase 3 escape-noise apparatus)

- Paired across arms (same instances), multi-seed re-runs. Reuse
  `aggregate_multiseed` / `binom_sign_test` from the `benchmark/phase3-multiseed`
  worktree.
- **Escape-noise gate (same conservative criterion as Phase 3):** an effect (e.g.
  the 3−1 context main effect) counts only if mean > 0 **AND** every seed is
  positive **AND** the paired sign-test p < 0.05. Otherwise: recorded as
  "within noise." 1-instance luck ≠ effect.
- Run the whole 2×2 on M3 **and** DeepSeek separately; an effect must replicate
  across both models to be called real.

## 6. Staging — the first minimal falsifiable probe (anchor #3: no full apparatus first)

1. **Probe 0 (smoke):** adopted scaffold runs arm 1 (`mono`/`generic`) on ~5
   instances; confirm a resolve rate sane vs published numbers (the Phase-2
   "single = 76.8% is sane" self-check).
2. **Probe 1 (minimal falsifiable):** run **only arm 1 vs arm 3** (baseline vs
   `decomp`/`generic`) on the core set, matched budget, 1–2 seeds, on M3. This is the
   cheapest direct test of the user's core hypothesis — *does clean isolated context
   alone beat a single mixed-context agent?* If arm 3 fails to beat arm 1 at matched
   budget, the whole Paradigm-B context claim is in trouble and we save the full-2×2
   cost.
3. **Expand to full 2×2 + multi-seed + DeepSeek only if Probe 1 shows signal.**

## 7. Scaffold selection (spike done 2026-06-03 via 3 parallel research agents)

**Decision: build all four arms on a single scaffold — `mini-swe-agent` — and use
`Agentless`'s pipeline only as a *design reference* for the decomposed arms. Do NOT
use two different codebases as the arms.**

Why single-scaffold: if `mono` arms ran on mini-swe-agent and `decomp` arms ran on
Agentless, the arms would differ by the *entire scaffold codebase*, confounding the
context-isolation factor with implementation differences. The 2×2 is only clean if
all four arms share one codebase and vary *only* the two factors. (This is the same
operationalization discipline as §2's arm-2 risk.)

Spike findings (all three projects: MIT-licensed; sources in the research reports):

- **mini-swe-agent** (chosen base): genuinely ~100–200 LOC, bash-only, no native
  tool-call schema to map — ideal for plugging in our custom `LLMClient` over
  MiniMax-M3 / DeepSeek via a duck-typed `query(messages)->dict` model class. Ships
  native `step_limit` + `cost_limit` + global caps (matched-budget out of the box;
  **strict token-matching needs a small `query()` extension** since native caps are
  steps/$ not tokens). The loop is already modular (`run`/`step`/`query`/
  `execute_actions`) with override hooks, so the `decomp` arms (orchestrate N
  role-scoped instances with isolated context + per-role tool gating) are tractable
  to build on top. **Risk:** no cleanly citable SWE-bench-*Lite* number (published
  figures are Verified) → Probe 0 must establish our own baseline.
- **Agentless** (design reference only): MIT, deliberately non-agentic fixed pipeline
  (localization → repair → patch validation) where **each stage already runs as a
  separate LLM call over its own focused context** — this *is* the "clean isolated
  context per sub-step" our hypothesis targets, so it's the blueprint for our
  `decomp` arms. Provider swap via OpenAI-SDK + `base_url`. **Risk:** its strength is
  deeply specialized (purpose-built per-stage prompts + embedding retrieval + a
  reproduction-test reranker), all confounded with "decomposition"; adopting it
  wholesale would make the 2×2 factors inseparable — hence reference-only.
- **SWE-bench official harness + dataset**: feasible on one x86_64 cloud VM (8+
  cores, 16 GB RAM, ~120 GB disk, Docker, `--cache_level=env`); Lite is only 6 repos
  so a 30–60 core subset pulls few env images and runs in well under an hour of test
  time. **Subset filtering by gold-patch structure is a pure string parse, no Docker:
  files = count of `diff --git ` headers, hunks = count of `@@` headers** in the
  `patch` field. Each arm must emit a JSONL of `{instance_id, model_patch,
  model_name_or_path}` for `run_evaluation`. Escape hatch from local Docker: Modal
  (`--modal true`) or sb-cli. **Main infra risk:** Docker disk exhaustion (never use
  `cache_level=instance` ≈ 2 TB; pin `env`, enable `--clean`). All fields needed
  (`patch`, `test_patch`, `FAIL_TO_PASS`, `PASS_TO_PASS`, `repo`, `base_commit`) are
  present in `princeton-nlp/SWE-bench_Lite` (300-row test split).

Next step before writing-plans: confirm multi-file/multi-hunk subset is large enough
to hit N≈30–60 (Lite gold patches skew small) — a pure-Python count over the HF
dataset, no Docker.

## 8. Guardrails carried in

- benchmark = proxy, **not** market validation. No wiring V5 RSI / economic loop /
  compass L4 before a real escape-noise signal (anchor #3).
- Reuse PR #127 harness skeleton where possible (anchor #5); the orchestration logic
  (decomposition, isolated-context handoffs, per-role tool gating, budget caps) is
  new.
- Falsifiable on day 1 via Probe 1; do not build the full 4-arm × 2-model ×
  multi-seed apparatus before Probe 1 shows signal.

## 10. Subset sizing result (2026-06-03, pure-Python count, no Docker)

Ran `swebench_lite_subset_count.py` over `princeton-nlp/SWE-bench_Lite` test split
(300) and cross-checked `SWE-bench_Verified` (500). Counting: files = `diff --git `
headers, hunks = `@@` headers in the `patch` field.

| Dataset | total | single-file | files≥2 | hunks≥2 | hunks≥3 |
|---|---|---|---|---|---|
| Lite | 300 | **all 300** | **0** | 110 | 37 |
| Verified | 500 | 429 | 71 | 220 | — |

**Key finding (corrects a design premise):** SWE-bench **Lite is single-file by
construction** — *every* gold patch touches exactly one file (largest patch:
`django__django-11019`, 1 file / 3 hunks). So the design's "≥2 files OR ≥2 hunks"
criterion collapses on Lite to **≥2 hunks = 110** instances; the ≥2-files branch is
structurally impossible there. Genuine multi-file decomposition tasks live only in
Verified (71 at files≥2).

**Decision (user, 2026-06-03): lock Lite + ≥2 hunks (N=110).** Rationale: the §2
`decomp` factor is a *pipeline* decomposition (localize→edit→test, each stage on a
curated isolated context), not a per-file split — so Probe 1's context-isolation main
effect (arm 1 vs arm 3) is testable even on single-file multi-hunk patches (a growing
mixed window vs staged clean contexts). The scaffold spike (§7) was already scoped to
Lite's 6 repos / single VM (cheapest, anchor #3 minimal-falsifiable-first). The
strongest *literal* form of division-of-labor (cross-file parallel sub-agents) is
deferred to a possible Verified expansion **only if Probe 1 shows signal**.

Artifacts: subset ids in `phase3/agent-engine/benchmarks/swebench_lite_core_subset.json`
(110 rows: `{instance_id, repo, files, hunks}`); counter in
`swebench_lite_subset_count.py`. Subset by repo: sympy 30, django 29, sklearn 16,
sphinx 10, matplotlib 9, pytest 5, astropy 3, flask 3, requests 3, pylint 2.

## 9. Open follow-ups (not blocking the design)

- Root-cause fix surfaced in Phase 3: `LLMClient.chat` has no per-request timeout →
  a hung M3 request deadlocks `ThreadPoolExecutor.map`. Fix: pass `timeout=` through
  `messages.create` (~180s) so a hang raises and `_chat_safe` retries/degrades.
  Needed before any long multi-seed cloud run. Backlog, not "I'll remind myself."

## Relations

- `session_20260603_phase3_multiseed_code_done_run_in_progress.md` (Paradigm A
  falsified — the trigger for this reframe)
- `design_20260603_multiagent_paradigm_b_division_of_labor_reframe.md` (the reframe)
- `design_20260601_external_selection_pressure_benchmark_loop.md` (direction source:
  benchmark = external selection pressure; SWE-bench candidate)
- PR #127 (harness skeleton + escape-noise stats to reuse)
