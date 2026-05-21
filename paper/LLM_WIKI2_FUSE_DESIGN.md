# LLM_WIKI2 Fuse Design · Declarative Lifecycle Memory

> v1.7.1 · MEME-extension Phase 2 · `declaration_field` 真 native extension
> Ship target · ~160 LOC · 5 smoke test pass
> Author · compass-dialog · 2026-05-21

---

## 1. Context

5/22 niche pivot CONFIRMED · 路径 3b · 4 ecosystem audit(evomap.ai closed · Mem0/Letta/Cognee LLM-required ingest)证 plug = lose 差异化。

真 add llm-wiki2(rohitg00 gist · Karpathy v2 · 5K stars)真 Ebbinghaus + 4-tier paradigm 进 compass declaration_field(174034e · 5/20 P0 ship)真 native extension。

**真 paper3 novelty claim**:
> "no open-source memory system has schema-declared, write-time-LLM-free 4-tier promotion + Ebbinghaus decay"

---

## 2. Prior art(verbatim audit · 2026-05-21 WebFetch)

### llm-wiki2(rohitg00 gist · 5K stars)
- Ebbinghaus verbatim:**"retention decays exponentially with time, but each reinforcement (access, confirmation from a new source) resets the curve"** — 无 formula
- 4-tier verbatim:Working / Episodic / Semantic / Procedural
- promotion verbatim:**"The LLM promotes information up the tiers as evidence accumulates"** — LLM-required
- frontmatter spec:**未 proposed**

### agentmemory(rohitg00 production · 15.3K stars · Apache 2.0)
- LongMemEval-S R@5:**95.2%** · 92% fewer tokens vs paste-full-context
- AUTO_COMPRESS 默认 OFF · BM25 真 fallback no-LLM
- 4-tier same names · production-validated
- 真 differentiation gap:compress LLM-required when AUTO_COMPRESS=true

### MEME K.2 prior art(Jung et al. arXiv 2605.12477)
- verbatim:**"MD-flat with Opus 4.7: explicit contingencies and active dependency propagation. At ingest, Opus writes the current value and an explicit contingency entry naming the parent."**
- 真 LLM-extracted contingency · compass `depends_on:` 是 **schema-declared variant**

### compass v1.7 已 ship baseline(commit 174034e · 5/20)
- `depends_on:` + `declaration_type:` + `supersedes:` 真 schema-declared
- `transitive_close` BFS(`recall.py:635-666`)
- `verify_cascade_closure`(`recall.py:669-705`)
- 9 smoke test pass

---

## 3. Schema · 5 new frontmatter fields(v1.7.1 extension)

```yaml
tier: working | episodic | semantic | procedural    # 默认 working · llm-wiki2 exact 4 tier
decay_rate: 0.5                                      # 0.0-1.0 · Ebbinghaus exponential
forget_at: 2026-06-01T00:00:00Z                      # ISO8601 · null = never
promote_after: "7d" | "5_access"                     # duration or access count
reinforce_count: 0                                   # int · access event 累计
```

### default `promote_after` by tier(deterministic table · 无 LLM 决策)

| current tier | default `promote_after` | next tier |
|---|---|---|
| working | "1d" or "1_access" | episodic |
| episodic | "7d" or "5_access" | semantic |
| semantic | "30d" or "20_access" | procedural |
| procedural | null(top tier 不 promote) | — |

用户可覆盖 default · explicit `promote_after` 真 frontmatter 真 last word。

---

## 4. LLM-free promotion rule(deterministic schema-driven)

### Rule A · access event
每次 recall hit 一条 entry:
- `reinforce_count++`
- `last_access_at = now()`

### Rule B · promote check(每次 ingest 或 access 时执行)
- if `promote_after` 是 duration · `(now() - created_at) >= duration` → `tier++`
- if `promote_after` 是 count · `reinforce_count >= count` → `tier++`
- `procedural` tier 不 promote(top)

### Rule C · forget check
- if `forget_at != null` and `now() >= forget_at` → archive flag set
- archive flag entries 真 recall 真 down-weight 或 exclude(opt-in via env flag)

### 真 anti-LLM 真 audit:
- 真 rule A/B/C 全 schema 真 read + arithmetic · 无 LLM call
- 真 promotion 真 deterministic · 真 audit trail 真 reproducible
- 真 Ebbinghaus reset 真 access event 真 emit · 真 schema 真 record

---

## 5. Code locations · verbatim

| File | Line | Change |
|---|---|---|
| `session_writer.py` | 55 之后(supersedes 之后) | 加 5 fields 真 frontmatter prompt schema |
| `mcp_server.py` | 449 之后(supersedes parse 之后) | 加 5 args parse |
| `mcp_server.py` | 474 之后(dep_lines build 之后) | 加 5 emit lines into frontmatter |
| `mcp_server.py` | 1229 之后(supersedes property 之后) | 加 5 inputSchema properties |
| `recall.py` | 705 之后(verify_cascade_closure 之后) | 加 `promote_lifecycle_tier` function |

---

## 6. Verification · 5 smoke test cases

| # | Test | Expected |
|---|---|---|
| 1 | **tier promotion** · entry with `tier:working` + `reinforce_count:5` + `promote_after:"5_access"` → `promote_lifecycle_tier` returns `tier:episodic` | tier promoted |
| 2 | **decay reset** · access event on entry → `reinforce_count++` · `last_access_at = now()` | count incremented |
| 3 | **forget_at expiry** · entry with `forget_at: 2020-01-01T00:00:00Z` → `archive_flag = True` | flag set |
| 4 | **reinforce_count 累计** · 3 access events → `reinforce_count = 3` | counter correct |
| 5 | **cascade closure 不破** · existing `verify_cascade_closure` 真 5/20 test cases 真 pass · lifecycle fields 真 not affect cascade | regression 0 |

---

## 7. Reuse existing(不重复造轮子 · anchor #5)

| Existing | Path:Line | Reuse for |
|---|---|---|
| `transitive_close` BFS | `recall.py:635-666` | promotion path traversal pattern |
| `verify_cascade_closure` | `recall.py:669-705` | lifecycle check pattern |
| `declaration_field` parser | `session_writer.py:46-67` | extend 加 5 new fields · 同 schema layer |
| `tool_ingest_obs` args parse | `mcp_server.py:437-449` | extend 加 5 new args |
| `dep_lines` emit | `mcp_server.py:468-474` | extend 加 5 new emit lines |
| `inputSchema` declaration | `mcp_server.py:1227-1229` | extend 加 5 new properties |

---

## 8. Risks + Mitigations

| Risk | Mitigation |
|---|---|
| 真 promotion rule 真 user 真期望 differ | promote_after 真 user-overridable 真 frontmatter · default table 真 spec verbatim |
| 真 forget_at 真 误删用户数据 | archive flag 真 soft-delete · 不 hard-delete · opt-in via env COMPASS_LIFECYCLE_FORGET=1 |
| 真 backward compat 真 break | 5 fields 真 all optional · default values 真 deterministic · existing entries 真 default 真 working tier |
| 真 cascade closure 真 regression | smoke test #5 真 explicit guard · 真 不动 transitive_close 真 existing function |
| anchor #5 重复造轮子 | reuse 真 existing parser/scanner/inputSchema pattern · 真 audit table §7 |

---

## 9. paper3 reframe novelty

真 paper3 真 next ship · 加 §6.2 真 verbatim:

> "We propose schema-declared, write-time-LLM-free 4-tier promotion + Ebbinghaus decay. No open-source memory system audited in §2(mem0, Letta, Cognee, Zep, MemOS, smrti, MemGPT, OpenViking, GBrain, llm-wiki2, agentmemory)exposes these as first-class frontmatter fields with deterministic promotion rules. agentmemory(LongMemEval-S 95.2% R@5)真 4-tier 真 production but compress LLM-required(AUTO_COMPRESS flag). llm-wiki2 真 mention Ebbinghaus + 4-tier but defers promotion to LLM."

真 cite 加:
- agentmemory 15.3K stars · LongMemEval-S 95.2% R@5 baseline 真比较
- llm-wiki2 rohitg00 gist · Ebbinghaus verbatim mention · 4-tier names verbatim

---

## 10. Outstanding(non-blocking · 真 next phase)

- Phase 2 · agentmemory fuse(9 hooks + iii worker plug + RRF k=60)· 真 plan §4 Phase 2
- Phase 3 · paper3 v2 reframe · 加 agentmemory cite · 真 plan §4 Phase 3
- 真 Gemini Flash $0 judge 真 benchmark(LongMemEval-S · service account chunxiao-vm-260414-de9e73f4697d.json reuse)

---

## Appendix · session_writer.py:46-67 真 verbatim baseline(174034e)

```
---
name: <8-15 字总结 · 中文优先>
description: <≤120 字 · 这次 session 解决了什么问题或学到什么>
type: <bugfix | feature | refactor | discovery | decision | change>
concept: <gotcha | pattern | trade-off | how-it-works | why-it-exists | problem-solution | what-changed>
drift: <green | yellow | red>
drift_signals: [<0-3 条 ≤30 字 · 引号 · 空数组 []>]
depends_on: [<0-5 file basenames · v1.7 MEME-extension>]
declaration_type: <cascade | absence | deletion | none · default none · v1.7 MEME-extension>
supersedes: [<only when declaration_type=deletion · v1.7 MEME-extension>]
# v1.7.1 lifecycle extension(NEW):
tier: <working | episodic | semantic | procedural · default working>
decay_rate: <0.0-1.0 · default 0.5 · Ebbinghaus exponential>
forget_at: <ISO8601 · null = never>
promote_after: <"7d" or "5_access" · default by tier>
reinforce_count: <int · default 0 · access event 累计>
contracts: <可选>
  - id: cnt_xxxxxxxx
    ...
---
```
