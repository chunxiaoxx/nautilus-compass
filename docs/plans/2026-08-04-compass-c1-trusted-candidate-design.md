# Compass C1 Trusted 2.3 Candidate Design

**Status:** Approved direction on 2026-08-04. This design authorizes work only
inside the isolated `codex/compass-c1-trusted-candidate` worktree. It does not
authorize deployment, push, merge, mutation of the installed 2.2 plugin, or
changes in Platform, Super Agent, or FDE repositories.

## Objective

Turn the already-tested Compass S4 and Learning Kernel work into one clean,
reproducible 2.3 candidate whose source, wheel, runtime slot, active process,
policy, and rollback target can all be read back mechanically.

C1 is complete only when a candidate built from a fresh `origin/main` base:

- contains the independently verified S4 verdict path and the R0 evaluation
  kernel without inheriting the full 137-commit experimental branch;
- produces an immutable manifest bound to the exact wheel and Git commit;
- stages, activates, diagnoses, and rolls back in a temporary dual-slot root;
- passes installed-wheel GEP, Learning Kernel, MCP, and bounded recall smoke;
- reports `default_policy=flat` and makes no improvement or SOTA claim;
- passes relevant pytest, Ruff, source/wheel secret scans, and independent
  review with High=0 and Medium=0.

## Verified Starting Point

The candidate worktree starts clean at `origin/main` commit
`81feef206df3b7f744288c4f9a3f10333f7f2f9a`. The focused mainline baseline is
150 passing tests:

```powershell
python -m pytest tests\gep tests\test_cli.py -q
```

The installed plugin is intentionally out of scope. It is a dirty 2.2.0 tree at
`C:\Users\chunx\.claude\plugins\nautilus-compass`, and the active daemon on
port 9876 runs from that tree. C1 must never import, clean, stop, overwrite, or
reconfigure it.

## Adoption Map

### Linear, reviewable donor stack

`origin/main` is an ancestor of `codex/pr-s4-3-verdict-attestation`, which is an
ancestor of `codex/compass-release-control-plane`:

```text
origin/main @ 81feef2
  + 16 S4 verdict commits -> 26174d6
  +  9 release commits    -> b6ca9c1
```

The 16-commit S4 group adds strict verdict packets, linked event persistence,
independent admission, a pure state reducer, wheel/security regression tests,
and Python 3.13 packaging support. The 9-commit release group adds:

- `15911cc` strict immutable release manifest;
- `a2eb9ba` source and wheel credential boundary;
- `6a13cee` atomic dual-slot stage/activate/rollback;
- `fcea312` fail-closed stable launcher;
- `2d2b7a6` durable MCP wheel packaging;
- `b6ca9c1` read-only runtime provenance and process ownership doctor.

Because these 25 commits form a direct linear descendant of `origin/main`, C1
preserves them as commits rather than copying files or rewriting behavior.

### Learning Kernel donor boundary

`codex/s4-mainline-convergence@3e7aa17` is 137 commits ahead of `origin/main`
and is not a descendant of the reviewed release stack. It must not be merged or
cherry-picked wholesale.

The R0 package itself has a narrow runtime dependency surface:

- `gep.experience_packet` and `gep.poi_rerank`, already on main;
- `gep.verdict_packet`, supplied by the 16-commit S4 group;
- `benchmarks.poi_gate2.canonical`;
- one dependency-free shared `percentile_95` helper;
- `benchmarks.poi_gate2.dogfood_evidence` only for blocked dogfood projection;
- PyNaCl for pinned Ed25519 verdict verification.

C1 therefore ports the R0 commits from `816df5c` through `3e7aa17` only after
supplying and testing canonical hashing, blocked dogfood evidence, and the
shared statistics helper. It does not import the donor `action_metrics` module
because that would pull in the complete action-projection dependency graph. It
also does not import
the live-agent provider harness, D0/D1 experimental orchestration, repair
windows, generated history, or any Platform/Super Agent adapter.

### Assets deliberately not adopted

- the 137-commit branch as a whole;
- provider probes as positive learning evidence;
- live-agent credentials, model routing, or API spend;
- automatic capsule generation or policy promotion;
- FDE-specific envelopes, receipts, or business state;
- old mutable PoI sidecars as verdict authority;
- the installed plugin's dirty source or process state;
- public SOTA language.

## Candidate Architecture

```text
clean origin/main
  -> reviewed S4 verdict stack
  -> reviewed release-control stack
  -> minimal canonical/statistics/dogfood support
  -> R0 evaluation-only kernel
  -> clean wheel + strict manifest
  -> temporary inactive slot
  -> isolated MCP/recall smoke
  -> atomic activation + doctor read-back
  -> rollback to previous verified slot
```

Release control and learning policy remain orthogonal. The release manifest pins
the policy to `flat`; R0 can only emit `candidate_only`. No successful C1 test
may mutate the production memory index or installed runtime.

## Evidence and Claim Boundary

The final evidence bundle must distinguish:

- source tests from installed-wheel tests;
- release integrity from recall quality;
- deterministic R0 mechanism delta from real-agent uplift;
- cache-hot latency from uncached latency;
- local candidate proof from production adoption.

The existing R0 result (`candidate_delta=0.25`, protected delta `0`, poison
admission `0`) is a donor result, not evidence for the newly assembled
candidate. C1 regenerates and rebinds evidence to the candidate commit and
wheel.

## Stop Conditions

Stop and report instead of widening scope when:

- the reviewed capabilities require importing the complete 137-commit branch;
- a donor commit changes live runtime, credentials, or external state;
- a manifest cannot bind the exact built wheel and Git commit;
- an installed-wheel test silently imports the source checkout;
- the default policy is not byte-for-byte `flat`;
- a protected class regresses, poison is admitted, or independent verdict
  authentication can be caller-supplied;
- verification requires modifying Platform, Super Agent, FDE, or the installed
  2.2 plugin.
