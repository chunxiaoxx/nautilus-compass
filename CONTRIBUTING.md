# Contributing to nautilus-compass

Thanks for considering a contribution! Two big ways to help:

## 1. Add anchors for new domains

v0.7.1 ships **3 domain profile starters** (review by domain expert before production):
- `anchors_legal.json` — contract / litigation / fiduciary patterns
- `anchors_medical.json` — clinical reasoning / Rx / consent patterns
- `anchors_finance.json` — trading / risk / compliance patterns

Default `anchors.json` covers Chinese/English engineering+research. PRs welcome to add new domains:
- `anchors_education.json`
- `anchors_security.json` (red-team / pentest specific)
- `anchors_journalism.json`
- ...

**Selection logic** (`recall.py:_select_anchors_path()`):
1. `ZMM_ANCHORS_PROFILE=<domain>` env var (explicit)
2. `cwd` substring match (legal/contract/law → legal; medical/clinical/rx → medical; etc.)
3. Fallback `anchors.json`

⚠️ **Known limitation v0.7.1**: daemon (cold-loaded) caches one anchor profile. Switching profiles requires `bash daemon_stop.sh && ZMM_ANCHORS_PROFILE=<new> bash daemon_start.sh`. Multi-profile daemon planned for v0.8.

Each anchor file requirements:
- 25+ positive_anchors (task-shaped, not maxims — see existing file)
- 25+ negative_anchors (concrete patterns the AI should NOT slip into)
- Test it: `ZMM_EMBEDDER_MODEL=BAAI/bge-m3 python tests/eval_drift.py` should show ROC AUC ≥ 0.75

The auto-selection in `recall.py:_select_anchors_path()` picks based on `cwd`. Add your domain pattern there.

## 2. Run public benchmarks

We have first numbers on LongMemEval-S subset 12. Help us:

- Run **full LongMemEval-S 500** (estimated ~1.5h on m3 + Linux). PR the result to `RESULTS.md`.
- Run on **PerLTQA** (Chinese long-term memory benchmark). Adapter not yet written.
- Run **head-to-head with mem0** on the same dataset. Requires OpenAI/Anthropic API key.

## 3. Drift detection improvements

The 4-step evolution (0.51 → 0.92 AUC) is documented in [CHANGELOG.md](CHANGELOG.md). Open ideas:

- Tri-band output already implemented (aligned / neutral / deviation)
- **Stretch goal**: dynamic anchor weighting (recently-confirmed anchors get more weight, ebbinghaus decay)
- **Stretch goal**: PostToolUse drift (catch AI mid-action, not just at prompt time)

## Dev setup

```bash
git clone <repo>
cd nautilus-compass
pip install -e .[dev,modelscope]
python tests/run_all.sh         # full eval suite (~5 min on small-zh, ~30 min on m3)
ruff check .
```

Eval scripts read `ZMM_EMBEDDER_MODEL` env var. Set it before runs.

## Code style

- `ruff` for lint (config in `pyproject.toml`)
- Functions ideally < 50 lines, files < 500
- Comments explain *why*, not *what*
- No emojis in code (only in user-facing hook output where they convey meaning)

## License of contributions

By submitting a PR you agree your contribution is MIT-licensed. Anchors files are CC0.

We are evaluating dual-licensing under Apache 2.0 for v1.0 enterprise
self-hosting; this is undecided as of 2026-05-05. Existing contributions
remain MIT-only unless contributors opt in.

---

## v0.9 additions (2026-05-05)

The v0.8 release introduced new component domains; the same contribution
flow applies, but please mind these:

### MCP server tools (`mcp_server.py`)

When adding a new tool:
1. Add a `tool_<name>(args)` function returning `_ok(text)` or `_err(msg)`
2. Register in `TOOLS` dict with proper inputSchema (JSON Schema draft-07)
3. Add an integration test to `tests/test_compass_v09.py`
4. Bump `SERVER_VERSION` in `mcp_server.py`
5. Document in `sdk/mcp_adapter.md` and update `examples/mcp_configs/*` if needed

### A2A capabilities (`sdk/a2a_adapter.py`)

When adding a new capability:
1. Add to `CAPABILITIES` dict with input/output schema
2. Add a branch in `handle_a2a_message`
3. Add a selftest case
4. Update `sdk/a2a_adapter.py` docstring

### Drift testing (the unique requirement)

Because compass is a drift-aware system, contributions that touch
behavior/prompts/anchors must be tested for regressions:

```bash
python tests/eval_drift.py    # AUC must remain ≥ 0.85
python tests/eval_recall.py   # P@5 must remain ≥ 0.85
python tests/test_compass_v09.py  # 7 v0.9 integration tests
python sdk/a2a_adapter.py selftest
```

### Roadmap awareness

Before proposing big features, please skim:

- [paper/V10_ROADMAP.md](paper/V10_ROADMAP.md) — 12-month phase plan
- [paper/PLATFORM_FUSION.md](paper/PLATFORM_FUSION.md) — Nautilus integration
- [paper/RESULTS_v0.8.md](paper/RESULTS_v0.8.md) — current benchmark state
- [paper/V09_API_SPEC.md](paper/V09_API_SPEC.md) — server endpoint contract

If your idea fits a planned phase, mark it; if not, discuss in an issue
first to avoid parallel divergent designs.

### Provider-neutral contributions

We run on Volc Ark · Anthropic · Gemini · OpenAI · any Anthropic-compatible
endpoint. Contributions must remain provider-neutral; vendor-specific
features behind feature flags only.

### Communication

- Issues: use the templates in `.github/ISSUE_TEMPLATE/`
- PRs: use `.github/PULL_REQUEST_TEMPLATE.md`
- Discussions: GitHub Discussions
- Real-time: Nautilus platform Discord (post-launch)

