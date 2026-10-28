# Platform Protocol V2 vertical-slice evidence

## Scope

This is a deterministic, synthetic, non-business local verification of the
Protocol V2 chain. It does not deploy, send network traffic, call an external
business system, use Docker, or add a compatibility adapter.

## Baseline

- Baseline commit: `010da5185574fcfd9d32c8989c99b0c6f0f5b116`
- Migration head: `20260804_02_protocol_v2_task4`
- Canonical conformance-vector SHA-256:
  `d3aa6361ab3152ff3a14e1887a5ed3b8ceac532c2f1392eea1ca3312e9f6fe29`

## Verification commands

The test process receives a disposable local database URL through
`NAUTILUS_PLATFORM_DATABASE_URL`; the URL and any credentials are neither
recorded here nor committed.

```powershell
python -m pytest tests/platform_protocol/test_vertical_slice.py -q --confcutdir=tests/platform_protocol
python -m pytest tests/platform_protocol -q --confcutdir=tests/platform_protocol
```

## Observed local evidence

- Registered service identities: 4; registered public keys: 4.
- Protocol rows after the first chain: operations 1, attempts 1, manifests 1,
  receipts 1, audit events 4, outbox events 2.
- Canonical Ed25519 verification passes for the caller credential, platform
  envelope, and independent receipt.
- A complete duplicate replay creates no rows and emits no additional audit or
  outbox events.
- Exactly one planned outbox event is acknowledged: delivered 1 and pending 1;
  repeating that acknowledgement is harmless.
- The vertical-slice command passed twice consecutively (one test on each run),
  followed by a full Platform suite result of 48 passing tests.
- Migration upgrade, downgrade, and repeat upgrade passed in the full suite.
- The disposable database is dropped after verification and a read-back confirms
  zero databases with its exact name.

## Persistence and review boundaries

The vertical slice asserts that the database contains only protocol metadata,
approved hashes, and the approved public verification material. The protected
storage reference participates in the canonical manifest, while persistence
keeps the manifest hash and binding rather than the reference itself. The
approved schema persists the Platform-envelope signature and independent
verifier-receipt signature. For the caller credential it persists only the
credential version, key identifier, and credential hash; it does not persist
the original caller-credential signature or any private key. Raw evidence,
dialogue, and external account data are not persisted. The focused test, full
Platform suite, static checks, and migration round trip passed. Independent
review concluded High=0, Medium=0, Low=0 before the standalone commit.
