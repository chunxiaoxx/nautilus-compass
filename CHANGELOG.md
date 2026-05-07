# Changelog

## [0.9.5] · 2026-05-06 — "production-validated · A2A live · cross-benchmark"

Production hardening + A2A v1 protocol surface + EverMemBench cross-validation.

### 🎯 Highlights

- 🌐 **A2A v1 Protocol live in production** · ext https://compass.nautilus.social
  - GET `/.well-known/agent.json` · 5-capability discovery · OAuth2 + MCP advertise
  - POST `/a2a/messages` · envelope dispatcher · maps to REST + bearer
  - HTTP 200 verified ext (TLS · nginx · 67-320ms)
- 🛡️ **Audit log Stage 0+1 deployed** · prod hardened against high-frequency events
  - login + oauth.token 1/10 sampling · signup 100% audit
  - async deque + 5s background flusher · 0 lock contention
  - VACUUM in retention cron (Stage 0 disk reclaim)
- 📊 **Stress benchmark · 1M rows · p95 7ms** (50× under 100ms threshold)
  - Postgres switch trigger raised 100K → 5M rows (real benchmark · not heuristic)
- 📈 **Cross-benchmark on EverMemBench-Dynamic** · paper §6.5 final (n=500)
  - First independent benchmark filling EverCore omission gap
  - BM25 lower-bound (free): R@1 14.8 / R@5 25.2 / R@20 38.1
  - **compass full stack (BGE-m3 + bge-reranker-v2-m3 + V4-flash):**
    **recall@20 94.8% · e2e 41.0% on n=500 (5 topics)**
  - Position vs paper Table 4 baselines: Zep 39.97 → **compass 41.00** → MemOS 42.55
  - Per-topic CV 6% · paper-defensible
- 🔬 **Cross-judge replication final** · n=500 · κ 0.772 · 88.6% agreement
  - DeepSeek V3.2 self-judge 56.6% · GLM-5.1 cross-judge 54.0% · Δ -2.6 (Good)

### Added

- A2A v1 protocol endpoints in `compass_http_v09.py` (+162 lines)
- `init_audit_table()` + `write_audit()` async deque + flusher
- `/v1/audit_log` self-export · GDPR delete/cancel/export endpoints
- `paper/AUDIT_PARTITION_SPEC.md` revised with real stress numbers
- `paper/sections/paper2_06_5_evermembench.tex` cross-benchmark (189 LOC · 4 tables)
- `scripts/stress_audit.sh` 4-scale benchmark
- `scripts/evermembench_smoke.py` BM25 R@K (free)
- `scripts/evermembench_e2e.py` BM25 + LLM e2e (~$0.10/100 QAs)
- `ops/prometheus_alerts.yml` 6 alerts
- `paper/REAL_USER_ONBOARDING.md` OpenClaw priority playbook
- `package.json` + `bin/compass-mcp.js` npm wrapper
- `tools/cross_judge_analysis.py` cross-judge κ analysis tool

### Changed

- nginx: + `/a2a/` + `/.well-known/agent.json` + `/metrics` location blocks
- AUDIT_PARTITION_SPEC trigger: 100K → 5M rows (data-driven)
- `paper2_03_method.tex` 9 hedge edits (over-claim → empirical)
- `paper2_appendix_crossjudge.tex` filled with real κ data
- `landing/index.html` v1.0 design · Nautilus dark theme

### Production verified (ext https://compass.nautilus.social)

- ✅ /healthz · 1281 req/s · p95 125ms
- ✅ /.well-known/agent.json · 200 (320ms · TLS)
- ✅ /a2a/messages · 200 (envelope reply)
- ✅ /metrics · Prometheus scrape-ready
- ✅ Self-heal: kill -9 → systemd restart 12s
- ✅ Live metrics: 305 users · 305 audit_events_24h · 0 drift_red

### Self-criticism

- 30-QA EverMemBench smoke (R@1 43%) over-optimistic vs full 2400 (R@1 15%)
  - n<100 CI ±15-20pt · documented in paper §6.5
- BM25 e2e 0% on EverMemBench (BGE-m3 + reranker pending T4 GPU)
- Two-server confusion early (T4 vs cloud) · stress test ran on wrong host
  - resolved · memorized to prevent recurrence

### CI · 2026-05-07 patch (post-tag)

- ✅ All 9 CI jobs green on main · ruff lint + py 3.10/3.12 ubuntu/macos matrix +
  v0.9 integration + npm wrapper + MCP smoke + Cursor extension build
- ✅ arXiv build workflow green · paper1 LaTeX compiles end-to-end
- Fixes (commits d3f179f → c2ff348):
  - `pyproject.toml` ruff config · ignore stylistic E/F rules · keep bug-catchers
  - `pyproject.toml` explicit packages list · `__init__.py` at root · `pip install -e .`
    now actually creates an importable `nautilus_compass` package (was broken before)
  - 14 modules · `sys.stdout.reconfigure(encoding="utf-8")` instead of
    `TextIOWrapper(sys.stdout.buffer)` · old pattern caused buffer aliasing →
    "I/O operation on closed file" under multi-import
  - 9 modules · CI fallback for `~/.claude/plugins/nautilus-compass` hardcoded
    paths · falls back to `Path(__file__).resolve().parent` when user-level
    plugin dir absent (CI runners + fresh clones)
  - `session_search.py` · added missing `PROJECTS.exists()` guard (parity with
    drift_history.py) · was raising `FileNotFoundError` on CI
  - `tests/test_e2e_encryption.py` · added missing `import os`
  - `paper/nautilus-compass.tex` · `\usepackage{cite}` → `\usepackage[round]{natbib}`
    + `\bibliographystyle{plain}` → `\bibliographystyle{plainnat}` ·
    sections used `\citep` / `\citet` (natbib syntax) · 45 unresolved citations
    + bbl incompatibility error fixed
  - `.github/workflows/ci.yml` · Test matrix · removed selftest.py and
    eval_recall.py (depend on user-specific memory data unavailable in CI) ·
    kept eval_drift.py (anchors-only · 100 hardcoded prompts)

### Promo · 2026-05-07

- 6 launch channels · `paper/promo/` (1184 lines)
  - `x_thread_zh.md` · 9 推 X 中文 thread + 配图 + 互动话术
  - `x_thread_en.md` · 9 tweets English thread
  - `hackernews.md` · Show HN title + first comment + reply playbook
  - `reddit_ml.md` · [R] flair · methodology callouts
  - `wechat_long_post.md` · ~5000 字公众号长文
  - `zhihu_tech.md` · ~5000 字知乎技术文
- `paper/V1.0_LAUNCH_DAY.md` · D-7 → D+7 timing playbook · 6 channels +
  cancel conditions + emergency contacts
- `paper/sections/paper2_00_abstract.tex` · expanded with EverMemBench 41% +
  cross-judge κ + V4-pro tied verdict (≤200 word target)

## [0.9.0-dev] · 2026-05-05 — "cross-agent · MCP/A2A · 56.6% on LongMemEval-S"

### 🎯 Highlights

- 🏆 **LongMemEval-S full-500 final = 56.6%** (DeepSeek V3.2 + 5 项加成 · ¥10 总成本)
  - 接近 Zep SOTA 下沿 (55-60%) · paper RAG SOTA 同档 (50-60%)
  - +12 pts vs Gemini-2.5-pro baseline (44.6%)
  - 1/15 cost vs commercial API stack
- 🆕 **Cross-agent memory federation** · 跨 Claude Desktop · Cline · Cursor · OpenClaw · Hermes 共享 memory
- 🆕 **MCP server v0.9** · 7 tools (4 new: ingest_obs · drift_history · session_search · profile)
- 🆕 **A2A adapter** · 4 capabilities (STORE/RETRIEVE/PROFILE/DRIFT_HISTORY)
- 🆕 **npm wrapper** · `@nautilus/compass-mcp` · `npx -y` 即用
- 🆕 **session_writer + drift-aware obs** · session 末自动蒸馏 · drift 自审 (claude-mem 替代 + 增强)

### Added

- `session_writer.py` · Volc Ark DeepSeek session 蒸馏 (¥0.05/session)
- `drift_history.py` + `session_search.py` · cross-project · ASCII timeline · keyword + drift filter
- `daemon_anchor_loader.py` · 3-layer anchors (platform_base + domain + tenant)
- `anchors_platform_base.json` · 通用 15 pos + 25 neg
- `sdk/compass_client.py` · multi-agent ingest SDK · offline buffer · E2EE-ready
- `sdk/attach_memory.py` · one-line Nautilus agent integration
- `sdk/a2a_adapter.py` · A2A protocol HTTP service (4 capabilities)
- `sdk/mcp_adapter.md` · MCP server installation spec
- `mcp_server.py` · 3 tools → 7 tools
- `npm/` · `@nautilus/compass-mcp` Node wrapper · auto Python detection
- `cursor-extension/` · VS Code extension TypeScript scaffold
- `examples/openclaw_integration.py` · `examples/hermes_integration.py`
- `examples/mcp_configs/` · paste-ready Claude Desktop · Cline · Cursor configs
- `paper/PLATFORM_FUSION.md` · 8 fusion points
- `paper/V09_USER_SCHEMA.md` · multi-user · multi-region · E2EE schema
- `paper/V09_API_SPEC.md` · server endpoint spec + FastAPI 实施
- `paper/V10_ROADMAP.md` · 12-month 17-phase roadmap
- `paper/RESULTS_v0.8.md` · 论文级 final 数据
- `paper/STAKE_DRIFT_COUPLING.md` · #4 fusion · economic spec
- `paper/sections/paper2_*.tex` · paper 2 LaTeX 8/8 sections (abstract · intro · related · method · eval · discussion · limitations · opensource)
- `INSTALL.md` · 3 install methods + 4 client configs
- `tools/migrate_from_v5.py` · v5-memory migration · #8 fusion
- `tests/test_compass_v09.py` · 7 integration tests
- `.github/workflows/ci.yml` · v0.9 multi-Python + npm + cursor + smoke
- `LICENSE` · MIT 首次正式声明

### Changed

- `pyproject.toml` v0.7 → v0.9.0-dev · 5 entry points · keyword expanded
- `mcp_server.py` v0.7 → v0.9 · 3 tools → 7 tools
- `stop_hook.py` · 加 session_writer 调用 · 不依赖 claude-mem
- `landing/index.html` · 加 v0.9 路线 + 8 fusion points sections
- `README.md` · LongMemEval section ~54% → 56.6% final
- `paper/results/experiments_20260505.csv` · v0.8 final 行填入 + 6 类型分项

### Removed

- claude-mem dependency (234 MB cache + uv tool + .claude-mem data)
  - session_writer 自给 · 不需要 claude-mem 写 session memory
  - v0.9 之前可共存 · 现在 compass 完整覆盖

### Performance

- LongMemEval-S full-500: **0.466 (baseline) → 0.566 (v0.8)** · +10 pts
- Per-type: ssa 76.8→83.9 · ku 51.3→57.7 · ssu 30.0→**57.1** ⭐⭐ · ms 43.6→54.9 · ssp 33.3→53.3 · temporal 45.9→46.6
- bge-m3 daemon recall p95: ~200ms (no change)
- session_writer cost: ¥0.05/session via Volc Ark DeepSeek V3.2

### Negative findings (paper 价值)

- Neo4j graph rerank: -6.2 pts (closed haystack 上跟 cross-encoder 重复)
- Double-model router (ssp+ku 用强 model): -2.1 pts (sample noise)
- SSP "infer preference" prompt: -37.5 pts (LLM 跑偏 · 撤回)
- MiniMax thinking-1024: 44% refusal cascade · full-500 collapsed at 33%
- Kimi K2.6 thinking: 0 gain (vs DeepSeek +10)


## [0.7.0] - 2026-04-29 — "from coin-toss to 0.92 AUC"

### 🎯 Drift detection: 0.51 → 0.92 AUC

Rebuilt the persona drift detection from the ground up in 4 steps:

1. **Anchors task-shaped**: replaced 25 abstract maxims with 25 task-pattern sentences that match real prompt distribution. AUC 0.51 → 0.79.
2. **Top-k mean scoring**: replaced anchor centroid mean (which blurs each anchor's semantics) with top-3 cosine mean. Marginal gain.
3. **bge-m3**: switched embedder from bge-small-zh-v1.5 (Chinese-only) to bge-m3 (1024d, 100+ languages). AUC → 0.84.
4. **Hard FP examples** added back into negative_anchors (10 examples → 35 total). AUC → **0.92**.

### 📊 LongMemEval-S benchmark (subset 12 · n=12 · 6 question types × 2)

| System | P@1 | P@5 | MRR |
|---|---|---|---|
| **nautilus-compass (m3 + bge-reranker-v2-m3)** | **0.750** | **0.917** | **0.837** |
| nautilus-compass (m3 only · no rerank) | 0.667 | 0.750 | 0.732 |
| mem0 (claimed retrieval-only) | n/a | ~0.6 | ~0.55 |

Reranker gives biggest lift on weakest question types:
- single-session-user: MRR 0.091 → 0.522 (**5x improvement**)
- multi-session: MRR 0.55 → 0.75 (+0.20)
- Other types already at MRR 1.0 baseline (ceiling)

Embedder ablation (subset 4 only):
- bge-small-zh-v1.5: MRR 0.414 (English content kills Chinese-only)
- bge-m3: MRR 0.760
- multilingual-e5-small: MRR 0.762 (practically tied with m3)

### 🆕 Added

- `tests/eval_calibrate.py` — cosine 分布校准建议 threshold
- `tests/eval_drift.py` — 50 aligned + 50 deviation drift detection AUC
- `tests/eval_recall.py` — leave-one-out P@1/3/5/MRR
- `tests/eval_longmemeval.py` — LongMemEval-S retrieval benchmark
- `tests/eval_rerank.py` — bi-encoder + CrossEncoder reranker pipeline
- `tests/run_all.sh` — full eval suite runner
- `pyproject.toml` + `LICENSE` (MIT) — pip packaging
- `.github/workflows/ci.yml` — CI on Linux + macOS · Python 3.10/3.12
- `OPEN_SOURCE_READINESS.md` — go/no-go decision tree
- `README_OPEN_SOURCE_DRAFT.md` — public-ready README

### 🔧 Changed

- `daemon.py` line 41-58: default embedder bge-m3 (was bge-small-zh) · all thresholds tunable via `ZMM_*` env vars
- `daemon.py` line 215-225: removed centroid mean (was blurring anchors)
- `daemon.py` line 282-310: drift scoring now top-3 mean, not centroid
- `recall.py` line 543, 601: daemon ping timeout 0.3s → 2.0s (m3 cold load was being misjudged unreachable)
- `recall.py`: dynamic embedder label in hook output (was hardcoded `BGE-bge-small-zh`)
- `anchors.json`: 25 positive (task-shaped) + **35 negative** (was 25, +10 hard FP examples added)

### 📝 Calibration values (m3 + 35 anchors · LongMemEval-validated)

```python
COSINE_MIN = 0.25                  # query↔memory recall threshold
DRIFT_ALERT_THRESHOLD = -0.032     # m3 + hard FP best Youden J
NEG_ANCHOR_HIT_THRESHOLD = 0.538   # neg ↔ memory p95
```

### ⚠️ Known issues

- m3 (~3 GB RAM) sometimes silently OOMs on Windows native Python 3.14. Recommended: WSL2.
- HF Hub downloads are flaky on Win/py3.14 (httpx client closes mid-request). Use `pip install -e .[modelscope]` and `install.sh` for ModelScope mirror fallback.
- Drift detection has false positives on system event injections (tool notifications mentioning "ephemeral", "size") that semantically overlap with anti-anchors. Production hooks should filter to true user prompts only.
- single-session-user retrieval MRR 0.099 — known limitation of bi-encoder-only retrieval. Use the BGE-CrossEncoder rerank path for production (see `tests/eval_rerank.py`).

### 📦 Dependencies

- Required: `sentence-transformers>=2.7`
- Optional: `modelscope` (China mirror), `hf_transfer` (faster HF download)
- Embedder: `BAAI/bge-m3` (default), or `intfloat/multilingual-e5-small`, or `BAAI/bge-small-zh-v1.5`
- Reranker (optional): `BAAI/bge-reranker-v2-m3`

## [0.6.0] - 2026-04-26

- Initial daemon TCP socket on 127.0.0.1:9876
- Strategy distillation (DPT-Agent style) via `strategy_store.py`
- Time-bucket recall (24h vs 7d+ warning)
- 3-hook lifecycle (UserPromptSubmit + PostToolUse + Stop)
- Per-domain anchors (vc / zenmind / default)
