# Compass Release Control Plane Design

**Date:** 2026-08-01  
**Status:** Approved for P0-P1 implementation  
**Base:** `codex/pr-s4-3-verdict-attestation` at `26174d6`

## 1. Goal

Make one installed Compass release identifiable, reproducible, secret-clean,
switchable, and rollback-safe before using S4 experience data to change recall
or routing behavior.

This design turns five related risks into one small control plane:

1. source/runtime version split;
2. branch and worktree divergence;
3. credential leakage through defaults or release artifacts;
4. unowned daemon and MCP processes;
5. policy promotion without measured positive value.

## 2. Design principles

- A running source checkout is not a release artifact.
- A worktree is never release authority.
- The active release must be explainable from machine-readable evidence.
- Runtime switching must be atomic and reversible.
- Missing or inconsistent provenance fails closed.
- The BGE daemon is a singleton; MCP stdio servers are per-client children.
- S4 data may propose a policy, but may not promote itself.
- `flat` remains the default until held-out replay proves positive value without
  protected-class regression.
- No new database, long-lived brain, model training, or Feishu integration is
  introduced by P0-P1.

## 3. Rejected alternatives

### Patch the installed source tree in place

This is fast but preserves the root failure: Codex and Claude execute mutable
source files whose version, local edits, and security state can diverge.

### Rewrite Compass from scratch

This would discard working MCP, recall, drift, and S4 behavior without solving
release authority first. It also makes benchmark changes impossible to
attribute.

## 4. Chosen architecture

### 4.1 Immutable release train

Only a clean Git commit may produce a candidate. The candidate contains:

- a wheel;
- a deterministic `release-manifest.json`;
- build and test evidence referenced by the manifest;
- a release identifier derived from version, Git SHA, and wheel SHA-256.

The manifest records at minimum:

```json
{
  "schema_version": "compass.release.manifest.v1",
  "release_id": "compass-2.3.0-<git12>-<wheel12>",
  "version": "2.3.0",
  "git_sha": "<40 lowercase hex>",
  "wheel_filename": "nautilus_compass-2.3.0-py3-none-any.whl",
  "wheel_sha256": "sha256:<64 lowercase hex>",
  "python_requires": ">=3.9",
  "schema_versions": {
    "experience_packet": "compass.experience_packet.v0",
    "flywheel_event": "compass.flywheel.event.v1",
    "verdict_packet": "compass.verdict.packet.v0"
  },
  "default_policy": "flat",
  "built_at": "<UTC RFC3339>",
  "build_tool": "compass-release-control-v1"
}
```

Unknown keys, malformed hashes, a dirty source tree, a version mismatch, or a
wheel hash mismatch block staging.

### 4.2 Dual-slot runtime

The local runtime root has two mutable slot names, but every release directory
inside a slot is immutable after verification:

```text
~/.nautilus-compass/runtime/
  current.json
  receipts/
  slots/
    a/<release-id>/
      release-manifest.json
      artifact.whl
      venv/
    b/<release-id>/
      release-manifest.json
      artifact.whl
      venv/
```

`current.json` contains only the active slot, release identifier, manifest hash,
and generation counter. It is written to a sibling temporary file, flushed, and
atomically replaced. A switch never mutates the active release.

The inactive slot is staged and verified first. A failed verification leaves
`current.json` untouched. The previous pointer is retained in the signed-off
runtime receipt so rollback is another atomic pointer switch.

### 4.3 Stable launcher

Agent configurations must point to one stable launcher, never a repository
checkout or slot implementation file. The launcher:

1. reads `current.json`;
2. validates its strict schema and manifest binding;
3. verifies the stored wheel hash;
4. executes the active slot interpreter and installed Compass entrypoint;
5. exits non-zero without fallback if any binding is invalid.

The launcher does not choose a branch, repair a release, start a daemon, or
silently fall back to mutable source.

### 4.4 Runtime receipt

Every stage, activation, rollback, or blocked action emits one append-only JSON
receipt under `receipts/`:

```json
{
  "schema_version": "compass.runtime.receipt.v1",
  "operation": "stage|activate|rollback|blocked",
  "release_id": "<release-id>",
  "manifest_sha256": "sha256:<64 lowercase hex>",
  "previous_release_id": "<release-id-or-null>",
  "generation": 1,
  "status": "verified|active|rolled_back|blocked",
  "reason_code": "<controlled-code>",
  "created_at": "<UTC RFC3339>"
}
```

Receipts contain no credentials, environment dumps, raw configuration, user
identities, or prompt content.

### 4.5 Doctor contract

`nautilus-compass doctor --json` is the one diagnostic entrypoint. It is
read-only and reports:

- active release identifier, version, Git SHA, manifest and wheel hashes;
- pointer/manifest/wheel integrity;
- Python executable and supported version;
- MCP tool-list smoke result and count;
- BGE daemon endpoint ownership and health;
- MCP process rows with PID, parent PID, parent liveness, start time, and
  attributable client when available;
- default runtime policy;
- bounded warnings and failure codes.

It never prints environment values, command-line secrets, database URLs, or
raw client configuration.

## 5. Security boundary

P0 treats any credential previously committed or copied into a runtime file as
compromised. Source cleanup does not revoke it; rotation is an operational gate.

Release gates scan three surfaces independently:

1. tracked source and service templates;
2. built wheel contents and package metadata;
3. generated runtime manifest, pointer, launcher configuration, and receipts.

Credential-bearing URLs, password/token assignments, permissive authentication
fallbacks, and secret-like values in build metadata block release. Test fixtures
may use clearly synthetic sentinel values only. Scanner findings are reported as
file/rule identifiers without echoing matched values.

The runtime must fail closed when a required secret is absent. P0-P1 never
creates, rotates, retrieves, or logs a production secret itself; rotation and
revocation are separately evidenced operations.

## 6. Process ownership model

- Exactly one process may own the configured BGE daemon listener.
- MCP stdio servers are expected to be one per live client session.
- An MCP process is healthy when its parent is live, its executable belongs to
  the active release, and its start time is not older than its parent.
- An MCP process is suspect when the parent is absent or the executable belongs
  to a retired release.
- Doctor only reports suspects in P1. Automated termination is deferred until a
  grace-period policy has replay evidence.
- Restart loops use bounded exponential backoff; no `pkill -f` or broad process
  termination is allowed.

## 7. Learning-policy containment

P0-P1 does not alter PoI, recall ranking, tiering, capsule generation, or route
selection. The runtime manifest pins `default_policy` to `flat`.

Later S4 candidates must run in shadow mode. Promotion requires:

- held-out replay with query-class breakdown;
- no statistically meaningful protected-class regression;
- positive retrieval delta under a predeclared threshold;
- no material error-rate or P95 latency regression;
- reproducibility across at least two independent runs;
- an independent verdict, not action-agent self-approval.

Failed candidates are retained as evidence but never become default behavior.

## 8. Failure handling

| Failure | Required behavior |
|---|---|
| Dirty source | Refuse to build |
| Manifest/hash mismatch | Refuse to stage or launch |
| Candidate smoke failure | Keep current pointer unchanged |
| Activation interruption | Atomic replace yields old or new complete pointer |
| Active release fails after switch | Roll back to previous verified pointer |
| Missing required secret | Fail closed without printing the value |
| Duplicate release | Idempotent no-op or controlled conflict |
| Unknown receipt/manifest key | Reject |
| Orphan MCP process | Report; do not kill in P1 |
| Candidate policy lacks uplift | Keep `flat` |

## 9. P0-P1 acceptance criteria

1. A clean S4-3 commit builds a wheel and deterministic strict manifest.
2. The same input produces identical semantic manifest content, excluding the
   explicit build timestamp.
3. Dirty source, mismatched version, unknown keys, and altered wheel all fail.
4. A candidate installs into the inactive slot and passes isolated import,
   MCP initialize/tool-list, and S4 module smoke tests.
5. Activation changes only the atomic pointer and emits a receipt.
6. Rollback restores the preceding verified release without reinstalling it.
7. Agent config generation targets the stable launcher rather than repository
   `mcp_server.py`.
8. Release scans find no credential-bearing URL in tracked production surfaces,
   generated artifacts, or wheel contents.
9. Existing 17-tool MCP behavior and a bounded recall probe are preserved.
10. `doctor --json` reports exact active provenance and process ownership without
    secret values.
11. All existing S4/GEP tests remain green.
12. No push, merge, deployment, live config mutation, or process termination is
    performed as part of implementation tests.

## 10. Deferred work

- online credential rotation and revocation;
- changing live Claude/Codex configurations;
- automatic orphan-process termination;
- release signing or transparency-log publication;
- S4-4 shadow policy and benchmark promotion;
- capsule generation, PoI ranking changes, or model-weight training;
- public SOTA claims or paper results.

