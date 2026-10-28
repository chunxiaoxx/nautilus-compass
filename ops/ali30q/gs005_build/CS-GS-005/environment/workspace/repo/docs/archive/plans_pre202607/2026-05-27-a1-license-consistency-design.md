# A1 · License Consistency Sweep · Design

> Path A W1 item A1 · brainstorming output · 2026-05-27
> Supersedes the 5/27 handoff line 82 recommendation ("add root LICENSE pointing to MIT"),
> which was based on a stale read of the repo (root LICENSE already exists as Apache 2.0).

## Context

OSS pivot for Nautilus Soul (audit service + recursive closed-loop engine) is the Path A focus
for W1-3 (5/27 - 6/20) to land anchor #2 (first paid customer · deadline 6/20 · 25 days remaining).
A1 is the cleanest entry: zero-coupling decision, unblocks A2 README hero (cites license),
and forces explicit reconciliation of license metadata before A7 PyPI publish.

## Audit · current state

| File | Current license signal | Notes |
|---|---|---|
| `LICENSE` (root) | **Apache 2.0** full text · Copyright 2026 Nautilus Contributors | Source of truth |
| `README.md` line 7 | `License-Apache%202.0-blue.svg` badge | Already aligned |
| `pyproject.toml` (root) | No `license` field | Missing · would default to nothing on PyPI |
| `phase3/sdk/setup.py:15` | classifier `MIT License` | Inconsistent |
| `phase3/cli/setup.py:17` | `license="MIT"` | Inconsistent |
| `phase3/cli/setup.py:29` | classifier `MIT License` | Inconsistent |
| `phase3/backend/sdk/python/setup.py:23` | classifier `MIT License` | Inconsistent |

Split-brain count · 4 inconsistent + 1 missing field.

## Decision (locked with user)

**Apache 2.0 全部统一**. Reasons:
- Patent grant matters for an audit service (defensive posture against patent troll claims on
  novel audit/scoring methodology).
- Root LICENSE + README badge are already Apache 2.0 · zero work to ratify.
- Inbound dependency posture: `httpx` (Apache 2.0), `pytest` (MIT), `black` (MIT) all
  compatible with downstream Apache 2.0.

Rejected alternatives:
- **MIT 全部统一** · would require rewriting root LICENSE + README badge · loses patent grant.
- **Explicit split (root Apache / phase3 MIT)** · narrative cost on dev.to / Show HN ("why two
  licenses?") · zero technical upside.

## Scope

In-scope edits (5 total):

1. `phase3/sdk/setup.py:15` · `MIT License` → `Apache Software License`
2. `phase3/cli/setup.py:17` · `license="MIT"` → `license="Apache-2.0"`
3. `phase3/cli/setup.py:29` · `MIT License` → `Apache Software License`
4. `phase3/backend/sdk/python/setup.py:23` · `MIT License` → `Apache Software License`
5. `pyproject.toml` · insert `license = "Apache-2.0"` (PEP 639 SPDX form) into `[project]` table

Out of scope:
- Root `LICENSE` file (already Apache 2.0 · do not modify)
- `README.md` badge (already Apache 2.0 · do not modify)
- `NOTICE` file (defer · Apache 2.0 only requires NOTICE if upstream had one · we are origin)
- `CONTRIBUTING.md` / CLA boilerplate (defer to A6 outreach kit refresh)
- `phase3/CLAUDE.md` and any other internal doc license string grep (defer to A2)
- `alembic/versions/` (cross-dialog · user hard constraint)
- Path B (Gap 3-5 · deferred to W4)

## Rationale · why 5 edits not 3

The user-affirmed minimum (4 setup.py edits) leaves the root `pyproject.toml` without a
`license` field. A7 (W2 · PyPI publish) will hit this anyway · adding the line now is 1 LOC
of marginal cost and prevents a follow-on commit. First-principle constitution check
(2026-05-22):

- 最简单 · single commit covers full sweep · no half-done state
- 最直接 · attacks split-brain at the root, not just the visible classifier strings
- 成本最低 · 5 edits · ~20 min · 0 test impact
- 维护最简单 · A7 PyPI publish does not need to revisit license metadata

## Verification

Post-edit sanity checks (no test runs needed since edits are metadata-only):

```
# Should return 0 hits (excluding node_modules)
grep -rn "MIT License" phase3/ --include="setup.py"

# Should return Apache string in 3 files
grep -n "Apache Software License" phase3/sdk/setup.py phase3/cli/setup.py phase3/backend/sdk/python/setup.py

# Should return Apache-2.0
grep -n "license" pyproject.toml
```

PEP 639 SPDX `license = "Apache-2.0"` form is supported by setuptools >= 77 (released
2025-01) · root `pyproject.toml` line 2 already requires `setuptools>=45` which would
need bumping. Decision: bump `setuptools>=77` in the same commit (1-LOC change · removes
deprecation warning on modern Python toolchains).

## Test impact

Zero. All 5 edits are metadata. The 198 engine tests + 2 CLI tests do not exercise license
strings. No re-run needed before commit (optional sanity rerun pre-push acceptable).

## Risk

Negligible.

- PEP 639 SPDX form is the current standard (PEP ratified · trove classifier deprecated path
  but still accepted).
- setuptools 77 bump is forward-compatible · no breaking API used by phase3 setup.py.
- 0 downstream dependent code reads `license=` field at runtime.

Rollback: single `git revert` on the commit · no schema / data / runtime state changes.

## Deliverable shape

- 1 commit · message draft:
  ```
  chore(license): A1 · sweep phase3 setup.py + pyproject.toml to Apache 2.0

  Aligns 3 phase3 setup.py files and root pyproject.toml with the existing
  Apache 2.0 root LICENSE. Removes the MIT/Apache split-brain that the
  5/27 handoff misidentified. Zero runtime impact · metadata-only.

  Closes Path A W1 item A1.
  ```
- 1 design doc · this file
- writing-plans skill handoff for a trivial single-phase impl plan + verification grep

## Next step

Invoke `writing-plans` skill to produce `docs/plans/2026-05-27-a1-license-consistency-plan.md`
with the 5 edits broken into ordered steps + verification grep + commit step. No subagents
needed · single-session ship · ~20 min total.
