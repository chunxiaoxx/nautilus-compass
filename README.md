# nautilus-compass

<!-- mcp-name: io.github.chunxiaoxx/nautilus-compass -->

> **Open-source memory & reliability layer for AI agents.**
> Long-term memory that now **beats mem0 on all three LongMemEval-S metrics**
> while staying fully local & 14× cheaper — plus drift detection and
> cross-agent contracts that no other memory layer ships.
>
> Plugin for Claude Code / Desktop · Cline · Cursor · Continue.dev · Zed ·
> any MCP client.
>
> **Built by [Nautilus Platform](https://nautilus.social)** · open agent ecosystem · [join as agent →](https://nautilus.social)

🇬🇧 English (this file) · [🇨🇳 中文](README.zh-CN.md)

[![CI](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/ci.yml)
[![arXiv build](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/build-paper.yml/badge.svg?branch=main)](https://github.com/chunxiaoxx/nautilus-compass/actions/workflows/build-paper.yml)
[![LongMemEval-S](https://img.shields.io/badge/LongMemEval--S-full500%20P%405%2097.8%25%20%C2%B7%20vs%20mem0%2091.6%25-brightgreen)](docs/evidence/headhead_mem0_full500_20260826.json)
[![EverMemBench](https://img.shields.io/badge/EverMemBench-44.4%E2%80%9347.3%25-brightgreen)](paper/sections/paper2_06_5_evermembench.tex)
[![drift-AUC](https://img.shields.io/badge/drift_AUC-0.83_held--out-brightgreen)](#how-it-works)
[![PyPI](https://img.shields.io/pypi/v/nautilus-compass?label=PyPI&color=blue)](https://pypi.org/project/nautilus-compass/)
[![MCP](https://img.shields.io/badge/MCP-17%20tools%20%C2%B7%20TLS%20%C2%B7%20RBAC-blue)](docs/mcp-usage.md)
[![A2A](https://img.shields.io/badge/A2A-mTLS%20%C2%B7%20scoped%20peers-blue)](examples/a2a_tls_demo.py)
[![license](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## What this is (2026-08 state)

Three pillars, one plugin:

**1 · Black-box long-term memory — now with SOTA retrieval.**
Raw text embedded locally with BGE-m3. No extraction LLM at ingest, no graph,
no data leaving your machine. In Aug 2026 we added **utterance-routed chunk
retrieval**: single-session and knowledge-update questions route to
turn-window chunks (the answer usually lives in ONE user turn; whole-session
embedding dilutes it), everything else uses session-level hybrid
(BM25 + dense RRF). Result on LongMemEval-S full 500 questions,
same-question head-to-head vs mem0 2.0.19 (both sides `infer=False`,
our reproduction):

| LongMemEval-S · n=500 | P@1 | P@5 | MRR |
|---|---|---|---|
| **compass** | **0.890** | **0.978** | **0.929** |
| mem0 2.0.19 | 0.774 | 0.916 | 0.834 |

The same utterance ammo overtakes mem0 **on its own home benchmark**
(LOCOMO-10, n=1986: 0.644 / 0.890 vs 0.592 / 0.802) and fixes the
single-session collapse on LongMemEval-M (0.20 → 1.00). Full evidence chain
with per-type breakdowns and every config flag:
[`docs/evidence/headhead_mem0_full500_20260826.json`](docs/evidence/headhead_mem0_full500_20260826.json)
— including the experiments that failed (cross-encoder reranking *hurts* on
this corpus; candidate-pool K is a no-op; Qwen3-0.6B swap is a wash).

**2 · Drift detection — the half nobody else solves.**
Memory recalled doesn't stop the AI from breaking the rule *this time*.
compass scores every prompt against an anchor set of real failure patterns
(25 positive + 35 negative) before the agent acts. AUC 0.83 held-out,
p95 latency <50 ms, fire rate 0.5% in production traffic. White-box layers
abstract prompts into facts before drift becomes checkable — structurally
out of their reach.

**3 · Cross-agent contracts + governance.**
When you run multiple agents (or multiple Claude dialogs) on shared files,
compass derives implicit contracts from handoff files, tracks closure, and
audits for fake-closure / red drift. A 4-dialog 28-hour field study lives in
[`docs/case_study_4dialog_compass.md`](docs/case_study_4dialog_compass.md).

**The trade that flipped**: earlier versions traded −30 points on
LongMemEval-S for local deployment and cost. As of 2026-08 there is no trade
— full sweep at 1/14 the reproduction cost (~$3.50 per 500 questions vs
$50+ for GPT-4o-judged stacks). Full argument:
[paper/BLACKBOX_VS_WHITEBOX.md](paper/BLACKBOX_VS_WHITEBOX.md).

---

## Quickstart

### 30 seconds (any machine with ssh access to your dev box)

```bash
bash ~/.claude/plugins/nautilus-compass/ops/agent_quickstart.sh my-agent
```

Generates a scoped token, wires the cloud MCP bridge, writes `.mcp.json`,
and runs an end-to-end self-check. Add `--hud` to install the fused status
line (live recall hit-counter 🧠, drift state, 5-min traffic).

### Claude Code / Desktop (manual, local daemon)

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass ~/.claude/plugins/nautilus-compass
bash ~/.claude/plugins/nautilus-compass/install.sh

# start the BGE-m3 daemon (one-time per boot)
bash ~/.claude/plugins/nautilus-compass/daemon_start.sh
```

The installer wires three hooks into `~/.claude/settings.json`:
- `UserPromptSubmit` → time-bucketed memory recall + drift check
- `PostToolUse` → mid-session writer
- `Stop` → end-of-session summary (writes a session battle-report to
  `~/.claude/.cache/compass-last-session.txt`)

Slash commands: `/compass-verify` · `/compass-drift` · `/compass-recall` ·
`/compass-search` · `/compass-status`.

### Any other MCP client

```bash
python ~/.claude/plugins/nautilus-compass/scripts/install_to_agent.py
```

Auto-detects Claude Desktop, Cursor, Cline, Continue.dev, Zed and patches
their MCP config. Per-agent copy-paste configs:
[`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) · raw protocol:
[`docs/mcp-usage.md`](docs/mcp-usage.md).

### Cloud-hosted (no local install)

```bash
curl https://compass.nautilus.social/.well-known/agent.json   # A2A discovery
```

Sign up at `compass.nautilus.social/signup` for a hosted gateway with
multi-user sync, audit log, and managed BGE-m3.

---

## Headline numbers

| Benchmark | Score | Honest compare |
|---|---|---|
| **LongMemEval-S 500q full** (utt-routed + hybrid, n=500) | **P@1 0.890 · P@5 0.978 · MRR 0.929** | sweeps mem0 2.0.19 (0.774/0.916/0.834, our reproduction): +11.6/+6.2/+9.5pt. Largest flip: single-session-user P@1 0.90 vs 0.49 |
| **LOCOMO-10** (n=1986 · mem0's home benchmark) | **P@1 0.644 · P@5 0.890 · MRR 0.740** | overtakes mem0 (0.592/0.802/0.677, our reproduction) +5.2/+8.8pt |
| **LongMemEval-M 500q full** (~501 sessions/question) | **P@5 0.888** | 12x larger session pools cost only 9pt vs S500; ssu collapse fixed at n=500 (0.20 → 0.93); ssp 0.53 newly exposed; no mem0 M head-to-head yet |
| **EverMemBench-Dynamic** (n=500) | **44.4% (Run 1) / 47.3% (Run 2)** | tops the four published Table 4 baselines (Mem0 37.09, Zep 39.97, MemOS 42.55, MemoBase 34.27). Not claiming "industry SOTA" — OMEGA / Mem0g haven't reported publicly |
| **LongMemEval-S e2e** | 30q paired: **56.7% vs 26.7% baseline (+30pt, 2.13x)** — context fix (typed utterance context + anchor_all); v0.8 full500: 56.6% (locked, deepseek subject) | retrieval P@5 97.8%; remaining gap = reader LLM, tr-type e2e still 0 (next lever) |
| **Drift detector AUC** | **0.83 held-out / 0.92 in-set** | only public memory layer doing drift detection at all |
| **Reproduction cost** | **~$3.50** / 500 questions | ~14× cheaper than GPT-4o-judged stacks |
| **p95 hook latency** | **<50 ms** | safe for every-prompt invocation |

We deliberately report Run 1 (44.4%) as the EverMemBench headline to avoid
cherry-picking; cross-run mean 45.84% clears MemOS by +3.3pt. Dual-run +
Gemini cross-judge sensitivity analysis:
[`paper/sections/paper2_06_5_evermembench.tex`](paper/sections/paper2_06_5_evermembench.tex).

**Try it without installing**: live drift-detection + Merkle-integrity demo
at [huggingface.co/spaces/chunxiaox/nautilus-compass](https://huggingface.co/spaces/chunxiaox/nautilus-compass)
(CPU only · metadata-mode jaccard fallback · no signup).

**Reproduce the numbers** — eval dataset (behavioral anchors + labeled
traces + LongMemEval-S / EverMemBench scoring) on the Hub:
[huggingface.co/datasets/chunxiaox/nautilus-compass-test-data](https://huggingface.co/datasets/chunxiaox/nautilus-compass-test-data)

```python
from datasets import load_dataset
ds = load_dataset("chunxiaox/nautilus-compass-test-data")
```

Benchmark entrypoint: `bash ops/bench_all.sh l0` (fast layer, no GPU) ·
`bash ops/bench_all.sh l1 30` (LongMemEval subset). Retrieval levers are
env-switched in `tests/eval_longmemeval_accuracy.py`
(`ZMM_UTTERANCE_RETRIEVE` / `ZMM_UTTERANCE_TYPES` / `ZMM_HYBRID` /
`ZMM_RETRIEVE_K` / `ZMM_DATE_ANCHOR` / `ZMM_EMBED_CACHE`).

---

## How it works

```
            User prompt: "Fix bug X for me"
                         │
                         ▼
       ┌─────────────────────────────────────┐
       │  UserPromptSubmit Hook (this plugin)│
       └─────────────────────────────────────┘
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
       ┌────────┐  ┌─────────┐  ┌──────────┐
       │ recall │  │  drift  │  │ profile  │
       │ memory │  │  check  │  │ aggregate│
       └────────┘  └─────────┘  └──────────┘
                         │
                         ▼
       Hooks inject results into Claude's system prompt:
       - Time-bucketed past memory (BGE-m3 semantic + keyword hybrid)
       - Drift score + nearest negative anchor (if score < threshold)
       - Profile facts ("you have 3 unfinished tasks in this repo")
                         │
                         ▼
            Claude answers — with full context loaded
```

Drift detector: each prompt vs anchor set (real failure transcripts),
BGE-m3 cosine. AUC 0.83 held-out.

---

## What's exposed (MCP tools)

**17 tools** — core seven:

| Tool | Purpose | Latency (local daemon) |
|---|---|---|
| `ingest_obs(name, body, agent_id?)` | Write observation with auto-anchor + drift signal | ~150 ms |
| `recall(query, project?, top_k?)` | BGE-m3 semantic + keyword hybrid search | ~200 ms |
| `session_search(query, since?)` | Time-bucketed session-log search | ~80 ms |
| `profile(user_id?)` | Work-profile aggregate (topics, agents, drift trend) | ~100 ms |
| `drift_check(prompt, project?)` | Black-box drift score against anchors | <50 ms |
| `drift_history(since?, agent_id?)` | Drift score timeline for trend audit | ~30 ms |
| `feedback_log(direction, reason)` | Log positive/negative anchor signal | <20 ms |

> Latencies are local-daemon figures. Over the public HTTPS MCP endpoint
> (`https://compass.nautilus.social/mcp/`) add TLS + WAN round-trip:
> measured p50 ≈ 0.9–1.7 s per call (2026-08-28 field test).

Plus: `thread_recall` · `proof_of_impact` · `long_task` · platform bridge
(`submit_platform_task` / `ingest_platform_task_result`) · governance
(`governance_dispatch` / `governance_audit` / `governance_lock_check` ·
`governance_plan`) · `add_worker`. JSON-RPC 2.0 over stdio / TCP / TLS / mTLS;
`notifications/*`, `logging/setLevel`, `resources/*` spec-complete.
Full guide: [`docs/mcp-usage.md`](docs/mcp-usage.md).

### Token scopes (v2.3.1)

Tokens are scoped, not global. `ops/compass_token_admin.py grant <agent>
--scopes read:<project>,write:<project>` issues a least-privilege token;
`read:*` (all-project recall, incl. `scope=user`) requires an explicit
`--yes-i-want-star`. The HTTP server enforces scopes per call (fail-closed);
legacy list-format tokens map to full access for backward compatibility.
The quickstart script signs **read-only, current-project** tokens by default.

---

## Comparison

| Capability | this | mem0 | Letta | Zep | claude-mem | MemOS | Smriti |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Cross-agent memory | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | archive-only |
| MCP A2A protocol native | ✅ TLS+mTLS+RBAC | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Drift detection | ✅ AUC 0.83 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Merkle integrity audit log | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| LongMemEval-S retrieval (500q head-to-head) | ✅ **0.890 / 0.978 / 0.929** | 0.774 / 0.916 / 0.834 (our reproduction) | n/r | n/r | n/r | ❌ | ❌ |
| LOCOMO-10 retrieval (n=1986) | ✅ **0.644 / 0.890 / 0.740** | 0.592 / 0.802 / 0.677 (our reproduction) | n/r | n/r | n/r | n/r | n/r |
| EverMemBench verified | ✅ 44.4-47.3% | 37.09 | n/r | 39.97 | n/r | 42.55 | ❌ |
| LongMemEval-S e2e (their own harness) | 30q paired 56.7% (+30pt after context fix; 500q re-run queued) | 94.4% (self-reported) | n/r | n/r | n/r | n/r | n/r |

*2026 newcomers not yet same-machine reproduced by us: Hindsight, Supermemory (self-reports LongMemEval SOTA), Cognee, LangMem, Membase — rows pending; their published numbers use their own harnesses and are not directly comparable to our head-to-head protocol.*
| Self-host + hosted both | ✅ | ☁ only | ✅ | ☁ only | ✅ | OSS only | OSS only |
| License | MIT | Apache | Apache | proprietary | MIT | Apache | MIT |

`n/r` = not reported in their published evaluations. Smriti is a team
conversation archive — different scope, listed for completeness.

---

## Case study · 4-dialog OSS multi-agent reliability

28 hours, four Claude Code dialogs on shared filesystem protocols:
drift fired 314×/7d (act-on rate instrumented), contract
`cnt_compass_soul_sub_a1` closed in 17.92h vs 6d21h budget, 13 plan-dup
audits saved ~40-50h, first cross-dialog L4 fire settled 50 NAU. Field log
+ 7 generalizable patterns:
[`docs/case_study_4dialog_compass.md`](docs/case_study_4dialog_compass.md).

---

## Advanced (opt-in surface)

<details>
<summary><b>Drift loop closure · act-on rate</b></summary>

Every fired alert gets a stable `alert_id` in
`.cache/drift_mitigation_log.jsonl`. Acknowledge via
`feedback.py log <alert_id> fp|tp`; `audit_kpi.py` reports
`act_on_rate(window_hours)` (target ≥0.70; <0.30 = cry-wolf → raise
threshold or retrain anchors).

```python
from audit_kpi import act_on_rate
m = act_on_rate(window_hours=168)
assert m["rate"] >= 0.70
```
</details>

<details>
<summary><b>v3 opt-in LLM switches (all default-off, byte-equal promise)</b></summary>

With no opt-in env set, daemon behavior is byte-equal to v2.0.1 — gated by
`tests/test_llm_opt_in.py` on every PR.

| env var | tier | feature |
|---|---|---|
| `COMPASS_USE_LLM_RESOLVE` | 1 (session-end) | LLM contradiction resolution |
| `COMPASS_USE_LLM_VERIFY` | 4 (runtime) | anti-confabulation cite-or-refuse |
| `COMPASS_USE_LLM_DRIFT_PAY` | 4 (runtime) | drift × outcome anchor feedback |
| `COMPASS_USE_LLM_REFLECT` | 3 (periodic) | self-reflection semantic emit |
| `COMPASS_USE_LLM_ECON` | 4 (runtime) | memory-as-economy NAU budget |

Deterministic v3 surface (always on): typed knowledge graph layer (NO-OP
until built), confidence scoring + contradiction hook, `MEMORY_REPORT.md`
auto-gen, `implementation_notes` frontmatter. Registry: [`llm_opt_in.py`](llm_opt_in.py).
</details>

<details>
<summary><b>Platform integration · BP1/BP3 + V7 governance</b></summary>

OSS↔platform bridge without a new HTTP server:
`submit_platform_task` (compass → platform queue, file-based or HTTP when
`COMPASS_PLATFORM_QUEUE_URL` is set) · `ingest_platform_task_result`
(platform → compass, searchable via `recall`). Round-trip demo:
`python examples/platform_flywheel_demo.py`.

V7 governance (multi-executor deployments): `governance_dispatch`
(decompose 1 task → N routed sub-tasks) · `governance_audit` (fake-closure /
red-drift scan) · `governance_lock_check` (SHA256 lock on the L0 core).
Demo: `python examples/v7_governance_demo.py`. Contract details:
[`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md).
</details>

<details>
<summary><b>Release history · v3.0.0 / v2.1.0 / v2.0.0</b></summary>

**v3.0.0 · "from memory library to evolution engine"** — same system closing
the loop: memories feed a **extract fuel → external verdict → distill**
cycle. Semantic-recall revival (Windows torch long-path fix), GOAL-SSOT
ledger + hourly heartbeat, cloud capacity root-cause fixes (load 10-14 →
1.x), daemon atomic pkl + per-project locks, paired-control evidence
(tribal-fact retrieval 0/3 → 3/3), fused HUD, 30-second quickstart.

**v2.1.0 · drift v2 + line reconciliation** — cry-wolf fix (fire rate
64.5% → 0.5% via rule-hit OR drift_score < −0.07), cross-agent contract
scanner (L4 substrate), L3 tier promotion + PoI, daemon hardening
(bounded pools, in-flight semaphore, BM25+vector RRF opt-in).

**v2.0.0 · Opinionated EvoMap** — deterministic lifecycle layer on the
black-box base. No LLM at ingest / tier promotion / forgetting; no vendoring
of GBrain/OpenViking; no graph rerank for closed haystacks (cost −6.2pt in
v0.8 — [`paper/RESULTS_v0.8.md`](paper/RESULTS_v0.8.md)).

Full notes: [`CHANGELOG.md`](CHANGELOG.md) · release:
[`v3.0.0`](https://github.com/chunxiaoxx/nautilus-compass/releases/tag/v3.0.0)
</details>

---

## Documentation

- [`docs/AGENT_ONBOARDING.md`](docs/AGENT_ONBOARDING.md) — per-agent install configs (6 platforms + 3 frameworks)
- [`docs/mcp-usage.md`](docs/mcp-usage.md) — raw MCP protocol guide, TLS setup, RBAC
- [`docs/PLATFORM_HANDSHAKE.md`](docs/PLATFORM_HANDSHAKE.md) — OSS↔SaaS coordination contract
- [`docs/evidence/`](docs/evidence/) — raw benchmark evidence files (JSON, per-question rows)
- [`paper/`](paper/) — two papers (drift detection + memory pipeline) and eval scripts
- [`ops/GPU_EVAL_RECIPE_4090.md`](ops/GPU_EVAL_RECIPE_4090.md) — 12-minute rented-GPU benchmark recipe
- [`CHANGELOG.md`](CHANGELOG.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md)

---

## Citation

**Paper 1 · drift detection**:

```bibtex
@misc{nautiluscompass-drift-2026,
  title  = {Nautilus Compass: Black-box Persona Drift Detection
            for Production LLM Agents},
  author = {Chunxiao Wang},
  year   = {2026},
  note   = {Yiluo Technology Co., Ltd.},
  howpublished = {\url{https://github.com/chunxiaoxx/nautilus-compass}}
}
```

**Paper 2 · memory pipeline + EverMemBench cross-bench**:

```bibtex
@misc{nautiluscompass-memrecall-2026,
  title  = {Closing the Memory Recall Gap with Chinese LLMs:
            A Multi-Stage Retrieval Pipeline Achieving Zep-SOTA Performance
            on LongMemEval-S at 1/15 Cost},
  author = {Chunxiao Wang},
  year   = {2026},
  note   = {Yiluo Technology Co., Ltd.},
  howpublished = {\url{https://github.com/chunxiaoxx/nautilus-compass}}
}
```

Prior work we build on (cite as appropriate): BGE-m3 / BGE-Reranker
(BAAI 2024) · Persona Vectors (Anthropic, [arXiv:2507.21509](https://arxiv.org/abs/2507.21509),
complementary white-box) · DPT-Agent ([arXiv:2502.11882](https://arxiv.org/abs/2502.11882)) ·
A-MEM ([arXiv:2502.12110](https://arxiv.org/abs/2502.12110)) ·
LongMemEval (Wu et al., NeurIPS 2024) · EverMemBench (Hu et al., 2026).

---

## License

- **Code, plugin, MCP wrapper, papers, scripts** — MIT ([`LICENSE`](LICENSE))
- **Behavioral anchor files** (`anchors*.json`) — CC0 1.0 Universal ([`LICENSE-ANCHORS`](LICENSE-ANCHORS))

---

## Star history

[![Star History Chart](https://api.star-history.com/svg?repos=chunxiaoxx/nautilus-compass&type=Date)](https://star-history.com/#chunxiaoxx/nautilus-compass&Date)

## Contributors

<a href="https://github.com/chunxiaoxx/nautilus-compass/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=chunxiaoxx/nautilus-compass" alt="Contributors" />
</a>

PRs welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Contact

- **Author**: Chunxiao Wang · Yiluo Technology Co., Ltd. · `chunxiaoxx@gmail.com`
- **Issues**: [github.com/chunxiaoxx/nautilus-compass/issues](https://github.com/chunxiaoxx/nautilus-compass/issues)
- **Hosted gateway**: [compass.nautilus.social](https://compass.nautilus.social)
- **中文文档**: [README.zh-CN.md](README.zh-CN.md)
