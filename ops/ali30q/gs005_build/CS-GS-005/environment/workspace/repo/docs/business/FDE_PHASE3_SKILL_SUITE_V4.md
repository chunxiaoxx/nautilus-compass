# FDE Phase 3 Skill Suite v4

> Historical reference only. The current Phase 3 operating contract is
> `FDE_PHASE3_SKILL_SUITE_V4_1.md` together with
> `FDE_PHASE3_BITABLE_AUTHORITY.md`. Where this document differs, the newer
> documents control.
>
> `ecc-fde-external` is a Phase 2 legacy asset. Every reference to it below is
> retained only as historical evidence and is blocked from Phase 3 runtime,
> training, and external copy generation.

## Purpose

This is a historical snapshot of the former five-Skill contract. It
updates the current suite without discarding its useful task-design, QC, and
Evidence Pack material. It does not create a Bitable table, configure a Form,
or authorize an online write.

The authoritative state and review ledger is Bitable. The detailed state
machine and privacy boundary are defined in `FDE_PHASE3_BITABLE_AUTHORITY.md`.

## Common Contract

- Each task, interaction attempt, review, and export receipt is anchored to its
  related Bitable record identity. The actual record identity remains internal.
- P0, `feedback_class`, `verdict`, `revision_of`, and redaction status are
  written and read back through Bitable before downstream automation acts.
- A revision request creates `repair_required`. It becomes `Repair` only after
  a later, source-linked attempt is accepted.
- V5 derives an opaque `task_id` from the internal Bitable anchor and emits a
  schema-valid, redacted v3 event plus manifest. It does not export raw evidence
  or Bitable record identifiers.
- Compass independently validates the event and writes a controlled receipt
  back through the Bitable export record. It is not a task ledger or reviewer.
- `canonical_blocked` is a valid outcome. A missing field, P0 failure, invalid
  lineage, failed manifest, or failed read-back remains visible as blocked.

## Role Contract

| Skill | Phase 3 responsibility | Must not do |
| --- | --- | --- |
| `ecc-fde-external` | Phase 2 historical role only; blocked in Phase 3 | Must not be loaded by Phase 3 runtime, training, or external copy generation |
| `ecc-fde-vertcase` | Design a coherent work task that supports a real multi-turn trajectory and P0 review | Substitute generated turns for human interaction or mark a task accepted |
| `ecc-fde-internal` | Route Bitable state, P0/QC, buyer feedback classification, revision, and settlement eligibility | Keep a competing task ledger or export raw evidence |
| `ecc-shared` | Own Bitable schema checks, controlled writes, idempotency, desensitization, and read-back | Let another Skill write Bitable state directly or send raw data to Compass |
| `fde-task-pipeline` | Orchestrate valid transitions and report the explicit block reason | Treat a revision request as `Repair`, revive S3 delivery, or create a parallel workflow |

## External Experience

For the current Phase 3, experts use Doubao Office Task only. Other Agent
tools remain compatibility guidance for other approved projects, not a
substitute for the Phase 3 interaction requirement:

```text
receive task -> complete relevant multi-turn interaction -> submit Evidence Pack
             -> receive accepted, rejected, or repair-required guidance
```

External users do not install a local Skill, call V5, invoke Compass, see
checklist scores, or manage Bitable state. Their agent tool produces evidence;
it is not the system of record.

## Metadata and Legacy Boundary

Yao-era meta value is retained as `interface.yaml`: role routing, supported
adapter targets, trust boundary, required input/output, and a machine-readable
blocked reason. It is not a separate business workflow.

- `checklist-from-task` remains an internal QC rule source only.
- `fde-row-assembler` remains a compatibility utility only when the confirmed
  buyer schema still requires it.
- Legacy S3 is not a Phase 3 delivery, settlement, or V5/Compass export path.
- Historical XLSX columns and static scores cannot override the current Bitable
  record, buyer review, or controlled Phase 3 state.

## Activation Gate

This v4 contract can be installed and validated locally. Bitable field mapping,
Form permissions, attachments, online writes, official V5 export, and Compass
live import remain frozen until the user approves the form blueprint and a first
authorized task is available.

## Local Installation Receipt

Installed locally on 2026-07-22 as `v4.0.0-phase3` for both `.agents` and
`.claude` runtimes. All five interface YAML files parsed successfully and every
Skill/interface mirror pair had the same SHA-256 value.

| Skill | Skill SHA-256 | Interface SHA-256 |
| --- | --- | --- |
| `ecc-fde-external` | `77A31695BF259E0B451DC78B30E1F28A8D238DA745934DCB010EDB3FCD413857` | `5DFB8D62366A4B42A78E75F37EAD56ADFA16FBE1AD3148B90DDACFAF5D307FE9` |
| `ecc-fde-internal` | `9DE014C0BF09B144095B11C447721354B68D95E7BBDD1DFBC88F25580DE95008` | `D2193102C7D4A7A6DC9867000B4EEEC69CA627BED56FA5C6E88DEB390313FE67` |
| `ecc-fde-vertcase` | `ED7B89490BA18DC33B4DD77F111DBB69E9358A6DAF935F7467F30F163D98B7B3` | `6F4955CA7483CCC53D69BBCC4D35736DC4B46C0BD0C075E78D4F1515CC626DCF` |
| `ecc-shared` | `17DB0BA17208F968CC6A2DE1B18E18E8955734B70A6B5C295EA6332692BCAC78` | `2CC2185FBD4881466147D6B8E92F16E8427943D5AFA4F34128AACB679BA93094` |
| `fde-task-pipeline` | `DB339AE6991EB2EAE19244445EAAAC3B5184ABDD06B92D5E8729A6563AA56452` | `B3A4592D466B1FBB9481E61BE3BBF2E9CEF32AEAB176AB8D668D7DE7D45DA991` |

## Offline Lifecycle Audit

These synthetic cases contain only placeholder Bitable identities and hashes.
They validate the Skill contract; they are not online records or delivery proof.

| Case | Bitable result | V5 eligibility | Required outcome |
| --- | --- | --- | --- |
| First-pass acceptance | P0 pass, `feedback_class=none`, accepted, no parent attempt | eligible after redaction | `verdict=Gold`, then controlled Compass receipt |
| Revision request | P0 pass, buyer asks for change, no later accepted attempt | not eligible | `repair_required`; no `Repair`, no export |
| Accepted revision | P0 pass, a new attempt has complete `revision_of`, accepted | eligible after redaction | `verdict=Repair`, then controlled Compass receipt |

## Implementation Stop Line

This release did not create or modify an online Bitable table, Form, credential,
V5 official event, or Compass live import. Those remain blocked until the form
blueprint is approved and a first authorized task is available.
