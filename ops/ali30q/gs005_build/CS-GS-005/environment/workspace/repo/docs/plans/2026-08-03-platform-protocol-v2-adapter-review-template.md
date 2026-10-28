# Platform Protocol V2 Versioned Domain Adapter Review Template

## Current admission state

No owner-domain proposal has been submitted with this template. The admission
state is therefore `pending`, and no domain adapter, domain test, source read,
or source write is in scope.

No adapter is authorized without an approved owner-domain proposal.

## Proposal identity and ownership

- Owning domain repository and immutable revision:
- Domain owner accountable for source authority and source write-back:
- Proposal and adapter contract version:
- Review timestamp and reviewer:

## Required proposal content

### Source authority

Name the source system that remains authoritative for the domain decision. The
proposal must identify the owner-controlled read-back that proves that authority.
Platform protocol records are not a substitute for source authority.

### Eligible source event

Define the sole versioned event eligible for translation. State its admission
preconditions, expiry, and the fixed fields that may be projected into an
opaque Platform request.

### Opaque reference derivation

Specify a deterministic, one-way derivation for every reference sent to
Platform. The proposal must exclude raw source evidence, source text, paths,
credentials, personal data, and external account identifiers.

### Allowed Protocol operation kind

State the single registered operation kind, policy version, caller identity,
executor release, and verifier interpretation that the domain adapter requests.
Platform may enforce the generic contract but may not infer a domain decision.

### Receipt interpretation

Explain how the domain reads an independent Protocol receipt. A receipt proves
the bounded Protocol decision only; it neither creates nor replaces the domain
decision and cannot by itself authorize a source mutation.

### Write-back authority

Identify the domain-owned component and authorization that may perform a source
write-back. Platform must not decide a domain write-back or own the domain
mutation policy.

### Source read-back proof

Provide the required pre-mutation and post-mutation source read-back proof,
including the permitted de-identified evidence references and the condition for
declaring the domain operation incomplete.

### Retention policy

State which domain-side data remains with the owner, the retention period for
the opaque protocol projection, and the deletion or revocation procedure.

### Rollback path

Define how the domain owner revokes eligibility, stops further source writes,
and verifies the post-rollback source state. Platform audit and outbox records
remain protocol history and do not reconstruct domain state.

## Rejection conditions

Reject the proposal if it:

- includes raw source evidence or another non-opaque projection;
- treats Platform protocol state as a domain decision;
- omits source read-back proof before or after a source mutation;
- lets Platform decide a domain write-back;
- lacks an immutable owner-domain revision, retention policy, or rollback path.

## Admission decision record

- Decision: `pending`, `rejected`, or `approved`.
- Reason codes and contract version:
- Approved operation kind and opaque projection schema hash:
- Owner-domain evidence reference for read-back proof:
- Explicit authorization for adapter creation:

An `approved` decision authorizes only the named, versioned domain adapter. It
does not authorize a Platform schema change, a deployment, a push, a merge, or
any additional domain workflow.
