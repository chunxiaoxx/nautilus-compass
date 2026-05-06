# Compass Public Roadmap

> Trimmed-for-public version of [V10_ROADMAP.md](V10_ROADMAP.md).
> Internal-only items (specific business decisions, dollar amounts,
> stakeholder names) are removed. Architectural commitments preserved.
> 2026-05-05 · subject to change with notice.

## Where we are

```
v0.8.x (✅ Released 2026-05): writer · drift-aware obs · LongMemEval-S 56.6%
v0.9.0 (🟡 RC 2026-05): MCP/A2A · cross-agent · npm wrapper · Cursor scaffold
v0.9.1 → v1.0: 12-month roadmap below
```

## Public commitments

We commit to the following architectural properties through v1.0:

1. **Provider-neutral**: Any Anthropic-compatible LLM endpoint works.
   Volc Ark, Anthropic, OpenAI, Gemini are all supported. We will not
   lock into a single provider.

2. **Local-first**: Plaintext memory stays local by default. Cloud sync
   is opt-in. Self-hosting is a fully supported deployment.

3. **Open protocol**: MCP (Anthropic) + A2A (Google) are first-class.
   Custom SDK is the fallback, not the recommended path.

4. **Open source**: Plugin core, SDK, MCP server, A2A adapter all
   licensed MIT (transitioning to Apache 2.0 considered for v1.0;
   not weakening permissions).

5. **Reproducible benchmarks**: All accuracy claims come with public
   reproduction scripts and raw logs.

6. **Region-respectful**: Multi-region sharding (cn-shanghai /
   eu-frankfurt / us-virginia) by v1.0. Default no cross-region
   data flow.

## v0.9.x milestones (next 6 months · 2026-06 → 2026-11)

### v0.9.1 (June 2026)

- Authentication: email + passphrase + JWT
- sqlite migration script (memory/*.md → observations table)
- Server-side `/v1/observations` endpoint live
- Single region (cn-shanghai) production
- Backward compat: v0.7.2 endpoints preserved 1 month

### v0.9.2 (July 2026)

- OAuth2 PKCE for 3rd-party agents (Cursor, OpenClaw forks, Hermes)
- Layered anchor inheritance (platform_base + domain + tenant)
- Daemon hot-reload of anchor packs

### v0.9.3 (August 2026)

- VS Code / Cursor extension on marketplace
- npm package public release
- Cline integration (chat history capture)

### v0.9.4 (September 2026)

- Profile aggregate v1 (client-side compute)
- Session search v2 (semantic + keyword fusion)
- Multi-window context expansion

### v0.9.5 (October 2026)

- Stake-coupled drift economics (red drift → penalty · green → bonus)
  for Pro+ tier
- Agent reputation metrics for Nautilus marketplace
- Anti-cheat sampling and outlier detection

### v0.9.6 (November 2026)

- v5-memory migration tool (legacy users)
- Audit log endpoint for enterprise compliance

## v1.0 milestones (next 6-12 months · 2026-12 → 2027-05)

### v1.0-rc (December 2026 → February 2027)

- E2EE default for Pro+ users (libsodium client-side)
- Self-host docker-compose template
- Apache 2.0 dual-license decision finalized

### v1.0 (March 2027 → April 2027)

- RAID-2 (writer-reviewer) write path for org plan
- Region sharding live in eu-frankfurt + us-virginia
- Team plan (shared memory rooms with group keys)

### v1.0 GA (May 2027)

- Public open-source release of platform server (apache 2.0 if
  decided)
- Paper publication (arXiv minimum; ICLR / NeurIPS workshop submission)
- Cross-agent profile aggregation (privacy-preserving)
- Marketplace agent recommendation engine

## Beyond v1.0 (post-2027)

(Subject to change. These are aspirations, not commitments.)

- v1.1: Cross-region encrypted backup (user-controlled · IPFS / Arweave)
- v1.2: Federated learning across users (no raw data exchange)
- v1.3: Multi-modal observations (voice / image / code / docs)
- v1.4: Local LLM mode (Ollama · LM Studio · for self-host)
- v2.0: On-chain anchor governance (DAO votes on platform anchors)

## What's NOT on the roadmap (intentionally)

- AGPL relicensing (we believe in MIT/Apache permissions)
- Mandatory cloud (self-hosting always supported)
- Telemetry-by-default (we don't collect usage data without consent)
- Vendor-locked LLM provider (architecture remains neutral)
- "Compass Cloud Premium" tier with proprietary features
  (the open-source version always has feature parity within
  3 months of any cloud-tier feature)
- Closed-source plugin (the plugin code stays open)

## Compatibility commitments

- **MCP protocol changes**: when Anthropic ships MCP v2, we will
  support both v1 and v2 transports for at least 12 months.
- **A2A protocol changes**: when Google revises A2A, similar 12-month
  dual support.
- **Schema migrations**: any breaking schema change announced 30 days
  before deprecation. Migration scripts shipped.

## Changes to this roadmap

- Major changes (slipping a milestone by >1 month) announced in CHANGELOG
  and via GitHub Discussions
- Every milestone has a corresponding tracked issue on GitHub
- We do retrospectives at the end of each phase (publicly visible)

## How to influence this roadmap

- Open a GitHub Discussion: "Roadmap proposal: ..."
- File a GitHub Issue with the `roadmap:` label
- For investor / strategic discussions: see Press Kit

## Key documents

- [V10_ROADMAP.md](V10_ROADMAP.md) — internal full version
- [V10_FINAL_SPEC.md](V10_FINAL_SPEC.md) — v1.0 specification
- [PLATFORM_FUSION.md](PLATFORM_FUSION.md) — Nautilus integration
- [LICENSE_DECISION.md](LICENSE_DECISION.md) — license evolution

---

*This roadmap was last updated 2026-05-05. We update it monthly.*
