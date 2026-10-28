# genopt_factory Architecture

> Adapter-pattern reference for producing Frontier-Eng generative-optimization
> benchmark tasks. Companion to `vtf/BUYER_SPEC_GenOpt_RL_20260702.md` (the
> buyer authoritative spec).
>
> **SSOT scope** = the factory root, the 5 task domains currently covered, the
> universal pipeline (data generation → baseline/reference → verifier →
> 9 frontier_eval metadata → H800 N=3 calibration → binding to platform
> fde_verdicts).
>
> Any new task domain MUST follow this contract. Do not branch.

## 1. The producer ↔ verifier ↔ producer identity boundary

The buyer is buying "1000 instances of continuous-scoring optimization
problems". The shape of every instance is the same: a sub-runnable program
that gets called repeatedly with verifier-supplied feedback, with a deterministic
continuous score in [0, 100].

Three actors, all with strict identity:

| actor | role | identity | boundary |
|---|---|---|---|
| **generator** (this factory) | emits task instances | `task_uid` ∈ `genopt_factory.tasks` | pre-run |
| **producer** (a registered platform agent) | submits candidate solver code, gets back metrics | `agent_id` (integer, on-chain) | per round |
| **verifier** (per-task script) | runs candidate, returns continuous score | filesystem path | per round |

The **producer** is NEVER a Claude Code dialog or a bare string claim — that
violates `LOOP_STATE_SSOT.md` §0-ARCH and has bitten us repeatedly
(see `feedback_producers_must_be_registered_agents_not_claude_dialogs_20260622.md`).

Concrete enforced paths:

```
register_h800_producer.py
    → POST /api/agent-first/challenge  (code capability → "55")
    → POST /api/agent-first/register
    → ~/.nautilus/<producer_id>_credentials.json
        {agent_id (int), wallet_address, api_key}

persist_trajectory_verdict.py
    → POST /api/fde/verdicts
        {verdict_id, task_uid, source="h800-genopt-runner-<id>",
         overall_pass, score, items[], artifacts{}}
    → row in `fde_verdicts` with `producer_agent_id` binding
```

If the platform backend is unreachable (current state, 7/2 23:30), the
**offline fallback** is a local registry at `genopt_factory/producer_registry.json`
mapping `producer_id` → `{name, h800_host, capabilities, created_at}`. The
trajectory JSON is then written locally with `source=<producer_id>` and is
marked `provisional · producer-pending` until backend reconciliation.

## 2. Per-task contract (the 14 files every task must contain)

```
<domain>/<task>/
├── Task.md                          # problem statement + hard constraints
├── README.md                        # human summary + grounded data
├── Dockerfile                       # reproducibility
├── requirements.txt                 # stdlib only — informational
├── baseline/init.py                 # weak candidate (editable)
├── reference/solve.py               # strong reference (informational, NOT loaded)
├── verification/evaluate.py         # scoring + validity gate
├── data/
│   ├── instances/*.json             # per-instance inputs
│   ├── optima.json                  # known optima where applicable
│   └── SOURCE.txt                   # sha256 provenance
├── frontier_eval/                   # 9 metadata files (buyer §3.1)
│   ├── eval_command.txt
│   ├── agent_files.txt
│   ├── readonly_files.txt
│   ├── constraints.txt
│   ├── io_format.txt
│   ├── scoring_rules.txt
│   ├── reference_solution.txt
│   ├── instance_provenance.txt
│   └── delivery_metadata.txt
└── gpt55_trajectory_h800.json       # real GPT5.5 N=3 trajectory (filled post-run)
```

The 9 `frontier_eval/*.txt` files implement the buyer's `9 frontier_eval
metadata` requirement (§3.1). They are the contract — any agent (LLM or human)
that picks up the task knows exactly what to read / write / not touch.

## 3. Universal pipeline (H800)

```
task_factory/produce_task.py            (template → K variant)
        ↓
task_factory/fetch_<domain>_synth.py    (synthetic data generation, seed-deterministic)
        ↓
verifier/evaluate.py                    (per-task scoring, MUST be deterministic + read-only
                                          outside baseline/init.py and /tmp)
        ↓
verifier/verifier_qc.py                 (3-iron-rule check: determinism, read-only, timeout)
        ↓
harness/genopt_orlib_run.py             (H800 N=3 GPT5.5 driver, 3 rounds concurrent)
        ↓
gpt55_trajectory.json                   (per-round prompts, raw, code, metrics)
        ↓
producer identity binding               (register_h800_producer.py
                                          + persist_trajectory_verdict.py
                                          → fde_verdicts row)
        ↓
soul canonical verify                   (difficulty grading: Easy/Medium/Hard/Rejected)
        ↓
feishu delivery table                   (S3 交付表 + S3 结算表)
```

## 4. Difficulty grading (the knob)

Buyer's grading (§5.4):

| gap_closed | difficulty | best_score constraint |
|---|---|---|
| ≥ 0.6 | Easy | best < 95 |
| ≥ 0.3 | Medium | — |
| ≥ 0.1 | Hard | — |
| < 0.1 | Rejected | — |
| ≥ 0.6 and best ≥ 95 | Rejected (too easy) | — |

**Empirical knob (from 5 grounded tasks, 7/2):**

The difficulty of a task is determined by the **gap between baseline and
reference** (not the absolute best score):

- Big gap (baseline weak, reference strong) → GPT5.5 N=3 has real headroom → Easy
  or Hard
- Small gap (baseline already close to reference) → Rejected (no headroom)
- The baseline's *kind* of weakness matters: a naive implementation of the
  right algorithm (e.g. naive O(N²) attention) leaves more headroom for a
  smart rewrite than a "smart but flawed" implementation (e.g. a BFD that
  already gets 66% on a tiny instance set).

5-task difficulty distribution (7/2, GPT5.5 N=3 H800):

| task | seed | best | gap | difficulty | baseline | reference |
|---|---|---|---|---|---|---|
| JobShop OR-Library | 24.68 | 94.89 | 0.7022 | Easy | Naive List | GT portfolio |
| TSP TSPLIB (synth) | 89.51 | 100.00 | 0.1048 | Hard | NN single start | 2-opt multi-restart |
| Attention Flash | 0.87 | 33.76 | 0.3289 | Medium | naive O(N²) | Flash BLOCK_N=32 |
| Cache LRU | 0.00 | 0.00 | 0.00 | Rejected (verifier bug fixed in v2) | FIFO | ARC simplified |
| BinPack | 0.00 | 66.67 | 0.6667 | Easy | FF | BFD |

## 5. Domain coverage

| domain | tasks | status |
|---|---|---|
| operations_research_and_decision_science | JobShop, TSP, BinPack | ✅ grounded |
| kernel_engineering_and_systems | Attention Flash | ✅ grounded (Medium) |
| computer_systems | Cache LRU | ⚠️ v2 rerunning |
| quantum_information | — | planned |
| robotics_control | — | planned |
| optical_communication | — | planned |
| energy_systems | — | planned |
| physics_engineering | — | planned |

## 6. What this architecture forbids

- ❌ **GPT5.5 N=3 with no real producer binding.** Every trajectory
  row must have a `producer_agent_id` (or `provisional · producer-pending`).
- ❌ **Verifier reading or writing outside `baseline/init.py` and `/tmp/`.**
  The 3-iron-rule check (`verifier_qc.py`) catches this; v1 Cache
  verifier had a path bug that made `fifo_misses` == `candidate_misses`
  (score 0 for every instance) — fixed in v2.
- ❌ **Per-task hard-rewrite of the verifier pipeline.** Use the
  adapter pattern: domain-specific scoring goes in
  `verification/evaluate.py`; the universal QC is `verifier_qc.py`;
  the N=3 driver is `gapclosed_runner.py`; the batch runner is
  `gapclosed_batch_runner.py`. Do not duplicate.
- ❌ **Verifying trajectory files from a Claude Code dialog as if
  they were the platform's real production.** The dialog writes
  code; the producer (H800 harness, registered agent) runs
  trajectories; the dialog may *persist* them but only after
  producer binding. See §0-ARCH.

## 7. Failure modes we've actually hit

| date | failure | real cause | fix |
|---|---|---|---|
| 7/2 | Cache verifier score 0 for all instances | Path bug: `_fifo_miss_count` ran candidate instead of FIFO | Fix evaluate.py: derive baseline from `--benchmark-dir`, not from `instance_path/../..` |
| 7/2 | GPT5.5 N=3 round 1 wrote Belady/MIN offline optimal — score 0 | (no bug, but) easy to misread as "GPT5.5 failed" | Look at trajectory `source_preview` before concluding |
| 7/2 | TSPLIB official mirror 503 | heidelberg.de unreachable from this env | Synthetic fallback with seed 20260702 + SHA256 chain + SOURCE.txt provenance |
| 7/2 | Local `gapclosed_runner` 502/close on every round | qixuw relay unstable from this host | All real production goes through H800 `harness/genopt_orlib_run.py` with direct `OPENAI_BASE_URL` |
| 7/2 | Producer registration script can't run | backend conn refused | Offline fallback: `genopt_factory/producer_registry.json` (planned) |
