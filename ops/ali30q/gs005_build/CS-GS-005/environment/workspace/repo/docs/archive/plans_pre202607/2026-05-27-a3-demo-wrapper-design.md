# A3 · Nautilus Soul Demo Wrapper · Design

> Path A W1 item A3 · brainstorming output · 2026-05-27
> Follows A1 (license consistency · commit `e8eb4f24c`).

## Context

Path A goal: land first paid customer by 2026-06-20 (anchor #2 · 25 days remaining).
A3 ships a 1-command demo that lets an HN / dev.to reader verify "engine actually
self-modifies" in 60 seconds without setting up API keys, databases, or LLM
credentials. The demo is the trust-anchor for A4 article + A5 Show HN.

5/27 handoff line 50 referenced "cycle 17 dogfood" — this was aspirational
numbering. Actual master tip has cycle 5 + cycle 9 dogfood commits as the
exemplars. Demo replays both.

## Decision summary (locked with user · 5/27 brainstorming)

- Demo mode = **canned replay** (no live LLM · 0 deps · 0 API keys · 0 internet)
- Hero cycles = **cycle 5 + cycle 9 serial** (~60s total · stronger evidence chain than single)
- Distribution surface added = **asciinema cast** only (GIF / colored UX / inline ASCII block all deferred)

## Audience model

External developer arrives from HN comment / dev.to article / Twitter post.
- Patience: ~60s before tab close
- Trust: low (skeptical of AI demos)
- Setup willingness: minimal (won't paste API key on first encounter)
- What proves the product: real git commits external user can independently verify

## Demo content · two cycles serial

Each cycle prints 6 sections. Total runtime ~60s.

### Cycle 5 · engine __main__ runner (~30s)

```
─ CYCLE 5 · engine __main__ runner ─

[1/6] Task   engine needs a standalone CLI runner (python -m engine <task>)
[2/6] Gen    LLM generated phase3/backend/engine/__main__.py (29 LOC)
[3/6] Check  6 checks run · all PASS · syntax_python · line_count · ...
[4/6] Ship   git commit 572547e7d · 2026-05-24 07:39 PDT
[5/6] Verify https://github.com/chunxiaoxx/nautilus-core/commit/572547e7d
[6/6] Live   $ python -m engine 'hello world'  # this file exists NOW
```

### Cycle 9 · text_utils.truncate (~30s)

Same structure, plus retry-heal narrative in [3/6]:

```
[3/6] Check  attempt 1: FAIL (line_count guard: shrink 0.42 < 0.85)
             attempt 2 after LLM re-prompt: PASS · 8 checks all green
```

Then [4/6] commit `9248e84c5` + [5/6] github verify URL + [6/6] live invocation.

### Footer

```
Both commits verifiable: gh log on this repo · 9248e84c5 · 572547e7d
Try live: nautilus code "your task" --apply --commit-msg "..."
```

## Invocation paths

| Scenario | Command |
|---|---|
| Fresh clone (recommended entry) | `python demo.py` (root shim) |
| Pre-pip-install (alt) | `python phase3/cli/nautilus_cli/__main__.py demo` |
| Post `pip install -e phase3/cli/` | `nautilus demo` |
| Post A7 PyPI publish | `pipx run nautilus-soul demo` |

All 4 paths share one core logic module.

## Implementation locations

- `phase3/cli/nautilus_cli/demo.py` (new · ~80 LOC · stdlib only)
  - `CYCLES` constant: list of cycle metadata dicts (hash, file path, LOC, task description, checks summary, commit timestamp)
  - `run_demo()` function: iterate cycles · for each call `subprocess.run(['git', 'show', '--stat', hash])` for live evidence · print formatted output
  - exit 0 always (informational command)

- `phase3/cli/nautilus_cli/__main__.py` modify · add `demo` subparser
  - ~10 LOC · `p_demo = sub.add_parser("demo", help="...")` · `p_demo.set_defaults(func=cmd_demo)` · `def cmd_demo(args): from .demo import run_demo; return run_demo()`

- `demo.py` (new at repo root · ~10 LOC · convenience shim)
  - Inserts `phase3/cli/` into sys.path · imports run_demo · invokes
  - Lets fresh-clone users skip the install step

- `phase3/cli/tests/test_demo.py` (new · ~30 LOC · 3 cases)
  - test_demo_prints_both_cycles · capsys assert cycle 5 + cycle 9 headers present
  - test_demo_includes_commit_hashes · assert `572547e7d` and `9248e84c5` in stdout
  - test_demo_exits_zero · assert exit code == 0

- `assets/demo.cast` (new · asciinema recording · ~50KB JSON · checked in after first record)
  - Recorded on cloud-server (Windows lacks asciinema native)
  - Uploaded to asciinema.org for public URL
  - URL committed to README in A2 rewrite (not this task)

## Risk + rollback

- Risk: negligible · demo is read-only (reads git history + current repo files) · no mutation · no network in demo execution.
- Recording cast on cloud-server adds 1 SSH session step in writing-plans · low risk · no production touch.
- Rollback: delete 4 new files + revert __main__.py subparser block · single `git revert <hash>`.

## Test impact

- CLI tests: 2 (current) → 5 (after A3) · stdout capture · no external deps.
- Engine tests: 196 unchanged.
- No PG / no LLM API / no network in test path.

## Out of scope (defer)

- `--live` flag for actual LLM call (defer to W2 if user demand surfaces)
- GIF generation from cast (defer to A4 dev.to article)
- README inline ASCII block (defer to A2 README hero rewrite)
- README hero rewrite itself (A2 · separate task)
- Colored / boxed / animated terminal UX (defer to demo v2 · ROI low vs distribution)
- PyPI publish (A7 W2)
- Recording on Windows (impractical · use cloud-server)
- Engine cycle metadata pulled from `engine_cycle_outcomes` table (defer · canned dict is enough for v0)
- alembic / cross-dialog / Path B (user hard constraint)

## Done criteria

1. `python demo.py` from fresh clone prints both cycles + verifiable commits + exits 0
2. `nautilus demo` (post pip install -e) does the same
3. `assets/demo.cast` exists in repo · public asciinema.org URL recorded in commit body
4. 3 new tests in `phase3/cli/tests/test_demo.py` all pass
5. Test count: CLI 2 → 5 · engine 196 unchanged
6. 1 or 2 commits on master · ~115 LOC + cast file

## Deliverable shape

- 1 design doc (this file)
- 1 implementation plan from writing-plans skill
- 4 new files + 1 modify + 1 cast recording
- ~75 min implementation budget (excluding cast record session)

## Next step

Invoke `writing-plans` skill for `docs/plans/2026-05-27-a3-demo-wrapper-plan.md`.
