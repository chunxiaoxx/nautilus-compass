# v0.9.0-dev · Cross-agent · MCP/A2A · 56.6% on LongMemEval-S

> Tag: `v0.9.0-dev` · Branch: `main` · 2026-05-XX

## 🎯 Release Highlights

**LongMemEval-S full-500 = 56.6%** with DeepSeek V3.2 + 5-component pipeline.
Same accuracy band as Zep SOTA at **1/15 cost**.

🆕 **Cross-agent memory federation** · Same `user_id` across Claude Desktop,
Cline, Cursor, OpenClaw, Hermes → all clients share memory. claude-mem
can't do this; Mem0/Letta/A-MEM/Zep can't either.

🆕 **MCP server v0.9** with 7 tools (4 new) · Compatible with Claude
Desktop, Cline, Cursor, any MCP-compatible client.

🆕 **A2A adapter** with 4 capabilities · Discoverable via
`a2a-registry.nautilus.social` (when launched).

🆕 **npm wrapper** `@nautilus/compass-mcp` · `npx -y @nautilus/compass-mcp`

🆕 **session_writer + drift-aware obs** · Self-audit at session end ·
DeepSeek V3.2 ¥0.05/session via Volc Ark.

## 📊 Per-question-type accuracy on LongMemEval-S (n=500)

| Type | Compass v0.8 | DeepSeek baseline | Δ |
|---|---|---|---|
| 🏆 single-session-assistant | **83.9%** | 76.8% | +7.1 |
| knowledge-update | **57.7%** | 51.3% | +6.4 |
| ⭐ single-session-user | **57.1%** | 30.0% | **+27.1** |
| multi-session | 54.9% | 43.6% | +11.3 |
| single-session-preference | 53.3% | 33.3% | +20.0 |
| temporal-reasoning | 46.6% | 45.9% | +0.7 (open) |
| **Overall** | **56.6%** | 46.6% | **+10.0** |

## 📦 Install

```bash
# Python
pip install nautilus-compass             # or uv tool install
# Node MCP wrapper
npm install -g @nautilus/compass-mcp     # or use via npx
```

## 🚀 Quick Start

### Claude Desktop
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "compass": {
      "command": "npx",
      "args": ["-y", "@nautilus/compass-mcp"],
      "env": { "COMPASS_USER_ID": "u_yourname" }
    }
  }
}
```

### Cursor / Cline
See `examples/mcp_configs/`.

### Nautilus agent (one-line)
```python
from nautilus_compass.sdk.attach_memory import attach_memory
agent = NautilusAgent(role="strategy", user_id="u_xxx")
attach_memory(agent)
```

## 🔬 Research artifacts

- `paper/RESULTS_v0.8.md` · final benchmark data (per-type · trajectory · negative findings)
- `paper/sections/paper2_*.tex` · 8 paper sections + 1 appendix + 3 figures + 19 refs
- `paper/PLATFORM_FUSION.md` · 8 deep-fusion points with Nautilus platform
- `paper/V09_USER_SCHEMA.md` · multi-user · multi-region · E2EE schema
- `paper/V09_API_SPEC.md` · server endpoint contract + FastAPI
- `paper/V10_ROADMAP.md` · 12-month 17-phase roadmap
- `paper/STAKE_DRIFT_COUPLING.md` · economic coupling spec
- `paper/REGION_SHARDING.md` · v1.0 multi-region (PIPL/GDPR/CCPA)
- `paper/results/experiments_20260505.csv` · 16 rows · 6 LLMs × per-type acc

## 📚 Negative findings (paper value)

We documented 4 interventions that did NOT help:

1. **Neo4j graph rerank**: -6.2 pts (closed haystack signal redundant with cross-encoder)
2. **Double-model router** (ssp+ku to strong model): -2.1 pts (sample noise)
3. **SSP "infer preference" prompt**: -37.5 pts (LLM invents preference-related answers)
4. **MiniMax thinking-1024**: refusal cascade collapse (44% refusal at full-500)

## 🔧 Per-model thinking ablation

| Model | nothink | thinking | Note |
|---|---|---|---|
| Gemini-2.5-pro | --- | 44.6% | (sample matches full) |
| DeepSeek V3.2 | 39.6% | **46.6%** | thinking +6.8 pts ⭐ |
| GLM-5.1 | 41.7% | 43.8% | +2.1 |
| Kimi K2.6 | 35.4% | 35.4% | thinking gain = 0 |
| MiniMax M2.7 | 41.7% | 33% † | refusal cascade · use nothink |

**Bottom line**: Per-model thinking-on/off must be benchmarked per release.
Don't assume thinking always helps.

## 🆕 7 MCP tools

| Tool | Purpose |
|---|---|
| `compass.recall` | Semantic recall over project memory (BGE-m3) |
| `compass.drift_check` | Real-time AI drift detection (anchor-based · AUC=0.92) |
| `compass.drift_history` | **Cross-project drift timeline** · claude-mem 没有的 |
| `compass.session_search` | Keyword search · type/drift filter |
| `compass.profile` | User profile aggregate |
| `compass.ingest_obs` | Write structured observation |
| `compass.feedback_log` | Train anchors via feedback |

## 🌐 8 Nautilus platform fusion points

| # | Fusion | When |
|---|---|---|
| 1 | 单点登录 (Nautilus JWT) | v0.9.1 |
| 2 | OAuth2 PKCE for 3rd-party | v0.9.2 |
| 3 | nautilus-agent runtime 自动注入 | v0.9.3 |
| 4 | stake×drift 经济耦合 | v0.9.5 |
| 5 | marketplace agent 信任层 | v1.0.1 |
| 6 | platform_anchors 三层继承 | v0.9.4 |
| 7 | RAID-2 写审分离 | v1.0 |
| 8 | v5-memory 兼容迁移 | v0.9.6 |

## 🛠 Platform changes

- Removed: `claude-mem` dependency (compass session_writer covers it · 234 MB freed)
- Added: `compass_http_v09.py` FastAPI server (multi-user · sqlite · JWT)
- Added: `openapi.yaml` machine-readable API spec (OpenAPI 3.1)
- Added: 4 new CI jobs (v0.9 integration · MCP smoke · npm wrapper · cursor build)
- Added: SECURITY.md · CODE_OF_CONDUCT.md · CODEOWNERS · dependabot.yml
- Updated: pyproject.toml v0.7 → v0.9.0-dev · 5 new entry points

## 🙏 Contributors

@chunxiaoxx · primary author

(Future contributors welcome · see [CONTRIBUTING.md](CONTRIBUTING.md))

## 💸 Reproducibility

```bash
git clone https://github.com/chunxiaoxx/nautilus-compass
cd nautilus-compass
pip install -e .[dev]
python tests/eval_longmemeval_accuracy.py --pipeline=m3-rerank --full
```

Total reproduction cost: **~$3.50 USD** (Tencent T4 spot 7.79h + Volc Ark
coding plan).

## 🔗 Links

- 📊 [Final results](paper/RESULTS_v0.8.md)
- 📰 [Blog post / announcement](paper/BLOGPOST.md)
- 📜 [Paper draft (LaTeX)](paper/paper2_main.tex)
- 🛣️ [Roadmap to v1.0](paper/V10_ROADMAP.md)
- 🔐 [Security policy](SECURITY.md)

## 📄 License

MIT · evaluating Apache 2.0 dual-license for v1.0 enterprise self-hosting.

## 🔭 What's next

- v0.9.1: Nautilus auth integration · sqlite migration
- v0.9.5: stake×drift economic coupling
- v1.0: E2EE default · region sharding · RAID-2 review · paper publication

---

*Compass is part of the [Nautilus platform](https://nautilus.social) 7-capability
suite. The platform is in private alpha; the compass component is open-source.*
