# Probe 0 milestone — agent integration end-to-end PROVEN (predictions side)

> 2026-06-03 · Phase 4 · live result on the local machine.

## What works (live-validated)

Ran mini-swe-agent on **Windows** against a real SWE-bench-Lite instance and got a
real patch from MiniMax-M3:

- Instance: `pallets__flask-4045` (from the locked ≥2-hunk core subset).
- Exit status: **Submitted** (agent completed the task), 6m53s.
- Output `model_patch`: 1503 chars, a coherent diff modifying `src/flask/blueprints.py`.
- The full chain works: **M3 via litellm (native tool-calls)** → mini-swe-agent loop
  → bash executed **inside the SWE-bench Docker container** → patch extracted →
  `preds.json` written.

This validates the expensive integration: route A (`anthropic/MiniMax-M3` + api_base)
with tool-calling drives the v2 agent against real Docker instances.

## The working invocation (Windows)

```powershell
$env:ANTHROPIC_API_KEY = <MINIMAX_API_KEY>   # litellm anthropic provider reads this
$env:PYTHONUTF8 = "1"                          # GBK console emoji-banner fix
$env:MSWEA_COST_TRACKING = "ignore_errors"     # M3 not in litellm cost registry
$env:MSWEA_SILENT_STARTUP = "1"
python -m minisweagent.run.benchmarks.swebench `
  --subset princeton-nlp/SWE-bench_Lite --split test `
  --filter "(pallets__flask-4045)" -o <out> -w 1 `
  -m "anthropic/MiniMax-M3" -c swebench.yaml `
  -c model.cost_tracking=ignore_errors `
  -c "model.model_kwargs.api_base=https://api.minimaxi.com/anthropic"
```

Key operational notes:
- **Pre-pull the instance image first** (`docker pull docker.io/swebench/
  sweb.eval.x86_64.<id>:latest`, `__`→`_1776_`, lowercased). mini-swe-agent's
  `docker run` has a 120s timeout; first-pull of a ~3.8 GB image exceeds it. Pre-pulled
  → `docker run` starts instantly. (flask-4045 image = 3.78 GB, ~1m47s pull.)
- Output is `<out>/preds.json` = a JSON **dict** `{id: {instance_id, model_patch,
  model_name_or_path}}`. Convert its `.values()` to JSONL with our `predictions.py`
  (Task 5) for the official harness.

## Official eval scoring — SOLVED via a Docker container (NOT WSL)

The official `swebench.harness.run_evaluation` is **Linux-only** (`import resource`,
Finding 1). The obvious host — WSL — is a **dead end on this machine**: the Windows
proxy is `127.0.0.1:52888` (loopback-only, xray under v2rayN), the machine has no
direct egress, and WSL (even `networkingMode=mirrored` + `hostAddressLoopback=true` +
a host firewall allow-rule) **cannot reach the Windows host on any port** — a mirrored-
mode Linux→host connectivity limitation on Win11 22H2. Verified: a relay bound to
`0.0.0.0:52889` is reachable **from Windows (HTTP 200)** but **not from WSL (HTTP 000)**.

**The working path: run the eval inside a Docker container.** Docker Desktop containers
*can* reach the host gateway (`host.docker.internal`), unlike WSL. So:

1. A tiny user-space TCP relay (`swebench-probe-run/proxy_relay.py`, no admin) bridges
   `0.0.0.0:52889 → 127.0.0.1:52888` (the loopback-only xray proxy).
2. A host firewall inbound-allow rule for 52889 (one-time, admin).
3. The eval runs in a `python:3.11` container with the docker socket mounted (to spawn
   sibling instance containers) and `HTTP(S)_PROXY=http://host.docker.internal:52889`:
   ```
   docker run --rm \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v <preds_dir>:/work \
     -e HTTP_PROXY=http://host.docker.internal:52889 \
     -e HTTPS_PROXY=http://host.docker.internal:52889 \
     -e NO_PROXY=host.docker.internal,localhost,127.0.0.1 \
     python:3.11 bash -lc "pip install -q swebench && cd /work && \
       python -m swebench.harness.run_evaluation --predictions_path preds.jsonl \
         --dataset_name princeton-nlp/SWE-bench_Lite --instance_ids <id> \
         --run_id probe0 --cache_level env --clean true"
   ```
   Container→relay→xray→internet tested HTTP 200; HF dataset download + Docker test
   execution work; the harness spawns instance containers via the mounted socket.

### RESULT — Probe 0 baseline = 1/5 resolved (20%), SANE ✓

Arm 1 (mono/generic, MiniMax-M3) on 5 light-repo ≥2-hunk core-subset instances,
scored by the official harness (`probe0_result.json`):

```
submitted 5 · completed 5 · resolved 1 · unresolved 4 · empty_patch 0 · errors 0
resolved:   pallets__flask-4045
unresolved: pallets__flask-4992, pallets__flask-5063, psf__requests-2148, psf__requests-2317
```

**Sane baseline confirmed.** 1/5 (20%) for a *minimal* scaffold (mini-swe-agent) + a
mid-tier model (M3) on ≥2-hunk Lite instances is plausible vs published Lite numbers
(strong agent+model setups reach ~40-60%); it is non-zero (wiring works, all 5 produced
real patches) and not suspiciously high (no leak). **The full Probe 0 apparatus is
proven end-to-end** (M3 → mini-swe-agent → Docker → patch → official harness →
externally-verified resolve verdict) and the baseline is sane — Probe 0's purpose
(design §6.1) is satisfied. Next: Probe 1 (arm 1 vs arm 3 decomp).

## Status

- Probe 0 **apparatus = PROVEN end-to-end** (agent + official eval, 1/1 resolved).
- The other 4 light-repo subset instances (flask-4992/5063, requests-2148/2317) are
  mechanically identical (pre-pull image → agent → eval); being run to get a 5-instance
  baseline resolve rate.
- **Standing infra for re-runs:** keep `proxy_relay.py` running (host) + the 52889
  firewall rule. Agent on Windows venv (`C:\Users\chunx\swebench-probe-venv`), eval in
  the python:3.11 container with the socket + relay-proxy as above.
- `.wslconfig` was bumped to 24GB/8core + mirrored networking (backup
  `.wslconfig.bak-20260603`); WSL ended up unused for the eval — can be reverted.
