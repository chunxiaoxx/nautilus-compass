# A2A Settlement Integrity Pilot (Draft)

Status: local review draft only. No external publication, payment, signing, or production integration.

## Scope

Compare Nautilus's proof/credit path and bounty settlement path with the partner's JiZhiMCP settlement surface using only the public gateway and the zero-balance fixture `agent-demo-verify`.

Allowed first-stage calls:

- `settlement.account` with `mode=balance`
- `settlement.ledger`

Disallowed in this stage:

- `settlement.transfer`
- `settlement.credit`
- any payment, signing, account mutation, or production endpoint

Gateway supplied by partner: `https://mcp.xn--5kvtwv52d.com/mcp/gateway`

## Design split

### 1. Compass proof/credit layer

- `proof/poi_reconciler.py`: joins recalled-memory candidates to trusted agent outcomes; stable candidate idempotency key prevents repeated settlement.
- `proof/poi_credit_store.py` and `sql/004_poi_credit.sql`: central `poi_credit` table accumulates impact by `memory_key` with UPSERT; snapshot export is atomic.
- `proof/fde_rsi_delta_consumer.py`: rejects non-escaping/non-positive rows and deduplicates by `delta_id` before crediting a producer/policy bucket.

This is an impact/credit evidence layer, not a funds-transfer ledger.

### 2. Core bounty settlement layer

`nautilus-core/bounty_lifecycle.py` routes deterministic, LLM-audited, or peer-reviewed outcomes to `_settle_bounty`. The caller commits the SQLAlchemy transaction after settlement. The current path primarily increments worker/poster `total_earnings` and related counters.

Current evidence gap: no verified transfer ID, hash-chained transfer ledger, or unified cross-endpoint settlement idempotency key was found in this path. Therefore the accurate claim is “transaction-bounded balance-field update,” not “tamper-evident funds ledger.”

## Reproducible trace plan

For the partner fixture, capture:

1. exact request method/body and UTC timestamp;
2. response status and canonical JSON digest;
3. account balance response;
4. ledger response, entry order, previous-hash linkage, and pagination/replay behavior;
5. repeated identical reads and whether response digests remain stable;
6. SHA-256 digests of the redacted request/response bundle.

No secret or account-changing payload is included in the evidence bundle.

## Acceptance criteria

- Both read-only calls succeed without a write capability.
- Zero-balance account remains unchanged.
- Ledger entries, if present, expose a verifiable previous-hash chain.
- Repeated reads do not create new entries or alter balance.
- Any mismatch is reported as an observation with a reproducible request/response digest, not as a production vulnerability claim.

## Next actions

1. Validate the gateway schema and response format from the partner.
2. Run the two read-only calls from an approved network environment.
3. Produce a redacted trace and compare it with the two Nautilus paths above.
4. Ask the partner to review the split before proposing any sandbox changes.

## Additional Core risk to validate

The current bounty endpoints check status before claim/submit/review, but the inspected lifecycle path does not use an explicit row lock or transfer idempotency key. Under concurrent duplicate submissions, status-check-then-settle may need a race test; a database transaction commit alone does not prove that two concurrent requests cannot both settle. This remains a code-level hypothesis until reproduced in an isolated test and must not be reported as a production incident without evidence.

## Partner contract readback

The partner README describes a Bearer-key gateway; `settlement.account` for balances; `settlement.transfer` as atomic and idempotent via `idempotency_key`; `settlement.ledger` for balances and transaction history; predecessor-linked SHA-256 ledger entries; and `audit.record`/`metering.record` for immutable evidence and usage aggregation. This is a contract-level claim to verify against the zero-credit fixture, not yet an independent runtime result.

## Compatibility comparison (pre-runtime)

| Capability | JiZhiMCP contract claim | Nautilus evidence found | Status before runtime trace |
|---|---|---|---|
| Balance read | `settlement.account(mode=balance)` | Core exposes agent/bounty state, but no verified equivalent settlement.account response | Not comparable yet |
| Atomic transfer | `settlement.transfer` atomic debit+credit | `_settle_bounty` updates balance fields inside a DB transaction; no verified transfer object | Partial / different abstraction |
| Transfer idempotency | `idempotency_key` | No verified transfer idempotency key in `bounty_lifecycle.py` | Gap to validate |
| Ledger history | `settlement.ledger` | Compass `poi_credit` is impact credit, not funds history; Core path has no verified hash-chain transfer ledger | Missing equivalent |
| Tamper evidence | SHA-256 predecessor chaining | PoI snapshots are atomic, but not a chained funds ledger | Different property |
| Audit/metering | `audit.record` / `metering.record` | Compass has PoI evidence and RSI delta attribution; Core emits task events, not a verified unified settlement evidence record | Partial / split |
| Double-spend guard | Partner claims guard on transfer | No verified equivalent in current Core bounty path; concurrency race remains a hypothesis | Unverified risk |

This table separates contract claims, code evidence, and runtime verification. It is not a production equivalence claim.

## Runtime trace 2026-11-22 (Mac mini)

The corrected read-only probe ran successfully from `chunxiao-430.local` against the partner gateway. Both calls returned HTTP 200 and JSON-RPC success:

- `settlement.account(account_id=agent-demo-verify, mode=balance)`: account exists, balance `0 credits`, no mutation.
- `settlement.ledger(account_id=agent-demo-verify)`: balance `0 credits`, `tx_count=0`, empty entries.

The evidence bundle records request/response SHA-256 digests and latency; no write call was made. Full redacted bundle: `docs/evidence/a2a_readonly_trace_20261122.json`.

This verifies the zero-balance fixture and read-only contract surface, but does not independently test transfer atomicity, idempotency, or double-spend prevention.
