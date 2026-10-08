**Category:** Workflow Orchestration (memory section, next to omega-memory/claude-brain)

**What it is:** [nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) — a local memory and reliability layer for Claude Code: BGE-M3 memory daemon (MCP, 17 tools), drift detection (AUC 0.83 held-out) that scores every prompt against a frozen failure-pattern anchor set before the agent acts, and a cross-agent contract layer for shared-file multi-agent work. MIT, PyPI `nautilus-compass`, one-command `install.sh`.

**Measured claims (reproducible):** retrieval beats mem0 on the full LongMemEval-S 500 (P@1 0.890 vs 0.774, both sides `infer=False`, one-command reproduction script in-repo). Preregistered criteria + negative results shipped as first-class artifacts.
