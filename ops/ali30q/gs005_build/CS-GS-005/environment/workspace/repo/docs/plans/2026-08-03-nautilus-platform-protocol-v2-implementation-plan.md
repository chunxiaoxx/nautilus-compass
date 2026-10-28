# Nautilus Platform Protocol V2 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an isolated, domain-neutral protocol service that can prove a
bounded operation was authenticated, deduplicated, independently attested, and
durably delivered without becoming a business ledger.

**Architecture:** Create a new nautilus_platform PostgreSQL database with an
independent forward-only migration root. Keep pure protocol rules separate from
persistence and the legacy Core ORM. Domain systems, including FDE, enter only
through versioned adapters that exchange opaque source references and signed
receipts.

**Tech Stack:** Python 3, SQLAlchemy 2, Alembic, PostgreSQL, Pytest, Pydantic,
and Python cryptography.

---

## Preconditions

- ADR docs/plans/2026-08-03-nautilus-platform-protocol-v2-adr.md is accepted.
- Work occurs in a clean, non-FDE worktree based on an explicit commit.
- A disposable PostgreSQL database is available for tests. No legacy Core
  database, Bitable, Feishu, V5, Compass, or production credential is used.
- The implementation introduces no FDE rule, field, state, person, or source
  record handling.

### Task 1: Create the Side-Effect-Free Protocol Contract

**Files:**
- Create: phase3/backend/platform_protocol/__init__.py
- Create: phase3/backend/platform_protocol/contracts.py
- Create: phase3/backend/tests/platform_protocol/test_contracts.py

**Step 1: Write failing contract tests**

Cover a valid OperationEnvelopeV2, canonical manifest hashing, changed-body
idempotency conflict, expired operation rejection, executor-verifier conflict,
and receipt-binding mismatch.

    def test_changed_payload_reusing_idempotency_key_is_rejected():
        first = accept_operation(caller=caller, envelope=envelope("key-1"))
        with pytest.raises(ProtocolViolation, match="idempotency_payload_conflict"):
            accept_operation(caller=caller, envelope=envelope("key-1", policy="v2"))

**Step 2: Run the focused tests**

Run: python -m pytest phase3/backend/tests/platform_protocol/test_contracts.py -q

Expected: failure because the contract module does not exist.

**Step 3: Write minimal implementation**

Use frozen dataclasses or immutable Pydantic models. Accept only explicit UTC
timestamps and canonical JSON. Do not import legacy ORM models, load dotenv,
open a database connection, or call a network API.

**Step 4: Re-run focused tests**

Run: python -m pytest phase3/backend/tests/platform_protocol/test_contracts.py -q

Expected: PASS.

**Step 5: Commit**

    git add phase3/backend/platform_protocol phase3/backend/tests/platform_protocol/test_contracts.py
    git commit -m "feat(platform): add protocol v2 contract rules"

### Task 2: Add a Separate Platform Database and Migration Root

**Files:**
- Create: phase3/backend/platform_protocol/database.py
- Create: phase3/backend/platform_protocol/models.py
- Create: phase3/backend/platform_migrations.ini
- Create: phase3/backend/platform_migrations/env.py
- Create: phase3/backend/platform_migrations/script.py.mako
- Create: phase3/backend/platform_migrations/versions/20260803_01_protocol_v2.py
- Create: phase3/backend/tests/platform_protocol/test_migrations.py

**Step 1: Write failing migration tests**

Use an explicitly supplied NAUTILUS_PLATFORM_DATABASE_URL pointing at a
disposable database. Assert that upgrade creates only protocol tables and one
dedicated version table. Assert that a missing URL fails before any connection
attempt.

    def test_platform_upgrade_creates_no_legacy_or_domain_tables(tmp_postgres_url):
        upgrade_platform_database(tmp_postgres_url)
        assert table_names(tmp_postgres_url) == {
            "platform_schema_version",
            "protocol_operations",
            "protocol_manifests",
            "protocol_receipts",
            "protocol_outbox",
            "protocol_audit_events",
        }

**Step 2: Run the migration test**

Run: NAUTILUS_PLATFORM_DATABASE_URL=<disposable-url> python -m pytest
phase3/backend/tests/platform_protocol/test_migrations.py -q

Expected: failure before migration code exists.

**Step 3: Write minimal implementation**

Create a new declarative metadata base, engine factory, and Alembic root. The
engine factory accepts only the named environment variable passed by the
process; it must not import utils.database, use Base.metadata, load dotenv, or
share the legacy alembic_version table. Persist only the records approved by
the ADR.

**Step 4: Prove forward-only migration behavior**

Run upgrade, downgrade, and repeat upgrade against the same disposable
database. Inspect table names and version values after each action.

Expected: one migration head, no legacy table creation, and deterministic
repeat upgrade.

**Step 5: Commit**

    git add phase3/backend/platform_protocol phase3/backend/platform_migrations.ini phase3/backend/platform_migrations phase3/backend/tests/platform_protocol/test_migrations.py
    git commit -m "feat(platform): add isolated protocol persistence"

### Task 3: Implement Atomic Command Handling and an Outbox

**Files:**
- Create: phase3/backend/platform_protocol/repository.py
- Create: phase3/backend/platform_protocol/service.py
- Create: phase3/backend/tests/platform_protocol/test_service.py

**Step 1: Write failing transactional tests**

Test that duplicate command bodies return the original result, changed bodies
with the same key fail, a valid signed receipt creates one audit event and one
outbox row, and replaying the receipt does not create additional rows.

    def test_receipt_replay_is_idempotent(session, signed_receipt):
        first = service.record_receipt(session, signed_receipt)
        second = service.record_receipt(session, signed_receipt)
        assert second.receipt_id == first.receipt_id
        assert count_rows(session, "protocol_outbox") == 1

**Step 2: Run the focused test**

Run: NAUTILUS_PLATFORM_DATABASE_URL=<disposable-url> python -m pytest
phase3/backend/tests/platform_protocol/test_service.py -q

Expected: failure because the repository and service do not exist.

**Step 3: Write minimal implementation**

The operation transition, immutable manifest or receipt, audit event, and
outbox enqueue happen in one database transaction. Use unique constraints for
idempotency and external receipt identity. Do not update a legacy task,
capability, reward, reputation, survival row, or domain source.

**Step 4: Re-run focused tests**

Run: NAUTILUS_PLATFORM_DATABASE_URL=<disposable-url> python -m pytest
phase3/backend/tests/platform_protocol/test_service.py -q

Expected: PASS.

**Step 5: Commit**

    git add phase3/backend/platform_protocol/repository.py phase3/backend/platform_protocol/service.py phase3/backend/tests/platform_protocol/test_service.py
    git commit -m "feat(platform): persist protocol commands atomically"

### Task 4: Add Registered Caller and Verifier Signature Checks

**Files:**
- Create: phase3/backend/platform_protocol/keys.py
- Create: phase3/backend/platform_protocol/registry.py
- Create: phase3/backend/tests/platform_protocol/test_receipt_signatures.py

**Step 1: Write failing signature tests**

Use generated test keys. Cover unknown key id, invalid signature, changed
receipt payload after signing, expired caller credential, and an executor that
also acts as verifier.

**Step 2: Run the signature tests**

Run: python -m pytest
phase3/backend/tests/platform_protocol/test_receipt_signatures.py -q

Expected: failure because no key registry exists.

**Step 3: Write minimal implementation**

Use public-key verification and explicit status/version checks. Store only
registered service and verifier identities. Do not store human identities,
third-party account IDs, or raw token values.

**Step 4: Re-run focused tests**

Run: python -m pytest
phase3/backend/tests/platform_protocol/test_receipt_signatures.py -q

Expected: PASS.

**Step 5: Commit**

    git add phase3/backend/platform_protocol/keys.py phase3/backend/platform_protocol/registry.py phase3/backend/tests/platform_protocol/test_receipt_signatures.py
    git commit -m "feat(platform): verify registered protocol receipts"

### Task 5: Prove a Deterministic Non-Business Vertical Slice

**Files:**
- Create: phase3/backend/tests/platform_protocol/test_vertical_slice.py
- Create: docs/plans/2026-08-03-platform-protocol-v2-vertical-slice-evidence.md

**Step 1: Write the end-to-end test**

Use one generated caller, one executor, a different verifier, an in-memory
artifact reference, and an intentionally simple verifier predicate. The test
must submit an operation, manifest, signed receipt, and one outbox delivery
acknowledgement.

**Step 2: Run it twice**

Run: NAUTILUS_PLATFORM_DATABASE_URL=<disposable-url> python -m pytest
phase3/backend/tests/platform_protocol/test_vertical_slice.py -q

Expected: one set of protocol rows after each replay, no duplicate receipt or
outbox delivery, and no access to external systems.

**Step 3: Record evidence without protected content**

Document commands, migration head, row counts by protocol table, signature
verification result, and duplicate-replay result. Do not include source
content, credentials, personally identifying information, or opaque record
identifiers.

**Step 4: Commit**

    git add phase3/backend/tests/platform_protocol/test_vertical_slice.py docs/plans/2026-08-03-platform-protocol-v2-vertical-slice-evidence.md
    git commit -m "test(platform): prove protocol v2 vertical slice"

### Task 6: Review a Versioned Domain Adapter Request

**Files:**
- Create: docs/plans/2026-08-03-platform-protocol-v2-adapter-review-template.md
- Create only after approval: <domain-repository>/adapters/platform_protocol_v2.py
- Test only after approval: <domain-repository>/tests/test_platform_protocol_v2_adapter.py

**Step 1: Require an adapter proposal from the owning domain repository**

The proposal must state source authority, eligible source event, opaque
reference derivation, allowed protocol operation kind, receipt interpretation,
write-back authority, read-back proof, retention policy, and rollback path.

**Step 2: Reject incomplete proposals**

Reject any proposal that sends raw source evidence, uses Platform protocol
state as a domain decision, omits source read-back, or lets Platform decide a
domain write-back.

**Step 3: Implement only the approved adapter**

The adapter owns source translation and any source write-back. Platform remains
unchanged except for a versioned, generic request interface.

**Step 4: Run joint contract tests in both repositories**

Expected: Platform accepts only opaque, versioned requests; the domain system
proves its own read-back before and after any source mutation.

**Step 5: Commit separately in each repository**

Do not combine a Platform commit with a domain workflow commit.

## Global Verification Before Any Deployment

Run all focused Platform tests, then inspect the disposable database and logs.
The release review must demonstrate absence of protected source content,
separate database credentials, one migration head, signature enforcement,
idempotency, and outbox retry behavior. A passing test suite alone is not
deployment approval.
