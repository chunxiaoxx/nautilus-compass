# Assay Protocol v0 · An Open Verification Protocol for Agent Claims

> One page. Anyone may implement it. Nautilus Assay is the reference implementation,
> not the owner. Status: v0 (2026-09-19). License: text CC-BY; reference code
> follows the repo's Modified MIT.
> Rationale & theory: docs/theory/a2a_trust_foundations_20260918.md (L3/L4 of the
> Agent Trust Stack). Motto: **"Don't trust claims. Recompute them."**

## 0 · Terms

- **Subject** — an agent (or org of agents) making claims. Identified by
  `(public_key, code_hash, config_hash)` — the identity triple. Change the brain,
  get a new identity (T8).
- **Verifier** — a party that recomputes claims per registered criteria.
- **Claim** — a statement whose truth is checkable from bytes.
- **Criteria** — the measurement rule, preregistered before results (see §1).
- **Receipt** — the verifier's signed verdict artifact (see §3).
- **Wall** — the public ledger of runs, verified and unverified alike.

## 1 · Criteria Registration

Format: `criteria:<id>@<catalog-version>` with definition, measurement method,
source case, and a triple j = (m, τ, D):

- m — measurement mapping (what is computed, from what inputs)
- τ — threshold(s)
- D — disclosure set (what must be published)

**Ratchet rule**: a revision is legal ⇔ ρ(m′) ≥ ρ(m) (recomputability does not
decrease) ∧ Δτ carries an evidence chain ∧ D′ ⊇ D. The ratchet locks the
honesty of measurement, not the tightness of thresholds.

## 2 · Verification Pack (claim wire format)

A directory with `pack.json` (claims + declared checks + inputs), a
`manifest.json` sealing every file's hash, and the input files. Checks are
scripted (deterministic; no LLM discretion). Every claim must be recomputable
by a third party **from the pack alone**. Reference implementation: VerifyPack
v0.2 (`tools/verifypack/`, stdlib-only).

## 3 · Receipt & Verification

A receipt states: pack id + manifest hash, per-claim verdicts
(**agree / disagree / not_computable** — three states, where "cannot compute"
is an honest answer), environment, timestamp, verifier identity, boundary
clause. The verifier signs it (Ed25519). **Verification of a receipt must not
require trusting the verifier**: anyone with the public key and the pack
re-runs the checks (one command; see `scripts/verify_receipt.py`). A receipt
that cannot be re-verified is UNVERIFIABLE by definition.

## 4 · The Wall (public ledger discipline)

All runs are listed — agree, disagree, and UNVERIFIABLE alike; failures are
never deleted; subjects' own numbers appear with the same prominence as third
parties'. Wall permanence is the Sybil cost: history cannot be migrated away.

## 5 · Verifier Discipline

(a) Verifier ≠ implementer for any run they sign (separation).
(b) Self-verification is structurally invalid (a verifier judging its own
output is a degenerate fixpoint — I3); self-runs must be marked
`internal-audited` and never mixed into certified rankings.
(c) Blind protocols where the judge must not know subject identity
(mapping held by a third party).
(d) Rulings and criteria changes escalate to a human court of last resort.

## 5b · Verifier Liability & Challenge (the teeth)

A signature that binds the verifier to nothing is worth nothing. Every
verifier operating under this protocol MUST publish, before issuing receipts:

1. **Liability clause** — if a signed verdict is overturned by independent
   recompute: the verdict is marked OVERTURNED on the wall with the same
   prominence as any subject's failure; fees are refunded; the challenger's
   recompute costs are covered; the verifier's track record resets to zero.
2. **Open challenge right** — ANY party may challenge any receipt within the
   challenge window (default 90 days) by posting a recompute under §1-§3
   rules; the wall MUST record the challenge and its outcome regardless of
   who is embarrassed. The challenge right belongs to the world, not to the
   verifier's discretion.
3. **Standing** — the verifier identifies a liable principal (individual or
   entity). Anonymous verification is UNVERIFIABLE-by-definition at the
   trust layer regardless of cryptographic validity.

Reference operator's standing (Nautilus Assay): **personal unlimited
liability** of the principal (user decision pending formal registration);
track record starts at zero and is forfeit on a sustained overturn.

## 6 · Conformance levels

- **L-1 Subject**: can emit verification packs.
- **L-0 Verifier**: runs packs per §1–§3 and issues receipts.
- **L-1 Wall**: publishes per §4.
- **L-2 Network**: multiple independent verifiers, cross-checking, bonded
  (future; see foundations §6).

Implementers MAY fork all of it. Interop happens at the artifact level
(packs + receipts), not at the org level.
