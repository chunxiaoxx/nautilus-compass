# Phase 3 Native Form Publication Design

## Trigger

The expert-information Form has valid Bitable/Form metadata but an external
user receives "temporarily unsupported for entry." The API-provided share URL
matches the reported URL and redirects an anonymous HTTP client to the Feishu
account service. It is therefore not evidence that an external expert can
fill the Form.

## Decision

Feishu's native Form sharing UI is the sole authority for public Form
publication. The existing Phase 3 CLI may validate schema, Form metadata, and
the resulting public URL behavior, but it must not treat an undocumented Form
metadata patch as proof of external fillability.

## Options Considered

1. Continue using the current Form metadata endpoint as a publisher. Rejected:
   its success response did not produce an anonymously fillable Form.
2. Use the authenticated Base owner's native "Share Form" UI, then use CLI and
   an anonymous browser acceptance check. Selected: it matches the documented
   Feishu product flow and retains the current Bitable ledger.
3. Build an owned external intake site. Deferred: it duplicates a native
   workflow, adds identity and attachment handling, and is unnecessary while
   the Form view can satisfy the requirement.

## Publication Contract

There are exactly two external surfaces:

| Form | Source table | Purpose |
| --- | --- | --- |
| `第三期专家信息采集（正式）` | `第三期专家` | expert application and Doubao enablement information |
| `第三期任务与交互提交（正式）` | `第三期任务与交互提交` | one complete task plus its Office Task interaction trajectory |

Each Form must be published through its own Form-view share dialog with the
scope equivalent to "internet users with the link can fill." It must not grant
Base or view access. The task Form remains blocked until its seven approved
additive fields have been created and the Form contract has been read back.

## Acceptance Sequence

1. In the authenticated owner session, open the expert Form view and use the
   native share dialog to disable/re-enable sharing with the external fill
   scope. Copy the resulting Form share link only into controlled operator
   configuration; do not commit it.
2. Validate in a clean anonymous browser session that the link renders fields
   and a submit action rather than a login redirect or unsupported page. Do not
   submit a row in this step.
3. Use the Phase 3 CLI to re-read only Form metadata and question counts. Its
   result supports, but never replaces, the anonymous browser acceptance check.
4. Only after the expert Form is accepted, run the separately approved task
   maintenance window: pause the task Form, add the seven fields, read back
   schema/Form state, and publish the unified task Form through the native UI.
5. Only after both Forms are accepted may an explicitly authorized synthetic
   submission test create a record. That later test validates the actual
   Bitable trigger, Nautilus P0 write-back, Mentor projection, and failure
   handling. It is not authorized by this publication action.

## Automation Boundary

The four-table state machine and P0 rules are code and schema contracts today,
not a running production funnel. Native Form submission creates the initial
Bitable record. Zhiyong Nautilus must subsequently be deployed and verified as
the sole post-form writer. Zhiyong Mentor receives only an expert-scoped,
redacted projection. Buyer sync, V5 export, Compass import, settlement, and
training remain disabled.

## Failure Handling

If native sharing remains unavailable, leave the Form unpublished and capture
the Feishu UI error category plus the developer-console operation log. Do not
retry metadata patches, expose the Base, or create an alternate external form
without a new approved design.
