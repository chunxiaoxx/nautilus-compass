# Compass Release Control Plane Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a strict, testable release control plane that produces an immutable Compass wheel manifest, stages it into an inactive runtime slot, switches and rolls back atomically, exposes read-only provenance diagnostics, and prevents mutable-source or secret-bearing releases.

**Architecture:** Keep release metadata and slot operations in small standard-library Python modules packaged with Compass. Copy one dependency-free launcher into a stable runtime root; agent configurations target that launcher, which validates the active pointer and artifact binding before executing the slot interpreter. Reuse existing S4 package secret guards and CLI dispatch, keep `flat` pinned, and add no database or daemon.

**Tech Stack:** Python 3.9-3.13 standard library, pytest, `venv`, `pip`, setuptools wheel, PowerShell read-only process probe on Windows, GitHub Actions.

---

### Task 1: Strict release manifest and provenance

**Files:**
- Create: `release_manifest.py`
- Create: `tests/release/test_release_manifest.py`
- Modify: `pyproject.toml`

**Step 1: Write failing schema tests**

Cover:

- exact manifest keys and `compass.release.manifest.v1`;
- lowercase 40-character Git SHA;
- `sha256:<64 lowercase hex>` wheel digest;
- filename-only wheel name;
- version equality with package metadata input;
- allowed schema-version mapping;
- `default_policy == "flat"`;
- rejection of unknown/missing keys and malformed timestamps;
- canonical JSON round trip;
- release ID derived from version, Git SHA, and wheel digest;
- semantic reproducibility with an injected timestamp.

Run:

```powershell
uv run --no-project --python 3.13 --with pytest python -m pytest tests/release/test_release_manifest.py -q
```

Expected: FAIL because `release_manifest` does not exist.

**Step 2: Implement the minimal immutable value object**

Add a frozen dataclass with `from_mapping`, `from_json_bytes`, `to_mapping`,
`canonical_bytes`, and `build` constructors. Hash bytes with `hashlib.sha256`.
Validate strict types rather than coercing values.

**Step 3: Verify green and compatibility**

Run the focused test, then:

```powershell
uv run --no-project --python 3.9 --with pytest python -m pytest tests/release/test_release_manifest.py -q
uv run --no-project --python 3.13 --with pytest python -m pytest tests/gep -q
```

Expected: focused tests pass on 3.9 and 3.13; 355 existing GEP tests pass.

**Step 4: Commit**

```powershell
git add release_manifest.py tests/release/test_release_manifest.py pyproject.toml
git commit -m "feat(release): add strict immutable manifest"
```

### Task 2: Source and artifact security gates

**Files:**
- Create: `release_security.py`
- Create: `tests/release/test_release_security.py`
- Modify: `tests/gep/test_packaged_secret_boundary.py`
- Modify only if a failing gate proves a production issue: `middleware/auth.py`, `compass_http_v09.py`, approved `ops/*` release surfaces

**Step 1: Write failing security-gate tests**

Use synthetic temporary files to prove detection without storing a real secret.
Cover:

- credential-bearing database URL;
- private-key marker;
- non-empty literal assigned to a sensitive name;
- non-empty sensitive keyword argument;
- service-template environment line containing a literal credential;
- clean environment-variable lookup;
- finding output includes only path, line, and rule code, never matched value;
- source allowlist excludes tests, examples, archives, Git metadata, and user
  configuration/history;
- wheel ZIP member scan rejects dangerous content and path traversal.

Run the focused test and observe the expected import failure.

**Step 2: Implement the scanner**

Reuse the AST logic already proven in
`tests/gep/test_packaged_secret_boundary.py`. Return frozen findings containing
only `path`, `line`, and controlled `rule_code`. Add bounded file-size and ZIP
member-count limits.

**Step 3: Run against tracked release surfaces**

Run the scanner only over its explicit repository allowlist. Classify each
finding. Fix only production defaults or fallbacks demonstrated by the gate;
keep clearly synthetic test fixtures out of the release surface rather than
weakening rules.

Expected: zero release-blocking findings.

**Step 4: Commit**

```powershell
git add release_security.py tests/release/test_release_security.py tests/gep/test_packaged_secret_boundary.py <proven-fixes>
git commit -m "security(release): fail closed on credential-bearing artifacts"
```

### Task 3: Dual-slot staging, activation, and rollback

**Files:**
- Create: `runtime_release.py`
- Create: `tests/release/test_runtime_release.py`

**Step 1: Write failing state-machine tests**

Cover:

- strict `current.json` schema;
- initial install chooses slot `a`;
- an active `a` release stages only to `b`, and vice versa;
- manifest and wheel hash verified before any slot mutation;
- candidate staged under `<slot>/<release-id>`;
- duplicate identical stage is idempotent;
- conflicting duplicate fails;
- failed installer leaves the current pointer unchanged;
- activation uses `os.replace` and increments generation;
- rollback restores the exact previous verified binding;
- unknown keys and altered manifests fail closed;
- receipt schemas, controlled reason codes, exclusive creation, and absence of
  secret-bearing fields.

**Step 2: Implement pure validation and filesystem transitions**

Use frozen pointer/receipt dataclasses, same-directory temporary files,
`flush` + `os.fsync`, and `os.replace`. Use dependency injection only for the
external wheel installer; all pointer and artifact behavior must use real
temporary files in tests.

**Step 3: Add one real wheel staging integration test**

Build the project wheel from a clean snapshot, create a temporary venv, install
with `--no-deps`, and prove these imports from outside the checkout:

```python
import gep.experience_packet
import gep.flywheel_event
import gep.flywheel_log
import gep.verdict_packet
```

The integration test may be separately marked `release_integration`, but must
run in the final P1 verification.

**Step 4: Commit**

```powershell
git add runtime_release.py tests/release/test_runtime_release.py
git commit -m "feat(runtime): add atomic dual-slot release switching"
```

### Task 4: Stable fail-closed launcher

**Files:**
- Create: `runtime_launcher.py`
- Create: `tests/release/test_runtime_launcher.py`

**Step 1: Write failing launcher tests**

Cover:

- runtime root supplied explicitly or by `COMPASS_RUNTIME_ROOT`;
- valid pointer resolves the slot interpreter and module entrypoint;
- invalid pointer, missing manifest, changed wheel, missing interpreter, and
  release-ID mismatch exit non-zero;
- no fallback to repository source or another slot;
- command construction uses an argument list, never a shell string;
- diagnostic errors contain controlled reason codes and no environment values;
- dry-run returns the resolved executable and redacted arguments without
  starting a process.

**Step 2: Implement a dependency-free launcher**

The file may import only Python standard-library modules and the strict manifest
module copied beside it during installation. Normal execution uses `os.execv`
on POSIX and `subprocess.call` with an argument list on Windows.

**Step 3: Verify from a directory outside the checkout**

Stage the real wheel from Task 3, copy launcher files into a temporary stable
root, activate the slot, and run a bounded MCP initialize/tools-list smoke.

Expected: initialize succeeds; tool count matches the release contract.

**Step 4: Commit**

```powershell
git add runtime_launcher.py tests/release/test_runtime_launcher.py
git commit -m "feat(runtime): add stable manifest-bound launcher"
```

### Task 5: Read-only doctor and process ownership

**Files:**
- Create: `runtime_doctor.py`
- Create: `tests/release/test_runtime_doctor.py`
- Modify: `cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Write failing doctor-contract tests**

Cover:

- exact top-level JSON keys and controlled status codes;
- active release provenance and pointer/manifest/wheel integrity;
- supported Python result;
- singleton daemon listener states: absent, one owner, multiple owners;
- MCP rows distinguish live-parent, missing-parent, and retired-release cases;
- process provider is bounded and read-only;
- environment values, command-line arguments, database URLs, and raw config
  bodies are absent from output;
- `nautilus-compass doctor --json` dispatch and exit codes.

**Step 2: Implement provider boundaries**

Keep report assembly pure. The Windows provider may call a fixed PowerShell
`Get-CimInstance Win32_Process` query and parse bounded JSON; Linux may use
`/proc`. Providers return only PID, parent PID, executable path, and creation
time. Do not add process termination or restart behavior.

**Step 3: Add MCP/daemon bounded probes**

Use short timeouts. Tool-list smoke runs against the active slot only. Daemon
probe checks the configured loopback endpoint without starting it.

**Step 4: Commit**

```powershell
git add runtime_doctor.py tests/release/test_runtime_doctor.py cli.py tests/test_cli.py
git commit -m "feat(runtime): report active provenance and process ownership"
```

### Task 6: Safe agent configuration generation

**Files:**
- Modify: `scripts/install_to_agent.py`
- Create: `tests/release/test_install_to_agent_runtime.py`
- Modify: `INSTALL.md`

**Step 1: Write failing configuration tests**

Cover:

- generated MCP block targets the stable launcher and absolute bootstrap
  interpreter;
- no path contains repository `mcp_server.py`;
- dry-run makes no filesystem changes;
- existing config is backed up before a controlled write;
- invalid JSON remains untouched;
- runtime not staged returns an actionable error rather than source fallback;
- no environment values are copied into generated config except explicit
  non-secret encoding settings.

**Step 2: Implement minimal migration behavior**

Add explicit `--runtime-root`; derive the launcher path from that root. Preserve
existing target discovery, per-file backup, and dry-run behavior. Do not mutate
the user's live config during tests or this implementation session.

**Step 3: Commit**

```powershell
git add scripts/install_to_agent.py tests/release/test_install_to_agent_runtime.py INSTALL.md
git commit -m "feat(install): bind agents to stable Compass runtime"
```

### Task 7: Reproducible release command and CI gate

**Files:**
- Create: `release_cli.py`
- Create: `tests/release/test_release_cli.py`
- Modify: `cli.py`
- Modify: `tests/test_cli.py`
- Modify: `.github/workflows/release.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `pyproject.toml`

**Step 1: Write failing CLI tests**

Cover `build`, `stage`, `activate`, `rollback`, and `status --json`. Build must
reject a dirty tree, version/tag mismatch, secret-scan findings, build failure,
or unexpected wheel count. State-changing commands require explicit paths and
never infer a repository from the current directory.

**Step 2: Implement command orchestration**

Compose Tasks 1-4 without duplicating validation. Build in a clean temporary
snapshot, not the working directory, and emit wheel plus manifest into an
explicit output directory. Use bounded subprocess timeouts and argument lists.

**Step 3: Harden CI/release workflow**

Update tag matching for 2.x, run the Python 3.9/3.13 S4 matrix, security gate,
clean wheel build, installed-wheel smoke, and attach wheel plus manifest to the
release. The workflow must not publish when any gate fails.

**Step 4: Commit**

```powershell
git add release_cli.py tests/release/test_release_cli.py cli.py tests/test_cli.py .github/workflows/release.yml .github/workflows/ci.yml pyproject.toml
git commit -m "feat(release): orchestrate reproducible Compass candidates"
```

### Task 8: End-to-end cutover and rollback rehearsal

**Files:**
- Create: `tests/release/test_release_e2e.py`
- Modify: `docs/plans/2026-08-01-compass-release-control-plane-design.md` only for verified deviations
- Create: `docs/evidence/compass_release_control_p1.json`

**Step 1: Write the failing E2E test before any E2E helper**

The test must:

1. build a clean candidate;
2. scan source and wheel;
3. stage to slot `a`;
4. activate and read back exact provenance;
5. run installed-wheel S4 import and MCP tool-list smoke;
6. stage a second synthetic candidate to slot `b`;
7. activate it;
8. roll back to slot `a` without reinstalling;
9. prove malformed and tampered candidates never change `current.json`.

**Step 2: Run complete verification**

```powershell
uv run --no-project --python 3.13 --with pytest --with pynacl python -m pytest tests/release tests/gep tests/test_cli.py -q
uv run --no-project --python 3.13 --with ruff python -m ruff check release_manifest.py release_security.py runtime_release.py runtime_launcher.py runtime_doctor.py release_cli.py scripts/install_to_agent.py tests/release tests/test_cli.py
uv run --no-project --python 3.13 --with build python -m build
git diff --check origin/main...HEAD
git status --short --branch
```

Repeat schema/unit tests on Python 3.9. Record exact interpreter versions,
counts, hashes, and smoke results in the evidence JSON. Do not record machine
credentials, user paths beyond repository-relative evidence paths, or process
command lines.

**Step 3: Independent review**

Request separate specification and code-quality reviews. Required review areas:

- no mutable-source fallback;
- no secret values in errors or receipts;
- atomic activation and exact rollback binding;
- Windows path and process behavior;
- no PoI/recall/routing/capsule behavior change;
- no live config, process, network service, push, merge, or deployment side
  effect.

Fix every Critical/High/Medium issue with a failing regression test first and
repeat the full verification set.

**Step 4: Commit evidence**

```powershell
git add tests/release/test_release_e2e.py docs/evidence/compass_release_control_p1.json <reviewed-fixes>
git commit -m "test(release): prove cutover and rollback rehearsal"
```

## Completion boundary

P0-P1 is complete only when the isolated branch has reproducible build evidence,
all tests and scans pass, and a temporary-runtime cutover plus rollback succeeds.
Completion does not authorize changing the installed plugin, Claude/Codex config,
live processes, remote services, GitHub branches, or release tags.
