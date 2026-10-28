# Phase 3 Expert Form CLI Recovery Design

## Context

The official expert-information Form is configured as public in a metadata
read-back, but an external user reported that the Feishu UI says the Form is
temporarily unavailable. The generic Phase 3 Form publisher cannot safely
refresh that Form alone: it resolves both public Forms and stops when the
unrelated task table is missing its approved maintenance fields.

This recovery must not read Bitable business records, inspect raw buyer
materials, change the task Form, or create a parallel workflow ledger.

## Options Considered

1. Use the generic publisher for both Forms. This is rejected because task
   schema drift prevents a narrow expert-Form recovery and makes the change
   surface larger than the incident.
2. Add a target selector to the generic publisher. This is workable, but a
   command that can select the task Form later has a larger accidental-mutation
   surface.
3. Add a dedicated expert-Form recovery CLI. This is selected. Its code has no
   task-Form selection path, so it can inspect and refresh only the official
   expert Form while the task maintenance window remains separate.

## Selected Design

Add `scripts/refresh_phase3_expert_form.py`, backed by narrowly scoped methods
on the existing `FormPublisher`. The command has two safe modes:

- `--probe` (the default): reads expert table, Form metadata, and Form question
  metadata only. It prints a sanitized status summary without record data,
  share URLs, identifiers, or credentials.
- `--apply --confirm FDE_PHASE3_EXPERT_FORM_REFRESH`: pauses only the expert
  Form, re-applies its approved question configuration, validates the expert
  Form's field contract, republishes it to anyone with the link, and performs
  metadata read-back.

The refresh sequence is fail-closed:

```text
read expert-only metadata
-> make expert Form private
-> read back private state
-> patch expert questions
-> validate expert fields
-> publish expert Form with approved public settings
-> read back public state
```

If a step after the pause fails, the expert Form remains private. The CLI does
not attempt a blind rollback because re-opening an unverified public Form would
weaken the incident boundary. The operator then receives a sanitized failure
message and investigates through the Feishu app console.

## Boundaries

- The dedicated command never enumerates, reads, writes, or matches Bitable
  records.
- It never resolves or changes `第三期任务与交互提交`, its Form, review table,
  export table, or legacy Forms.
- It reuses the current protected Feishu application credentials and existing
  Form API adapter. No credential values are added to code, documentation, or
  CLI output.
- A successful API read-back proves Form metadata and question configuration,
  not that every browser client has rendered the Feishu SPA correctly. A clean
  external open is still the user-facing acceptance check.

## Acceptance Criteria

1. Unit tests prove the command cannot select or call task Form endpoints.
2. Unit tests prove it requires the exact confirmation string before a PATCH.
3. Unit tests prove probes use only table, field, view, Form metadata, and Form
   question endpoints, never record endpoints.
4. A live `--probe` produces an expert-only sanitized status result.
5. An explicitly authorized live refresh produces expert-only private and
   public read-backs. The broader seven-field task maintenance remains pending
   and separately authorized.
