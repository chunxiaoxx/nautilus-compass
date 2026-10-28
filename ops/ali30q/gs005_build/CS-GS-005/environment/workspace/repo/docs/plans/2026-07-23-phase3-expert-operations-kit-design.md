# Phase 3 Expert Operations Kit Design

## Goal

Create one source-aligned, offline operations kit that lets the recruiting team
recruit and train experts for the Phase 3 online interactive-trajectory program
without exposing internal Bitable fields, P0 implementation, buyer identity,
raw feedback, or private evidence.

## Source Boundaries

The kit derives its public requirements from:

- `docs/business/FDE_PHASE3_INTERACTIVE_PROTOCOL_20260722.md`;
- the approved `ecc-fde-external`, `ecc-fde-internal`, and
  `ecc-fde-vertcase` role boundaries; and
- the Phase 3 form blueprint.

It does not reproduce buyer documents, passwords, account identifiers, raw
conversations, source attachments, Bitable record IDs, or private feedback.

## Chosen Structure

Four Markdown documents live in `docs/business/phase3_expert_operations/`:

1. `README.md` is the single entry point and source map.
2. `01_RECRUITING_KIT.md` contains the expert profile, JD, public recruiting
   copy, private invitation copy, group-announcement copy, and the approved
   compensation wording.
3. `02_EXPERT_ONBOARDING.md` contains the welcome message, red lines,
   15-minute lesson, Office Task multi-turn SOP, a clearly fictional evidence
   package template, FAQ, daily reminders, and repair notices.
4. `03_OPERATOR_SOP.md` contains the internal recruiting, screening,
   group-building, training, assignment, status-check, and settlement-confirm
   process.

Splitting by audience prevents the expert-facing material from accidentally
leaking internal workflow details, while keeping the recruiting team from
having to assemble instructions from multiple technical contracts.

## Non-goals

This delivery does not create, change, or publish a Feishu Form/Bitable record;
does not route a submission; does not promise buyer acceptance; and does not
start V5, Compass, settlement, or training automation.

## Acceptance Criteria

- The kit covers all seven requested operational categories: persona/JD,
  recruiting copy, group welcome and terms, 15-minute training, interaction
  and evidence guidance, daily/FAQ/repair copy, and internal SOP.
- It states the approved rule that each buyer-accepted question is 200 RMB and
  settles within three business days after acceptance; it never treats P0 or
  `buyer_ready` as acceptance.
- It requires the approved Doubao Office Task mode, a new conversation per
  complete task, at least six relevant turns, per-turn human reasons, a
  24-hour completion/submission window, and formal-form submission.
- It explains that task/trajectory submission and expert registration use
  separate native Forms, but does not hard-code a form URL or identifier.
- It gives safe templates and examples, not fabricated business evidence.
- It gives internal staff a deterministic checklist and explicitly reserves
  business-state writes, buyer verdicts, repair lineage, settlement, V5, and
  Compass for their controlled workflows.

## Verification

A deterministic content audit will assert that every document exists, all
required sections are present, and prohibited internal terms are absent from
expert-facing materials. A human review checks wording against the current
buyer guide before any public posting.
