# Task 3 — mini-swe-agent / swebench scaffold API confirmation (live-tested)

> 2026-06-03 · Phase 4 · the "confirm, don't assume" spike (anchor #6). Ran live on
> the local Windows machine (Docker via WSL2 already up). Versions pinned in
> `phase3/agent-engine/benchmarks/swebench_probe/requirements.txt`.

## Installed (Windows venv `C:\Users\chunx\swebench-probe-venv`, Python 3.13)

`mini-swe-agent==2.3.0`, `swebench==4.1.0`, `datasets==4.8.5`, `anthropic==0.105.2`,
`litellm==1.87.0` (+ docker SDK, modal, openai, textual, litellm).

## Finding 1 — swebench harness is LINUX-ONLY (eval must run in WSL)

`import swebench` fails on native Windows:
```
File ".../swebench/harness/prepare_images.py", line 2, in <module>
    import resource
ModuleNotFoundError: No module named 'resource'
```
`resource` is a Unix-only stdlib module. **The official eval harness cannot run on
native Windows.** Orchestration + eval must happen in **WSL Ubuntu (Linux)**.
mini-swe-agent itself imports fine on Windows (with `PYTHONUTF8=1`, see Finding 4),
but since the harness needs Linux we run the whole pipeline in WSL.

## Finding 2 — model interface: configure litellm, do NOT write a custom Model class

The v2 `Model` protocol (`minisweagent/__init__.py`) is richer than the spike
assumed — `query`, `format_message`, `format_observation_messages`,
`get_template_vars`, `serialize`, plus a `config`. **But `minisweagent.models.
litellm_model.LitellmModel` already implements all of it.** So Task 7 collapses from
"write a 6-method adapter" to "configure the built-in LitellmModel" (anchor #5).

`LitellmModel.query(messages, **kw)` calls
`litellm.completion(model=config.model_name, messages, tools=[BASH_TOOL], **model_kwargs)`
— i.e. the v2 agent uses **native tool-calling** (a `bash` tool), not text-fenced
action parsing. Returns the choice message dict with an `extra` block carrying
parsed `actions`, the raw `response`, and `cost`.

## Finding 3 — litellm → MiniMax-M3 routing (LIVE-TESTED)

M3 is served at the Anthropic-compatible base `https://api.minimaxi.com/anthropic`
(same base our `LLMClient` uses). Three routings tested with the project's
`MINIMAX_API_KEY`:

| Route | Config | Result |
|---|---|---|
| **A ✅** | `model="anthropic/MiniMax-M3"`, `api_base="https://api.minimaxi.com/anthropic"`, `api_key=$MINIMAX_API_KEY` | returned `content='pong'` |
| B ❌ | `model="minimax/MiniMax-M3"` (litellm native provider) | 401 `invalid api key` — native provider hits a different MiniMax endpoint/auth |
| **C ✅** | route A **+ `tools=[BASH_TOOL]`** | M3 returned a real `tool_calls`: `function(name='bash', arguments='{"command":"ls"}')` |

**Decision: route A.** M3 supports native tool-calling through litellm (route C), so
the v2 agent's default tool-call loop works as-is — **no text-based model variant
needed.**

Config to give `LitellmModel`:
```python
LitellmModelConfig(
    model_name="anthropic/MiniMax-M3",
    model_kwargs={"api_base": "https://api.minimaxi.com/anthropic",
                  "api_key": os.environ["MINIMAX_API_KEY"]},
    cost_tracking="ignore_errors",   # M3 not in litellm cost registry -> would raise
)
```
(Or set `MSWEA_COST_TRACKING=ignore_errors` in the env.)

## Finding 4 — Windows console UTF-8 (only relevant if introspecting on Windows)

mini-swe-agent prints a 👋 banner at import; on a GBK (zh-CN) Windows console this
raises `UnicodeEncodeError`. Fix: `PYTHONUTF8=1` (and/or `MSWEA_SILENT_STARTUP=1`).
Irrelevant once the pipeline runs in WSL.

## Confirmed entry points (for Task 8/9 wiring)

- Batch SWE-bench runner: `minisweagent.run.benchmarks.swebench` (multi-instance).
- Single instance: `minisweagent.run.benchmarks.swebench_single`.
- Docker exec env: `minisweagent.environments.docker`.
- Official eval: `python -m swebench.harness.run_evaluation` (Linux/WSL only).

## Remaining cloud-setup steps (next, in WSL)

1. Python 3.11+ in WSL Ubuntu-20.04 (ships 3.8) — `uv` standalone or deadsnakes PPA.
2. Confirm `docker` CLI works inside WSL (Docker Desktop WSL integration for
   Ubuntu-20.04).
3. `pip install` the pinned set in the WSL 3.11 env; confirm `import swebench` OK.
4. Drive `minisweagent.run.benchmarks.swebench` with the route-A LitellmModel over
   the N=110 subset (start: 5 for Probe 0) → predictions JSONL → official eval.
5. `BudgetedModel` (Task 6) wraps `LitellmModel.query` for the matched-budget cap —
   thin wiring (read token cost from the returned `extra`/usage).

## Open risks

- Per-instance token budget: `LitellmModel` does cost($), not a hard token cap;
  our `BudgetedModel` adds the token cap but must read M3's usage from the litellm
  response (`response.usage`) — verify the field is populated for route A.
- mini-swe-agent's swebench runner expects a Docker image per instance; confirm it
  uses the same images the official harness builds (`--cache_level env`).
