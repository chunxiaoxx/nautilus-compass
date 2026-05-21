# SPEC · GBrain Skillpack 5-step Cycle Rewrite

> **Status**: Design only · 2026-05-21 · code ship deferred (~1-2 weeks effort)
> **Strategy**: Python clean-room rewrite of GBrain skillpack subsystem · NO fork of MIT TypeScript source
> **Target**: v2.0 Layer 5 adoption · post-`npx init` (S2 already shipped 8c2f8a2)
> **Total LOC estimate**: ~300 (loader + registry + evaluator + cron emitter + CLI)
> **Companion**: `SPEC_GBRAIN_ADAPTER.md` (framing + attribution · NOT this doc) · this is implementation

---

## 1. Context · why a skillpack subsystem

compass v1.7.1 current state:
- Single ingest+recall flow (`stop_hook.py` distill · `mcp_server.py` tools · `recall.py` retrieval)
- 9 lifecycle hooks (Phase 2.A · `c68dc6c`) for event trigger surface
- `add_worker(spec)` MCP tool (Phase 2.B · `2ed77b4`) for self-evolving worker registration
- **No skill abstraction** · adding new capability = patching core files

GBrain ships a **skillpack** subsystem (`garrytan/gbrain` · MIT · 17.8K stars · production: 14,700 brain files + 40+ skills + 20+ cron jobs · built in 12 days). Verbatim from GBrain skillpack doc:

> "5-step cycle: concept · prototype · evaluate · codify · cron"

This SPEC ports that **architecture pattern** to Python clean-room. **No code fork** — GBrain is MIT but TypeScript, and the value is in the 5-step lifecycle architecture, not the specific TS implementation.

---

## 2. Why · skillpack value for compass

1. **Super-agent self-evolving** · skill = primitive that an agent can add without core code change
2. **Cross-agent reuse** · skill catalog can be browsed via `compass-mcp skill list` · agents discover each other's capabilities
3. **Audit trail** · every skill has `created_at` / `codified_at` / `review_count` frontmatter · drift detection over skill quality
4. **RAID-dispatchable** · each module of this SPEC fits a separate bounty (see §6)

---

## 3. 5-step cycle · GBrain → compass mapping

| Step | GBrain verbatim | compass mapping (NEW) | Trigger |
|---|---|---|---|
| **concept** | markdown SKILL.md proposal | `skills/concepts/<name>.md` user-authored | manual create |
| **prototype** | minimal handler code | `skills/prototypes/<name>/{SKILL.md, handler.py, tests/}` | `compass-mcp skill init <name>` |
| **evaluate** | gbrain-evals harness | `tests/test_skill_<name>.py` 5-case smoke + walltime check | `compass-mcp skill evaluate <name>` |
| **codify** | merge to skills/ + version tag | move to `skills/codified/` · frontmatter `status: codified` · `review_count++` | `compass-mcp skill promote <name>` |
| **cron** | systemd timer + scheduled invocation | `cron/skill_<name>_cron.sh` generated from frontmatter `cron_schedule` | `compass-mcp skill schedule <name>` |

---

## 4. Architecture · Python clean-room

### 4.1 Storage layout

```
nautilus-compass/skills/
├── concepts/                       # step 1 · open proposals · markdown only
│   ├── auto-link-fixup.md
│   └── overnight-consolidate.md
├── prototypes/                     # step 2 · code in progress · not active
│   └── auto-link-fixup/
│       ├── SKILL.md
│       ├── handler.py
│       └── tests/test_smoke.py
├── codified/                       # step 3-4 · evaluated · production
│   └── numeric-claims-extractor/   # example existing skill
│       ├── SKILL.md
│       ├── handler.py
│       └── tests/
├── retired/                        # step 5 (rare) · archived
└── _skill_registry.json            # auto-generated · lookup all codified
```

### 4.2 SKILL.md frontmatter (declared schema · LLM-free)

```yaml
---
name: auto-link-fixup
description: ≤120 char what this skill does
status: concept | prototype | codified | retired
created_at: 2026-05-21T10:00:00Z
codified_at: null  # ISO8601 when promoted to codified
handler_path: handler.py  # relative to skill dir
cron_schedule: null  # crontab format · null if event-driven only
trigger_events: [PostToolUse, SessionEnd]  # from compass 9 hooks (Phase 2.A)
resource_budget:
  llm_calls_max: 0  # MUST be 0 at ingest path · positive only for nightly cron
  walltime_max_sec: 60
  memory_mb_max: 200
authors: [chunxiaoxx, hr-agent-web]
review_count: 0  # incremented per evaluate run
last_eval_at: null
last_eval_pass: null
---
```

### 4.3 handler.py contract

```python
# nautilus-compass/skills/codified/<name>/handler.py
from typing import Any

def execute(event_payload: dict, context: dict) -> dict:
    """Skill handler entry point.

    Args:
        event_payload: dict from hook trigger (SessionStart/PostToolUse/etc)
        context: dict with compass facilities · {recall, ingest, mcp_call}

    Returns:
        {success: bool, output: any, llm_calls_used: int, walltime_ms: int}

    Contract:
        - Deterministic given same event_payload (idempotent)
        - llm_calls_used MUST be 0 unless cron-scheduled
        - Raises SkillBudgetExceeded if exceeds resource_budget
    """
    ...
```

### 4.4 Implementation modules · ~300 LOC

| Module | Path | LOC | Description |
|---|---|---|---|
| `skill_loader.py` | `nautilus_compass/skills/skill_loader.py` | 60 | Parse SKILL.md frontmatter + dynamically import handler.py · validate contract |
| `skill_registry.py` | `nautilus_compass/skills/skill_registry.py` | 80 | `_skill_registry.json` maintenance · status promotion (concept→prototype→codified) · review_count update |
| `skill_evaluator.py` | `nautilus_compass/skills/skill_evaluator.py` | 70 | Run `tests/test_smoke.py` · enforce resource_budget · record `last_eval_pass` |
| `skill_cron_emitter.py` | `nautilus_compass/skills/skill_cron_emitter.py` | 40 | Generate crontab line from frontmatter · `cron/skill_<name>_cron.sh` template |
| `cli_skill.py` | `bin/cli_skill.py` | 50 | `compass-mcp skill {init,promote,list,evaluate,schedule,retire}` subcommands |
| **Total** | | **~300** | |

---

## 5. Verification criteria · 10 smoke cases (LLM-free deterministic)

1. `skill_loader.load("skills/codified/numeric-claims-extractor")` → returns handler callable
2. Loading skill with `status: concept` (no handler.py yet) → returns `None` + warning
3. Loading skill with invalid frontmatter → raises SkillSchemaError
4. `skill_registry.promote("foo", from="prototype", to="codified")` → moves dir + updates JSON
5. `skill_registry.list_by_status("codified")` → returns all codified skill metadata
6. `skill_evaluator.run("foo")` → executes `tests/test_smoke.py` · enforces walltime budget
7. Skill exceeds `resource_budget.llm_calls_max` → raises SkillBudgetExceeded
8. `skill_cron_emitter.emit("foo")` → generates valid crontab line + cron/skill_foo_cron.sh script
9. CLI `compass-mcp skill init my-skill` → creates `skills/prototypes/my-skill/` scaffold (SKILL.md + handler.py stub + tests/)
10. CLI `compass-mcp skill list` → table of all skills + status + review_count

---

## 6. RAID dispatch · this SPEC ready for bounty

| Bounty | Module | LOC | Suggested NAU | Notes |
|---|---|---|---|---|
| `b-skill-loader` | `skill_loader.py` | 60 | 8 | Self-contained · frontmatter parse + dynamic import |
| `b-skill-registry` | `skill_registry.py` | 80 | 10 | JSON state machine · status promotion |
| `b-skill-evaluator` | `skill_evaluator.py` | 70 | 10 | Subprocess pytest runner + budget enforce |
| `b-skill-cron` | `skill_cron_emitter.py` | 40 | 5 | Pure template generation |
| `b-skill-cli` | `bin/cli_skill.py` | 50 | 8 | Subcommand routing · UX polish |
| **Total** | | **~300 LOC** | **41 NAU** | `caishen-group` has 5000 NAU · sufficient |

Modules are mostly independent · can dispatch concurrently to multiple agents via RAID-2 consensus.

---

## 7. Risks + Mitigations

| Risk | Mitigation |
|---|---|
| Dynamic `handler.py` import = security risk | Whitelist path prefix · validate file is in `skills/codified/` only |
| `cron_schedule` user input = injection risk | Validate crontab syntax with strict regex · reject shell metacharacters |
| Skill drift over time (`codified` skill degrades) | `last_eval_pass` field · cron re-evaluates monthly · auto-demote on failure |
| Frontmatter schema bloat | Pre-register fields · `SkillSchemaError` on unknown fields (anti-feature-creep) |
| Anchor #5 reinvention vs GBrain TS source | Clean-room verified · read GBrain README + GBRAIN_SKILLPACK.md only · NOT source code |
| Resource budget too lax · skills hog system | Default `walltime_max_sec=60` + `memory_mb_max=200` · explicit opt-in for higher |

---

## 8. Anchor contributions

| Anchor | Contribution |
|---|---|
| #1 agent first | Skill = self-evolving primitive · super-agents add capabilities without core patch |
| #2 真客户 onboard | `npx init` (S2 shipped) + skillpack = full adoption story · enterprises can extend without forking |
| #3 anti-D-maintenance | Clean 5-module breakdown · RAID-dispatchable bounties |
| #5 anti-reinvention | Reuse `npx init` (S2) · reuse 9 hooks (Phase 2.A) · reuse `add_worker` (Phase 2.B) · GBrain paradigm reference |
| #7 anti-overclaim | 10 smoke + resource budget enforcement explicit |

---

## 9. Sequence (ship order in 1-2 week sprint)

| Day | Module | Notes |
|---|---|---|
| 1-2 | `skill_loader.py` | Frontmatter parse + dynamic import · self-contained · easy smoke (3 cases) |
| 3-4 | `skill_registry.py` | JSON state machine · status promotion logic |
| 5 | `skill_evaluator.py` | Subprocess pytest + budget enforce |
| 6 | `skill_cron_emitter.py` | Template gen · simple |
| 7-8 | `bin/cli_skill.py` | UX polish · all subcommands |
| 9 | Integration · port `numeric-claims-extractor` as first reference codified skill | Migration · validates contract |
| 10 | Full smoke 10 cases + backward-compat check | All v1.7.1 tests must still pass (31/31) |

---

## 10. Related ship trail

- v2 spec source · `paper/COMPASS_V2_SPEC_DRAFT.md` Layer 5
- Companion attribution · `paper/SPEC_GBRAIN_ADAPTER.md` (framing/citation · NOT implementation)
- npx init (prerequisite) · commit `8c2f8a2` (S2 · ships `.compass/` workspace)
- 9 hooks (prerequisite) · commit `c68dc6c` (Phase 2.A · `trigger_events` field references these)
- `add_worker` (prerequisite) · commit `2ed77b4` (Phase 2.B · skills could register as workers)
- Plan reference · `~/.claude/plans/scalable-drifting-seahorse.md`
- Companion specs same sprint · `SPEC_LAYER2_L1_REWRITE.md` (S3) · `SPEC_PROOF_OF_IMPACT.md` (S4)

---

## 11. Open questions (defer to ship session)

- [ ] Skill version tagging · git tag per skill or just frontmatter `version: 1.0`?
- [ ] Skill dependency declaration · can skill A `depends_on:` skill B?
- [ ] Skill cross-agent share · publish skill to V5 `platform_skill_registry` (existing · 7 skills · 3 imports)?
- [ ] Skill marketplace · pricing in NAU? out of scope or in?
- [ ] Backward compat · existing `stop_hook` strategies (`auto_distill_log.jsonl`) — convert to skills or keep separate?
