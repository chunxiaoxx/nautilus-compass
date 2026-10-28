# Meta-Harness: Automatic Optimization of Raid Configurations

> **Status**: Design Document (no code)
> **Author**: Dialog B (Architecture)
> **Date**: 2026-04-03
> **Depends on**: Raid Engine (`services/raid_engine.py`), Sandbox A/B (`services/sandbox.py`), Natural-Language Harness YAML (P1)

---

## 1. Problem Statement

### Current State

The Raid consensus engine supports four manually designed configurations:

| Level | Agents | Behavior | Use Case |
|-------|--------|----------|----------|
| Raid 1 | 1 | Execute + self-review | Low-stakes, fast |
| Raid 2 | 1 | Execute -> Review -> Improve (up to 3 rounds) | Default, balanced |
| Raid 3 | 3 | 3 parallel executions + judge picks best | Quality-sensitive |
| Raid 5 | 5 | 5 expert reviews, 4/5 consensus threshold | Mission-critical |

These four levels were designed by intuition. Several problems follow:

1. **No task-type awareness.** A sentiment classification task and an entity extraction task are routed through the same Raid level, despite having fundamentally different quality/cost profiles.

2. **Coarse granularity.** The jump from Raid 2 to Raid 3 changes agent count from 1 to 3, feedback rounds from 3 to 0 (judge-only), and execution mode from sequential to parallel -- all at once. There is no way to, say, use 2 parallel agents with 1 feedback round.

3. **No Pareto frontier.** We have no empirical data on where quality saturates relative to cost. It is plausible that Raid 2 with a stronger judge model outperforms Raid 3 with a weaker model at lower cost, but we cannot test this without infrastructure.

4. **Static forever.** As LLM capabilities improve and costs decline, the optimal configuration drifts. There is no mechanism to track or adapt.

### Desired End State

A system that:
- Continuously collects outcome data from every Raid execution.
- Uses Bayesian optimization to search the harness configuration space.
- Proposes new configurations as sandbox A/B experiments.
- Promotes winning configurations as the new default per task type.
- Runs unattended as a periodic cron job (Layer 1 of the Autonomous Bootstrap Engine).

---

## 2. Optimization Space

### 2.1 Parameter Definitions

Each Raid configuration is a point in a 7-dimensional mixed space:

```yaml
# meta_harness_search_space.yaml

parameters:
  agent_count:
    type: categorical
    values: [1, 2, 3, 5, 7]
    description: >
      Number of agents involved in execution.
      1 = solo, 2-3 = small panel, 5-7 = expert committee.

  execution_mode:
    type: categorical
    values: [parallel, sequential, hierarchical]
    description: >
      parallel    -- all agents run concurrently, judge picks best.
      sequential  -- execute -> review -> improve loop (current Raid 2).
      hierarchical -- lead agent delegates sub-tasks to workers, then merges.

  feedback_rounds:
    type: categorical
    values: [0, 1, 2, 3, auto_stop]
    description: >
      Number of review-and-improve iterations.
      0 = single shot (no review loop).
      auto_stop = continue until quality threshold met or budget exhausted.

  model_tier:
    type: categorical
    values: [fast, balanced, strong]
    mapping:
      fast: "haiku-class (lowest cost, ~3x cheaper)"
      balanced: "sonnet-class (default)"
      strong: "opus-class (highest quality, ~5x more expensive)"
    description: >
      LLM tier used for the executor agent(s).

  judge_model:
    type: categorical
    values: [same_tier, one_tier_up, strongest]
    description: >
      LLM tier used for the reviewer/judge.
      same_tier    -- same as executor model.
      one_tier_up  -- one level stronger (fast->balanced, balanced->strong).
      strongest    -- always use opus-class for judging.

  consensus_threshold:
    type: categorical
    values: [0.5, 0.6, 0.7, 0.8, 0.9]
    description: >
      Fraction of experts/votes that must approve for consensus.
      Only meaningful when agent_count >= 3.
      Lower threshold = cheaper (fewer retries), higher = more reliable.

  cost_budget_nau:
    type: categorical
    values: [1, 5, 10, 25, 50]
    description: >
      Maximum NAU spend allowed for a single task execution.
      Acts as an early-stop constraint: if budget exhausted, return best-so-far.
```

### 2.2 Search Space Size

The full Cartesian product is `5 x 3 x 5 x 3 x 3 x 5 x 5 = 16,875` unique configurations. Many are degenerate (e.g., `agent_count=1` with `consensus_threshold=0.9` is meaningless). After pruning invalid combinations, the effective space is estimated at ~3,000 configurations.

### 2.3 Constraint Rules (Pruning)

```python
CONSTRAINTS = [
    # Single-agent configs ignore consensus_threshold
    lambda c: c["agent_count"] > 1 or c["consensus_threshold"] == 0.5,

    # feedback_rounds > 0 requires sequential or hierarchical mode
    lambda c: c["feedback_rounds"] in (0, "auto_stop") or c["execution_mode"] != "parallel",

    # hierarchical mode requires agent_count >= 3
    lambda c: c["execution_mode"] != "hierarchical" or c["agent_count"] >= 3,

    # judge_model 'one_tier_up' from 'strong' wraps to 'strongest'
    # (not a constraint, just a normalization)

    # cost_budget must be >= agent_count * base_cost_per_call
    lambda c: c["cost_budget_nau"] >= c["agent_count"] * MODEL_COST[c["model_tier"]],
]
```

### 2.4 Task Type Stratification

Optimization runs independently per task type. Initial task types from the platform:

| Task Type | Description | Expected Optimal Profile |
|-----------|-------------|------------------------|
| `sentiment_classification` | Binary/ternary label | Low agent count, fast model |
| `entity_extraction` | Structured NER | Higher agent count, balanced model |
| `text_summarization` | Long-to-short | Sequential + feedback, balanced model |
| `code_review` | Code quality assessment | Strong model, sequential |
| `data_labeling` | Multi-class annotation | Parallel + majority vote |
| `translation` | Cross-lingual | Sequential + feedback |
| `general` | Catch-all | Default Raid 2 until data accumulates |

---

## 3. Objective Function

### 3.1 Multi-Objective Formulation

Each Raid execution produces a triple of outcomes:

```
f(config, task) -> (quality, cost, latency)
```

Where:

- **Quality** `Q in [0.0, 1.0]`: Weighted combination of:
  - `task_success` (binary: did the task complete without error?) -- weight 0.3
  - `consensus_score` (from Raid engine, already recorded) -- weight 0.4
  - `downstream_rating` (if available: requester satisfaction 1-5, normalized) -- weight 0.3

- **Cost** `C in [0, inf)`: Total NAU spent on the execution, including all agent calls, judge calls, and retry rounds. Derived from token counts and model pricing.

- **Latency** `L in [0, inf)`: Wall-clock seconds from execution start to completion. Already recorded as `completed_at - created_at` in `raid_executions`.

### 3.2 Scalarization for Bayesian Optimization

Since BO works best with a scalar objective, we scalarize using a weighted Chebyshev approach:

```python
def objective(quality, cost, latency, weights=None):
    """
    Scalarized objective. Higher is better.

    weights: dict with keys 'quality', 'cost', 'latency'.
    Default: quality-first (the platform's main concern).
    """
    w = weights or {"quality": 0.6, "cost": 0.25, "latency": 0.15}

    # Normalize cost and latency to [0, 1] using observed ranges
    cost_norm = 1.0 - min(cost / MAX_OBSERVED_COST, 1.0)       # lower cost -> higher score
    latency_norm = 1.0 - min(latency / MAX_OBSERVED_LATENCY, 1.0)  # lower latency -> higher score

    return (
        w["quality"] * quality
        + w["cost"] * cost_norm
        + w["latency"] * latency_norm
    )
```

Users (or the platform itself) can override weights to express different preferences:
- **Quality-first**: `{quality: 0.8, cost: 0.1, latency: 0.1}` -- for mission-critical tasks
- **Budget-first**: `{quality: 0.3, cost: 0.5, latency: 0.2}` -- for high-volume labeling
- **Speed-first**: `{quality: 0.3, cost: 0.2, latency: 0.5}` -- for real-time applications

### 3.3 Pareto Frontier Extraction

In addition to the scalar objective, we maintain the full Pareto frontier:

```
A config X dominates config Y if:
  X.quality >= Y.quality AND X.cost <= Y.cost AND X.latency <= Y.latency
  with at least one strict inequality.

Pareto frontier = set of all non-dominated configs.
```

The frontier is recomputed after each batch of evaluations and stored for visualization in the platform dashboard.

---

## 4. Optimization Algorithm

### 4.1 Primary: Bayesian Optimization with Gaussian Process

**Why Bayesian Optimization?**

Each evaluation is expensive -- it requires executing a real task through the Raid engine, consuming LLM tokens and NAU. We need an algorithm that is *sample-efficient*: it should find good configurations in as few trials as possible.

Bayesian Optimization (BO) with a Gaussian Process (GP) surrogate is the gold standard for this setting:
- Builds a probabilistic model of the objective surface.
- Uses an acquisition function (Expected Improvement) to decide which configuration to try next.
- Converges to the optimum in 50-100 evaluations for spaces of this dimensionality.
- Handles mixed categorical/continuous parameters via kernel engineering.

**Implementation Plan:**

```python
# Pseudocode -- not for implementation, illustrative only.

from skopt import Optimizer
from skopt.space import Categorical

space = [
    Categorical([1, 2, 3, 5, 7], name="agent_count"),
    Categorical(["parallel", "sequential", "hierarchical"], name="execution_mode"),
    Categorical([0, 1, 2, 3, "auto_stop"], name="feedback_rounds"),
    Categorical(["fast", "balanced", "strong"], name="model_tier"),
    Categorical(["same_tier", "one_tier_up", "strongest"], name="judge_model"),
    Categorical([0.5, 0.6, 0.7, 0.8, 0.9], name="consensus_threshold"),
    Categorical([1, 5, 10, 25, 50], name="cost_budget_nau"),
]

optimizer = Optimizer(
    dimensions=space,
    base_estimator="GP",            # Gaussian Process
    acq_func="EI",                  # Expected Improvement
    acq_optimizer="sampling",       # For categorical spaces
    n_initial_points=20,            # Random exploration before GP kicks in
    random_state=42,
)

for trial in range(MAX_TRIALS):
    suggested = optimizer.ask()

    # Prune invalid configs
    if not satisfies_constraints(suggested):
        optimizer.tell(suggested, PENALTY_VALUE)
        continue

    # Execute real task with this config
    result = await execute_raid_with_config(task, suggested)

    score = objective(result.quality, result.cost, result.latency)
    optimizer.tell(suggested, -score)  # skopt minimizes, we negate

best_config = optimizer.Xi[np.argmin(optimizer.yi)]
```

### 4.2 Kernel Choice for Mixed Categorical Space

Standard RBF kernels assume continuous inputs. For our fully categorical space, we use:

- **Hamming kernel** for categorical dimensions: `k(x, y) = exp(-gamma * hamming_distance(x, y))`
- **scikit-optimize's default categorical handling**, which uses one-hot encoding + RBF. This is sufficient for our space size.
- If performance is poor, upgrade to **SMAC3** (Sequential Model-based Algorithm Configuration), which was designed specifically for mixed categorical hyperparameter optimization.

### 4.3 Alternative: Multi-Armed Bandit for Online Learning

For task types with high execution volume (>100 tasks/day), a contextual Multi-Armed Bandit (MAB) approach can complement BO:

```
Arms = finite set of known-good configs (from BO's Pareto frontier)
Context = task metadata (type, complexity estimate, requester priority)
Reward = scalarized objective score

Algorithm: LinUCB or Thompson Sampling
```

**When to use MAB vs BO:**

| Criterion | Bayesian Optimization | Multi-Armed Bandit |
|-----------|----------------------|-------------------|
| Exploration phase | First 50-100 trials per task type | After BO has identified top configs |
| Volume needed | Low (sample-efficient) | High (needs many pulls) |
| Handles new configs | Yes (continuous search) | No (fixed arm set) |
| Online regret | Higher (more exploration) | Lower (exploit quickly) |
| Implementation | `skopt` or `SMAC3` | `vowpalwabbit` or custom |

**Hybrid strategy:** Use BO to discover the initial Pareto frontier (Phase B). Once 5-10 good configs are identified per task type, switch to MAB for real-time allocation (Phase D).

### 4.4 Warm-Starting from Historical Data

The `raid_executions` table already contains historical execution data. Before starting BO:

1. Query all completed executions with their config metadata.
2. Compute quality/cost/latency for each.
3. Feed as `optimizer.tell()` observations to warm-start the GP.
4. This gives the optimizer a head start, potentially saving 20-30 trials.

Requires Phase A (execution logging) to be recording config details, not just `raid_level`.

---

## 5. Data Collection

### 5.1 New Table: `raid_execution_log`

Extends the existing `raid_executions` table with full config metadata and computed outcomes.

```sql
-- DDL sketch (not for execution)

CREATE TABLE raid_execution_log (
    id              SERIAL PRIMARY KEY,
    execution_id    VARCHAR(36) NOT NULL REFERENCES raid_executions(execution_id),
    task_type       VARCHAR(50) NOT NULL,       -- e.g. 'sentiment_classification'

    -- Full config vector
    config_agent_count       INTEGER NOT NULL,
    config_execution_mode    VARCHAR(20) NOT NULL,
    config_feedback_rounds   VARCHAR(10) NOT NULL,  -- '0','1','2','3','auto_stop'
    config_model_tier        VARCHAR(10) NOT NULL,
    config_judge_model       VARCHAR(15) NOT NULL,
    config_consensus_threshold FLOAT NOT NULL,
    config_cost_budget_nau   FLOAT NOT NULL,

    -- Outcome measurements
    quality_score            FLOAT,              -- composite [0,1]
    consensus_score          FLOAT,              -- from raid engine
    downstream_rating        FLOAT,              -- requester feedback [1-5], nullable
    total_cost_nau           FLOAT,              -- actual NAU spent
    latency_seconds          FLOAT,              -- wall-clock duration
    token_count_input        INTEGER,            -- total input tokens across all calls
    token_count_output       INTEGER,            -- total output tokens across all calls

    -- Metadata
    optimizer_trial_id       VARCHAR(36),         -- links to BO trial, null for organic
    experiment_id            VARCHAR(36),         -- links to sandbox experiment, nullable
    created_at               TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes
    CONSTRAINT idx_raidlog_task_type_created
        UNIQUE (task_type, created_at, execution_id)
);

CREATE INDEX idx_raidlog_task_type ON raid_execution_log(task_type);
CREATE INDEX idx_raidlog_optimizer_trial ON raid_execution_log(optimizer_trial_id);
```

### 5.2 Logging Integration

Every Raid execution -- both organic (user-triggered) and optimizer-triggered -- writes to this table. The logging happens in `RaidEngine._update_execution()` after status transitions to `completed` or `failed`.

For organic executions, the config fields are derived from the Raid level:

```python
LEVEL_TO_CONFIG = {
    1: {"agent_count": 1, "execution_mode": "sequential", "feedback_rounds": "0", ...},
    2: {"agent_count": 1, "execution_mode": "sequential", "feedback_rounds": "3", ...},
    3: {"agent_count": 3, "execution_mode": "parallel",   "feedback_rounds": "0", ...},
    5: {"agent_count": 5, "execution_mode": "parallel",   "feedback_rounds": "1", ...},
}
```

For optimizer-triggered executions, the full config vector is passed through from the BO trial.

### 5.3 Sample Size Requirements

Statistical power analysis for detecting a 5% quality improvement:

```
Effect size: 0.05 (quality score difference)
Standard deviation: ~0.15 (estimated from current data)
Alpha: 0.05 (two-tailed)
Power: 0.80

Required sample size per group: ~71 observations

Rounding up for safety: 100 evaluations per task type.
```

At 10 tasks/day per type, this means ~10 days per task type to reach reliable optimization. At 50 tasks/day (high-volume types like data_labeling), optimization converges in ~2 days.

---

## 6. Integration with Sandbox A/B Testing

### 6.1 Flow: Optimizer -> Sandbox -> Promotion

```
                    BO suggests
                    new config
                        |
                        v
            +-----------------------+
            | Create Sandbox        |
            | Experiment            |
            | (10% traffic to new   |
            |  config, 90% to       |
            |  current default)     |
            +-----------------------+
                        |
                  24-48h observation
                        |
                        v
            +-----------------------+
            | Evaluate Experiment   |
            | (sandbox.evaluate_    |
            |  experiment)          |
            +-----------------------+
                   /           \
                  /             \
          improved >= 5%    not improved
                |                 |
                v                 v
         +-----------+    +-----------+
         | Promote   |    | Rollback  |
         | to default|    | Keep old  |
         +-----------+    +-----------+
                |
                v
         Update raid_harness.yaml
         with new default config
         for this task type
```

### 6.2 Sandbox Experiment Creation

When the optimizer identifies a promising config (top-3 from BO), it creates a sandbox experiment:

```python
proposed_change = {
    "change_type": "raid_config_optimization",
    "task_type": "sentiment_classification",
    "current_config": get_current_default("sentiment_classification"),
    "proposed_config": {
        "agent_count": 2,
        "execution_mode": "parallel",
        "feedback_rounds": "1",
        "model_tier": "fast",
        "judge_model": "one_tier_up",
        "consensus_threshold": 0.6,
        "cost_budget_nau": 5,
    },
    "expected_improvement": {
        "quality_delta": "+0.07",
        "cost_delta": "-30%",
    },
    "observation_hours": 48,
    "sandbox_traffic_pct": 10,
}

experiment_id = create_experiment(db, proposal_id, proposed_change)
```

### 6.3 Task Routing During Experiment

The existing `sandbox_router.tag_task_for_experiment()` handles traffic splitting. For Raid config experiments, the tagged task also carries the proposed config in its `parameters` JSON:

```json
{
  "experiment_id": "exp_abc123",
  "experiment_group": "sandbox",
  "raid_config_override": {
    "agent_count": 2,
    "execution_mode": "parallel",
    "feedback_rounds": "1",
    "model_tier": "fast",
    "judge_model": "one_tier_up",
    "consensus_threshold": 0.6,
    "cost_budget_nau": 5
  }
}
```

The Raid engine reads `raid_config_override` from the task parameters and uses it instead of the default level-based config.

### 6.4 Config Versioning

Promoted configs are stored in a versioned YAML file (building on the P1 Natural-Language Harness work):

```yaml
# raid_harness.yaml (version-controlled)

version: 3
updated_at: "2026-04-15T10:30:00Z"
updated_by: "meta_harness_optimizer"

defaults:
  general:
    agent_count: 1
    execution_mode: sequential
    feedback_rounds: 3
    model_tier: balanced
    judge_model: same_tier
    consensus_threshold: 0.8
    cost_budget_nau: 10

  sentiment_classification:
    agent_count: 2
    execution_mode: parallel
    feedback_rounds: 1
    model_tier: fast
    judge_model: one_tier_up
    consensus_threshold: 0.6
    cost_budget_nau: 5
    # promoted from exp_abc123 on 2026-04-15
    # quality: 0.87 (+0.07), cost: 3.2 NAU (-30%)

  entity_extraction:
    agent_count: 3
    execution_mode: sequential
    feedback_rounds: 2
    model_tier: balanced
    judge_model: strongest
    consensus_threshold: 0.7
    cost_budget_nau: 15
    # promoted from exp_def456 on 2026-04-18

history:
  - version: 2
    date: "2026-04-10T08:00:00Z"
    changes: ["Added sentiment_classification override"]
  - version: 1
    date: "2026-04-03T00:00:00Z"
    changes: ["Initial config from manual Raid levels"]
```

---

## 7. Implementation Phases

### Phase A -- Raid Execution Logging (Week 1)

**Goal:** Every Raid execution records its full config and outcome metrics.

**Tasks:**

1. Create `raid_execution_log` table via Alembic migration.
2. Add a `_log_execution()` method to `RaidEngine` that writes to the new table after every completed/failed execution.
3. Backfill historical data from `raid_executions` using `LEVEL_TO_CONFIG` mapping.
4. Add token counting to `_llm_call()` -- accumulate input/output tokens per execution.
5. Add NAU cost computation based on model tier and token counts.
6. Write unit tests: verify logging for all 4 Raid levels, verify config extraction.

**Deliverables:**
- Alembic migration file
- Updated `raid_engine.py` with logging
- Backfill script
- Tests (target: 90% coverage on new code)

**Estimated effort:** 2-3 days

### Phase B -- Bayesian Optimizer (Week 2)

**Goal:** A standalone optimizer that queries historical data, suggests new configs, and evaluates them.

**Tasks:**

1. Add `scikit-optimize` to requirements (or `SMAC3` if categorical handling is insufficient).
2. Create `services/meta_harness_optimizer.py`:
   - `load_observations(task_type)` -- query `raid_execution_log` for historical data.
   - `suggest_config(task_type)` -- ask BO for next config to try.
   - `evaluate_config(task_type, config)` -- execute a benchmark task with the config, return score.
   - `run_optimization(task_type, max_trials=100)` -- main loop.
3. Create `services/meta_harness_objectives.py`:
   - `compute_quality_score()` -- composite quality metric.
   - `compute_scalarized_objective()` -- weighted aggregation.
   - `extract_pareto_frontier()` -- non-dominated configs.
4. Implement constraint checking and invalid config pruning.
5. Write integration test: run optimizer on synthetic data, verify it converges.

**Deliverables:**
- `meta_harness_optimizer.py`
- `meta_harness_objectives.py`
- CLI command: `python -m services.meta_harness_optimizer --task-type sentiment_classification --trials 50`
- Integration tests

**Estimated effort:** 3-4 days

### Phase C -- Sandbox Integration (Week 3)

**Goal:** Promising configs from the optimizer are automatically deployed as sandbox A/B experiments.

**Tasks:**

1. Create `services/meta_harness_sandbox_bridge.py`:
   - `propose_experiment(task_type, config, expected_improvement)` -- creates a sandbox experiment.
   - `check_experiment_results(experiment_id)` -- evaluates and decides promote/rollback.
   - `promote_config(task_type, config)` -- updates `raid_harness.yaml`.
2. Modify `RaidEngine.execute()` to check for `raid_config_override` in task parameters before falling back to the default level.
3. Add a generalized `RaidEngine.execute_with_config(task, config_dict)` method that accepts the full config vector instead of a Raid level integer.
4. Implement config versioning: atomic YAML writes, version history.
5. Add API endpoint `GET /api/raid/optimized-configs` to expose the current defaults and Pareto frontier.
6. Write E2E test: optimizer suggests config -> sandbox created -> traffic split -> evaluation -> promotion.

**Deliverables:**
- `meta_harness_sandbox_bridge.py`
- Updated `raid_engine.py` with `execute_with_config()`
- Updated `raid_harness.yaml` schema
- New API endpoint
- E2E test

**Estimated effort:** 3-4 days

### Phase D -- Auto-Evolution Cron Job (Week 4)

**Goal:** The optimizer runs unattended as a cron job, continuously improving Raid configs.

**Tasks:**

1. Register `meta_harness_auto_optimize` in the cron registry (Layer 1 of the Autonomous Bootstrap Engine):
   ```python
   "meta_harness_auto_optimize": {
       "interval_hours": 6,
       "fn": run_meta_harness_cycle,
       "budget_ms": 300000,  # 5 minutes
       "description": "Run one BO iteration per task type with sufficient data"
   }
   ```
2. Implement `run_meta_harness_cycle()`:
   - For each task type with >= 50 logged executions in the last 7 days:
     - Load observations.
     - Run 1-3 BO iterations (budget-constrained).
     - If a new config outperforms the current default by >= 5% on the objective:
       - Check if a sandbox experiment for this task type is already running. If yes, skip.
       - Create a new sandbox experiment.
   - For task types with running experiments past their observation window:
     - Evaluate and finalize (promote or rollback).
3. Add monitoring: log optimizer decisions to `platform_metrics_snapshots`.
4. Add guardrails:
   - Maximum 3 concurrent sandbox experiments across all task types.
   - Minimum 48 hours between config changes for the same task type (cooldown).
   - If quality drops >10% after promotion, auto-rollback.
5. Dashboard integration: expose optimization history and Pareto frontiers via API.

**Deliverables:**
- Cron job registration
- `run_meta_harness_cycle()` implementation
- Guardrail logic
- Monitoring and dashboard API
- Full test suite

**Estimated effort:** 3-4 days

---

## 8. Success Criteria

### 8.1 Hard Metrics (must achieve all)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Quality improvement | >= 5% quality score increase at same cost for at least 1 task type | Compare optimized config vs Raid 2 default on same task set |
| Cost reduction | >= 20% NAU cost reduction at same quality for at least 1 task type | Compare optimized config vs current default |
| Task type coverage | >= 3 task types have optimized configs | Count task types with non-default entries in `raid_harness.yaml` |
| Data coverage | >= 100 logged executions per task type before optimization | Query `raid_execution_log` |
| Auto-promotion | >= 1 config promoted via unattended cron job | Check `sandbox_experiments` with `status='promoted'` and `updated_by='meta_harness_optimizer'` |

### 8.2 Soft Metrics (track but don't block)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Pareto frontier size | >= 5 non-dominated configs per task type | Extract frontier from `raid_execution_log` |
| BO convergence speed | Top config found within 80 trials | Track best-so-far curve |
| Sandbox experiment success rate | >= 50% of experiments promoted | `promoted / (promoted + rolled_back)` |
| Latency reduction | >= 10% for speed-sensitive task types | Compare before/after |
| Cron job reliability | >= 95% successful runs over 30 days | Monitor cron execution logs |

### 8.3 Non-Goals (explicitly out of scope)

- **Real-time per-task config selection.** Phase D uses periodic optimization, not per-request routing. Real-time MAB is a future extension.
- **Cross-task-type transfer learning.** Each task type is optimized independently. Sharing information across types is a future enhancement.
- **Model fine-tuning.** We optimize the *harness configuration*, not the underlying LLM weights.
- **Human-in-the-loop optimization.** The system is fully automated. Human override is available but not required.

---

## 9. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Insufficient data volume for reliable BO | Medium | High | Start with highest-volume task types; lower sample requirement to 50 if variance is low |
| Optimizer finds a degenerate config (e.g., always Raid 1 because it is cheapest) | Medium | Medium | Quality floor constraint: reject configs with quality < 0.6 |
| Sandbox experiments interfere with production quality | Low | High | Hard cap at 10% sandbox traffic; auto-rollback on quality drop >10% |
| scikit-optimize struggles with fully categorical space | Medium | Low | Fall back to SMAC3 or random search with pruning |
| LLM pricing changes invalidate cost models | Low | Medium | Recompute cost normalization weekly; store raw token counts, not just NAU |
| Cron job runs during peak load | Low | Medium | Schedule during off-peak hours; budget-constrain each cycle |

---

## 10. Dependencies and Prerequisites

| Dependency | Status | Blocker? |
|------------|--------|----------|
| Raid Engine (`services/raid_engine.py`) | Implemented | No |
| Sandbox A/B (`services/sandbox.py`) | Implemented | No |
| Natural-Language Harness YAML (P1) | In progress | Soft -- Phase A-B can proceed without it |
| `raid_executions` table | Exists | No |
| `sandbox_experiments` table | Exists | No |
| Cron registry (Layer 1) | Exists (`services/cron_registry.py`) | No |
| `scikit-optimize` or `SMAC3` | Not installed | Phase B blocker |
| Token counting in LLM client | Not implemented | Phase A blocker (minor) |

---

## 11. Open Questions

1. **Should the optimizer use real production tasks or synthetic benchmark tasks for evaluation?**
   - Production tasks: most realistic, but slower feedback loop and potential quality risk.
   - Synthetic benchmarks: controlled, repeatable, but may not reflect real distribution.
   - Recommendation: hybrid. Use benchmarks for initial BO exploration (Phase B), then validate top configs on production traffic via sandbox (Phase C).

2. **How to handle task complexity variance within a single task type?**
   - A "sentiment_classification" task with 5 items is very different from one with 500 items.
   - Option A: Add `item_count_bucket` as an additional parameter dimension.
   - Option B: Use item count as context in MAB (Phase D extension).
   - Recommendation: Option A for Phase B, migrate to Option B when MAB is implemented.

3. **What is the NAU cost model for different model tiers?**
   - Need concrete pricing: NAU per 1K input tokens, NAU per 1K output tokens, per model tier.
   - This must be defined before Phase A can compute `total_cost_nau`.

4. **Should we allow users to override the optimized default for their specific tasks?**
   - Yes, but with guardrails. Users can specify a Raid level (existing behavior) or a custom config.
   - The optimizer only changes the *platform default* for unspecified tasks.

---

## Appendix A: Relationship to Existing Architecture

```
                 Autonomous Bootstrap Engine (Layer 5)
                              |
                   meta_harness_auto_optimize (cron)
                              |
                 +------------+------------+
                 |                         |
          Bayesian Optimizer        Sandbox A/B Bridge
          (skopt / SMAC3)           (sandbox.py)
                 |                         |
          raid_execution_log        sandbox_experiments
                 |                         |
          RaidEngine.execute()      sandbox_router.py
                 |                         |
          raid_executions           academic_tasks
                 |
          raid_harness.yaml
          (versioned defaults)
```

## Appendix B: Example Optimization Run (Illustrative)

```
Task type: sentiment_classification
Current default: Raid 2 (agent_count=1, sequential, 3 rounds, balanced, same_tier, 0.8, 10 NAU)
Current metrics: quality=0.80, cost=8.2 NAU, latency=45s

Trial 1 (random):  agent_count=3, parallel, 0 rounds, fast, strongest, 0.7, 25 NAU
  -> quality=0.82, cost=12.1 NAU, latency=18s
  -> objective=0.71

Trial 2 (random):  agent_count=1, sequential, 1 round, fast, one_tier_up, 0.5, 5 NAU
  -> quality=0.78, cost=3.1 NAU, latency=22s
  -> objective=0.74

...

Trial 15 (BO-guided): agent_count=2, parallel, 1 round, fast, one_tier_up, 0.6, 5 NAU
  -> quality=0.87, cost=4.8 NAU, latency=15s
  -> objective=0.89  ** new best **

Trial 16 (BO-guided): agent_count=2, parallel, 2 rounds, fast, one_tier_up, 0.6, 5 NAU
  -> quality=0.88, cost=6.2 NAU, latency=25s
  -> objective=0.84  (quality marginal gain, cost increase)

...

Trial 50: Convergence. Best config = Trial 15.
  Quality improvement: +0.07 (+8.75%)
  Cost reduction: -3.4 NAU (-41.5%)
  Latency reduction: -30s (-66.7%)

-> Create sandbox experiment with 10% traffic.
-> 48h later: sandbox quality=0.86, control quality=0.80, delta=+0.06 (>5% threshold).
-> Promote. Update raid_harness.yaml.
```
