# FDE Phase 3 Skill Suite v4 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Upgrade the local FDE skill suite so all Phase 3 work uses Bitable as
the single authority while giving external experts a simple tool-neutral
submission path and giving internal agents a controlled automation loop.

**Architecture:** Keep five role-based Skills and one shared Bitable contract.
External users receive an Evidence Pack workflow only; internal automation reads
and writes controlled Bitable state. V5 and Compass consume redacted, eligible
records and return receipts without becoming a second task ledger.

**Tech Stack:** Markdown Skills, YAML interface metadata, PowerShell/Python
syntax validation, SHA-256 mirror comparison.

---

### Task 1: Publish the v4 shared contract and migration boundary

**Files:**
- Create: `docs/business/FDE_PHASE3_SKILL_SUITE_V4.md`
- Modify: `docs/business/FDE_PHASE3_INTERACTIVE_PROTOCOL_20260722.md`
- Modify: `docs/business/FDE_PHASE3_BITABLE_AUTHORITY.md`

**Step 1: Write the contract acceptance checklist**

Require the contract to define Bitable authority, `P0`, `feedback_class`,
`verdict`, `revision_of`, controlled V5 v3 export, Compass receipt, and the
rule that external users never need to run a local Skill.

**Step 2: Verify the current inconsistency**

Run a targeted search that confirms the legacy Phase 3 protocol still lists
`revision_of` as a Compass-facing field and the pipeline still treats a revision
request as `Repair`.

**Step 3: Write the minimal contract and correct the protocol boundary**

Make the contract point to `FDE_PHASE3_BITABLE_AUTHORITY.md`. Keep actual
Bitable field names and all online configuration out of this change.

**Step 4: Verify the contract**

Run Markdown content checks for all required gates and verify no link, credential,
actual record identifier, raw evidence, or buyer material was added.

**Step 5: Commit**

```powershell
git add -- docs/business/FDE_PHASE3_SKILL_SUITE_V4.md docs/business/FDE_PHASE3_INTERACTIVE_PROTOCOL_20260722.md docs/business/FDE_PHASE3_BITABLE_AUTHORITY.md
git commit -m "docs(fde): define phase 3 skill suite v4"
```

### Task 2: Upgrade the five role-based Skills and metadata

**Files:**
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-external\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-external\agents\interface.yaml`
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-internal\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-internal\agents\interface.yaml`
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-vertcase\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\ecc-fde-vertcase\agents\interface.yaml`
- Modify: `C:\Users\chunx\.agents\skills\ecc-shared\SKILL.md`
- Create: `C:\Users\chunx\.agents\skills\ecc-shared\agents\interface.yaml`
- Modify: `C:\Users\chunx\.agents\skills\fde-task-pipeline\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\fde-task-pipeline\agents\interface.yaml`
- Mirror each changed file under `C:\Users\chunx\.claude\skills\...`

**Step 1: Establish the expected v4 behavior in checks**

Define validation expectations: every role names the Bitable authority boundary;
only `ecc-shared` owns Bitable writes/read-back; only `fde-task-pipeline`
orchestrates transitions; `needs_revision` remains `repair_required`; and
external instructions are tool-neutral for Doubao, WorkBuddy, TRAE, ChatGPT and
Claude.

**Step 2: Upgrade content without replacing useful history**

Add a concise v4 Phase 3 section to each Skill. Preserve historical task-design
and QC material, but mark old checklist/XLSX/S3 routes as internal compatibility
only. Preserve Yao-era interface value as common metadata, triggers, inputs,
outputs, and blocked reasons; do not preserve it as a parallel workflow.

**Step 3: Upgrade interface metadata**

Revise display descriptions and default prompts to route by role and Bitable
state. Add the missing `ecc-shared` interface. Do not add tool credentials,
table IDs, or write commands to external-facing Skills.

**Step 4: Validate all local mirrors**

Parse every changed YAML file, scan for contradictory lifecycle language and
sensitive values, and SHA-256 compare the `.agents` and `.claude` copies.

**Step 5: Record activation evidence**

Write the resulting Skill versions, hashes, validation results, and known
implementation freeze to `docs/business/FDE_PHASE3_SKILL_SUITE_V4.md`; do not
claim an online Bitable rollout.

### Task 3: Run an offline lifecycle fixture audit

**Files:**
- Modify: `docs/business/FDE_PHASE3_SKILL_SUITE_V4.md`

**Step 1: Define three synthetic lifecycle cases**

Cover accepted-first-pass to `Gold`, revision-request to `repair_required`, and
accepted-revision to `Repair`. Each case uses only placeholder Bitable identities
and hashes.

**Step 2: Verify the cases against the contract**

Confirm P0 gates, feedback classification, revision lineage, V5 eligibility,
and Compass receipt handling. A revision request alone must not produce `Repair`.

**Step 3: Record the implementation stop line**

State that form mapping, permissions, online writes, V5 official export, and
Compass live import remain blocked until the form blueprint is approved.

**Step 4: Commit**

```powershell
git add -- docs/business/FDE_PHASE3_SKILL_SUITE_V4.md
git commit -m "docs(fde): validate phase 3 skill suite v4"
```

## Final Verification

1. `git diff --check` is clean in the isolated Core worktree.
2. All changed `.agents` and `.claude` Skill mirrors have matching SHA-256 values.
3. Every changed interface YAML parses successfully.
4. Required v4 terms exist and conflicting `needs_revision -> Repair` language is absent.
5. No online Bitable call, credential, source material, R3 modification, push, or merge occurred.
