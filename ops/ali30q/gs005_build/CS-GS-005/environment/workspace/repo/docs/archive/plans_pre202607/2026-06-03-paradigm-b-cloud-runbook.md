# Cloud Runbook — Paradigm B Probe 0/1 (SWE-bench-Lite)

> Phase 4. Covers Task 3 (vendor + confirm scaffold API) and Task 9 (official
> harness eval). **This is the only part that needs Docker / a cloud VM** — all of
> Phase A (escape-noise stats, subset loader, predictions writer, budget
> accountant) is already built and unit-tested locally on master.
>
> ⚠️ **Do NOT run this on the production soul/platform VM.** The SWE-bench Docker
> eval can pull ~tens of GB of images and, under the wrong cache level, exhaust
> disk (≈2 TB). A disk-full event on the production box would take down the
> platform backend. Use a **dedicated** VM, or the managed Modal/sb-cli path.

## 0. Provisioning preconditions (what must exist before step 1)

- **Dedicated x86_64 Linux VM** (Ubuntu 22.04+): **8+ vCPU, 16+ GB RAM, ≥120 GB
  free disk**. (Design §7 spike sizing; Lite has only 6 repos so `--cache_level=env`
  pulls few images.)
- **Docker** installed and running; the run user in the `docker` group
  (`docker run hello-world` works without sudo).
- **Python 3.11+** and `pip`, a fresh venv.
- **Network egress** to: huggingface.co (dataset), `api.minimaxi.com` (M3),
  pypi.org + github.com (install + repo clones during eval).
- **`MINIMAX_API_KEY`** exported in the run shell (the same M3 key the project
  already uses; `LLMClient` reads `MINIMAX_API_KEY`).
- Decide the **eval backend** (see §4): local Docker (default), Modal, or sb-cli.

## 1. Install + pin (Task 3)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -U pip
pip install mini-swe-agent swebench datasets anthropic
pip freeze | grep -Ei 'mini-swe-agent|swebench|datasets|anthropic' \
  > phase3/agent-engine/benchmarks/swebench_probe/requirements.txt
```

## 2. Confirm the scaffold model API (Task 3 — DO NOT skip; do not assume)

The Phase-A `M3Model` adapter (Task 7) is intentionally NOT written yet because it
must match `mini-swe-agent`'s real model contract, not an assumed one. Confirm and
record into `NOTES_scaffold_api.md`:

```bash
python - <<'PY'
import inspect, mini_swe_agent as m, pkgutil
print("mini_swe_agent at:", m.__file__)
for mod in pkgutil.walk_packages(m.__path__, m.__name__ + "."):
    if any(k in mod.name.lower() for k in ("model", "swebench", "agent", "run")):
        print(mod.name)
PY
```

Then read the model module + the SWE-bench batch entry point and write down:
1. The exact method the scaffold calls on a model — name, signature, return shape
   (spike expects a duck-typed `query(messages) -> {"content": str, ...}`).
2. How step / cost caps are configured (native caps are steps/$, not tokens — our
   `BudgetedModel` adds the strict token cap on top).
3. The SWE-bench run command, where it reads the dataset, where it writes
   predictions (a `{instance_id, model_patch, model_name_or_path}` JSONL — the
   format `predictions.py` already emits).

> **Gate:** if the model is NOT cleanly injectable without editing scaffold source,
> STOP and report — that breaks the single-scaffold arm-isolation argument (design
> §7) and the plan needs revisiting before Task 7/8.

## 3. Build remaining code against the CONFIRMED API (back to local TDD)

With §2's findings, Task 7 (`model_adapter.py`) and Task 8 (`run_arm.py`) become
local TDD tasks again (fakes shaped like the real contract). Only the actual
*runs* (steps 4–5) need the VM.

## 4. Eval backend — pick one

- **Local Docker (default, spike-validated):**
  ```bash
  python -m swebench.harness.run_evaluation \
    --predictions_path preds_probe0.jsonl \
    --dataset_name princeton-nlp/SWE-bench_Lite \
    --max_workers 4 --run_id probe0 --cache_level env --clean true
  ```
  **Never `--cache_level instance`** (≈2 TB). `env` + `--clean true` keeps disk
  bounded. Watch `df -h` during the first run.
- **Modal (no local Docker):** add `--modal true` — needs a Modal account + token.
- **sb-cli (managed eval service):** needs an sb-cli API key. Good if the VM can't
  run Docker.

## 5. Probe 0 smoke → Probe 1

1. `probe0_smoke.py` (Task 9): first 5 subset ids → arm1 (mono/generic) → write
   `preds_probe0.jsonl` → run §4 eval → record `resolved` count + report path.
   **Verify (not "done" until checked):** a sane >0/5 resolved with well-formed
   lines; 0/5 with empty patches = broken agent/model wiring → debug before Probe 1.
2. Probe 1 (Tasks 10/11): arm1 vs arm3 over the full N=110, matched budget, 1–2
   seeds on M3 → eval both (distinct `--run_id`) → feed booleans into
   `aggregate_paired_multiseed(..., "baseline", "treatment")` → `escapes_noise`
   verdict. Report matched-budget (headline) AND natural-budget figures.

## 6. Cost / disk guardrails

- Token spend: `BudgetedModel` caps per instance; total ≈ N × per-instance cap ×
  arms × seeds. Probe 0 = 5 instances, tiny. Estimate before the N=110 Probe 1 run.
- Disk: `docker system df` before/after; `docker system prune` between runs if
  needed. Abort if free disk drops below ~20 GB.
- Time: design §7 — a 30–60 instance Lite subset runs in well under an hour of test
  time at `--max_workers 4`.
```
