# FDE Phase 3 Single-Submission Flywheel Design

## Decision

Phase 3 uses one Feishu-native submission journey for each expert task:

```text
expert profile -> full task and interaction submission -> automatic QC
               -> buyer-ready | repair_required | blocked
               -> buyer feedback -> revision_of lineage -> eligible export
```

The previous split between a prescreen table and an interaction-result table
is retired. It required people to match records manually and added a wait
state before experts could complete a trajectory. It is unsuitable for the
required high-volume loop.

## Canonical Bitable Model

The current Base is empty of business records. New canonical tables are
created before any old table is archived:

| Table | Purpose | External surface |
| --- | --- | --- |
| `第三期专家` | Expert profile and enablement state | Expert profile Form |
| `第三期任务与交互提交` | One complete task trajectory or one revision | Single task Form |
| `第三期审核与反馈` | Deterministic P0, model QC, buyer feedback, verdict history | Internal only |
| `第三期导出与回执` | Redacted V5 export eligibility and Compass receipt | Internal only |

`第三期任务与交互提交` owns the task contract, attachment references,
Doubao interaction evidence, log ID, and a self-link `revision_of`. A revision
is a new record whose direct predecessor is read back from Bitable. A row is
never matched manually by name, UID, or timestamp.

Existing tables and Forms are renamed with an archive prefix and all old public
Forms are unshared only after the two new Forms are published and read back.
They are retained until the synthetic acceptance run succeeds. The default
Feishu `数据表` remains outside the business workflow.

## Automatic QC Funnel

P0 is automatic rather than a human admission queue. Each review stores the
rule and model versions, confidence, reason codes, and a feedback summary.

- `buyer_ready`: mandatory metadata and evidence gates pass, and the model QC
  confidence meets the configured threshold.
- `repair_required`: a recoverable field, evidence, coherence, or quality
  issue is returned to the expert through 智涌导师.
- `blocked`: safety, privacy, or integrity violation blocks downstream sync.

Human work is limited to drift sampling, dispute handling, and policy changes.
The buyer remains the commercial authority; an automatic pass only controls
routing, never fabricates a buyer verdict.

## Application Responsibilities

`智涌Nautilus` is the only app with direct canonical-Base access. It receives
the Base automation callback, reads the selected record, runs QC, writes a
linked review record, updates allowed lifecycle fields, and emits a redacted
projection.

`智涌导师` is the expert-facing agent. It receives versioned Phase 3 knowledge:
the interaction guide, quality rules, category taxonomy, approved examples,
and redacted structured lessons from buyer feedback and internal QC. For an
expert's own task it can show the authorized feedback summary and next action.
It does not enumerate unrelated experts, unrestricted Base rows, unredacted
attachments, or raw cross-expert buyer material.

The Mentor projection is a service contract, not a parallel business ledger.
It contains only the expert identity binding, the task record reference,
current Bitable state, next action, approved feedback summary, and knowledge
pack version.

## Feishu-Native Surfaces

There is no external web portal. Experts use two public Feishu Forms and
智涌导师 messages/cards. Internal operators use Bitable views. The backend is
only a signed Feishu callback and Bitable adapter.

## Safety and Evidence Boundaries

All business state, review history, and revision lineage are authoritative only
after Bitable read-back. The V5 and Compass path receives a redacted envelope
only after eligibility. Raw chats, attachments, account identifiers, share
URLs, passwords, and buyer identity are not exported in the envelope.
