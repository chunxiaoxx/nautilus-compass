# Production Main Reconciliation

## Purpose

This is a one-time operator runbook for bringing `/home/ubuntu/nautilus-mvp` back to the canonical deployment contract. It is deliberately separate from the deployment script: unexpected production state must be preserved and reviewed, not silently overwritten.

## Observed state on 2026-07-20

- Branch: `soul-audit-increment1`
- Upstream: unset
- Local `main` branch: absent
- Untracked path: `CLOUD_STATE_20260715.md`
- Production `HEAD`: `1eaeba5657a96d8bdf9c225e8ab96ad9bac84d86`
- GitHub `origin/main`: `6ab02ba6e54d526791f58d28f1f82cf6c46e52fb`
- The observed production commit was verified as an ancestor of that `main` by seven commits.
- `nautilus-backend` was active and `/api/platform/convergence` returned HTTP 200.

Re-run every check below. These values are evidence from one observation, not permanent assumptions.

## Phase 1: Read-only evidence

```bash
ssh cloud '
  cd /home/ubuntu/nautilus-mvp
  git status --porcelain=v1 -b
  git rev-parse HEAD
  git branch --show-current
  git rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null || true
  git ls-remote origin refs/heads/main
  systemctl is-active nautilus-backend
  curl -fsS http://127.0.0.1:8000/api/platform/convergence
'
```

If the state differs from the observation above, stop and update the incident record before choosing any mutation.

## Phase 2: Preserve the untracked state file

Create a restricted backup directory and copy the file without removing the original:

```bash
ssh cloud '
  set -eu
  umask 077
  cd /home/ubuntu/nautilus-mvp
  backup_dir=$(mktemp -d /var/tmp/nautilus-reconciliation-20260720TXXXXXX)
  install -m 600 CLOUD_STATE_20260715.md "$backup_dir/CLOUD_STATE_20260715.md"
  cmp -s CLOUD_STATE_20260715.md "$backup_dir/CLOUD_STATE_20260715.md"
  source_hash=$(sha256sum CLOUD_STATE_20260715.md | awk "{print \$1}")
  backup_hash=$(sha256sum "$backup_dir/CLOUD_STATE_20260715.md" | awk "{print \$1}")
  test "$source_hash" = "$backup_hash"
  printf "backup_dir=%s\nsha256=%s\n" "$backup_dir" "$backup_hash"
'
```

Record the unique backup path and verified hash in the incident handoff. Never
reuse or overwrite an earlier evidence directory.

## Mandatory decision gate

**STOP.** An operator must decide whether `CLOUD_STATE_20260715.md` belongs in Git, belongs only in the restricted archive, or needs redaction. Do not remove or move the production copy until that decision is recorded.

The same gate applies if any additional dirty or untracked path appears.

Recommended disposition for the observed file: keep the original only in the
restricted archive, and put a redacted summary plus its SHA-256 in a reviewed
Git change if durable repository history is useful. After that choice is
approved and the archive is re-verified, remove only the named production copy:

```bash
ssh cloud '
  set -eu
  cd /home/ubuntu/nautilus-mvp
  test "$(sha256sum CLOUD_STATE_20260715.md | awk "{print \$1}")" = 0c546cbaa8472d0c84ab44af43e1b1321b36c0f0b53c572511f7c3927baa0513
  rm -- CLOUD_STATE_20260715.md
  test -z "$(git status --porcelain)"
'
```

This exact removal is an approval-gated operator action. Do not generalize it
to a wildcard or repository cleanup command.

## Phase 2b: Restrict the production environment file

The service runs as `ubuntu`, but the observed `.env` was `root:root 0644`.
After the evidence backup is recorded, remove world-readable access while
preserving service readability:

```bash
ssh cloud '
  set -eu
  cd /home/ubuntu/nautilus-mvp
  sudo chown root:ubuntu phase3/backend/.env
  sudo chmod 0640 phase3/backend/.env
  test "$(stat -c "%U:%G %a" phase3/backend/.env)" = "root:ubuntu 640"
  sudo -u ubuntu test -r phase3/backend/.env
  if id nobody >/dev/null 2>&1; then
    ! sudo -u nobody test -r phase3/backend/.env
  fi
'
```

Do not print or source the environment file during this verification.

## Phase 2c: Credential rotation gate

**STOP.** Historical repository state tracked multiple production-shaped
environment backups. The cleanup change removes those files from the reviewed
source tree and ignores future `.env.backup*` files, but deleting them now does
not remove historical copies from Git history. Treat every credential in those
artifacts as exposed, even when its present production use is uncertain.

Complete and record all of the following without copying secret values into a
task, PR, terminal transcript, log, or incident note:

1. Inventory and rotate the database password and verify the service connects
   only with the replacement credential.
2. Rotate JWT and CSRF signing material, revoke the old material where the
   implementation supports revocation, and document the expected session
   impact.
3. Rotate every OAuth client secret, including the tracked Google OAuth
   frontend artifact, and verify each callback flow.
4. Rotate OpenAI and Anthropic API credentials and confirm the old credentials
   are disabled at the providers.
5. Rotate Web3Auth, MetaMask, blockchain, and other wallet/provider secrets or
   private keys represented in the artifacts.
6. Update only the protected production `phase3/backend/.env` through a secure
   operator workflow; do not print, source, or paste its values into shell
   history.
7. Restart `nautilus-backend`, verify localhost and public health/convergence,
   and record non-secret rotation evidence: provider, credential identifier,
   rotation time, revocation status, and verification result.
8. Review GitHub secret-scanning findings and decide whether a coordinated
   history rewrite is required. Do not force-push or rewrite history without a
   separate approved migration plan.

Do not deploy until the rotation evidence shows every exposed credential has
been replaced or explicitly proven inactive and revoked.

## Stale deployment lock recovery

An interrupted deploy can intentionally leave `/tmp/nautilus-deploy.lock`.
Inspect it and the runtime before deciding that it is stale:

```bash
ssh cloud '
  set -eu
  cd /home/ubuntu/nautilus-mvp
  if [ -d /tmp/nautilus-deploy.lock ]; then
    stat /tmp/nautilus-deploy.lock
    cat /tmp/nautilus-deploy.lock/owner
    git status --porcelain=v1 -b
    git rev-parse HEAD
    systemctl is-active nautilus-backend
  fi
'
```

The token format is `owner-host:owner-pid:start-epoch:nonce`. The deployment
controller runs on the owner host, not on production, so a process search on
production cannot prove that the lock is stale. Verify the owner PID and the
originating Codex/CLI task on the owner host. The task must be complete or
explicitly aborted. If the owner host cannot be reached, the PID cannot be
attributed, or the deployment state is ambiguous, keep the lock and handle the
case as an incident.

Do not remove a lock by age or an automatic TTL. After production Git and
service state have been reconciled, record the exact owner token and explicit
operator approval in the incident record. Then compare the unchanged token and
remove only the exact lock files:

```bash
expected_owner='copy-the-exact-owner-token-here'
ssh cloud bash -s -- "$expected_owner" <<'REMOTE'
  set -eu
  expected_owner=$1
  actual_owner=$(cat /tmp/nautilus-deploy.lock/owner)
  test "$actual_owner" = "$expected_owner"
  rm -- /tmp/nautilus-deploy.lock/owner
  rmdir /tmp/nautilus-deploy.lock
REMOTE
```

## Phase 3: Establish tracked main after approval

Only after production is clean and the preservation decision is recorded:

```bash
ssh cloud '
  set -eu
  cd /home/ubuntu/nautilus-mvp
  test -z "$(git status --porcelain)"
  test "$(git branch --show-current)" = soul-audit-increment1
  if git show-ref --verify --quiet refs/heads/main; then
    printf "%s\n" "Local main already exists; stop and reconcile it before continuing." >&2
    exit 2
  fi

  rollback_head=$(git rev-parse HEAD)
  test "$rollback_head" = 1eaeba5657a96d8bdf9c225e8ab96ad9bac84d86

  git fetch origin main
  test "$(git rev-parse origin/main)" = "$(git rev-parse FETCH_HEAD)"
  git merge-base --is-ancestor "$rollback_head" origin/main

  git branch main "$rollback_head"
  git switch main
  git branch --set-upstream-to=origin/main main

  test "$(git branch --show-current)" = main
  test "$(git rev-parse --abbrev-ref --symbolic-full-name "@{u}")" = origin/main
  test "$(git rev-parse HEAD)" = "$rollback_head"
  test -z "$(git status --porcelain)"
'
```

This phase intentionally leaves production `main` behind `origin/main` at the
known healthy rollback commit. The canonical deployment script performs the
reviewed fast-forward and records that commit as `PREVIOUS_HEAD`; do not pull or
merge the candidate outside the script.

Then run the canonical preflight from a clean local `main`:

```bash
phase3/scripts/deploy-and-verify.sh --preflight-only
```

Do not run the deployment form until preflight passes and the operator explicitly requests a production deployment.
