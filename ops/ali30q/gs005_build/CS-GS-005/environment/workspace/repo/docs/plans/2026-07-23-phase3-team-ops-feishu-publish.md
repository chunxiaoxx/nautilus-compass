# Phase 3 Team Operations Feishu Publish Plan

> **For Codex:** Execute this plan with the configured Feishu custom app. Do
> not touch Bitable, Forms, buyer Sheets, V5, or Compass runtime.

**Goal:** Publish the approved offline Phase 3 team-operations package as a
readable Feishu Wiki directory under the user-owned Wiki root.

**Architecture:** The existing Sheet root remains untouched. Create one child
Wiki document named `第三期团队运营包`, then create four child documents from
the version-controlled Markdown sources. Use the existing custom-app tenant
token from the controlled local secret file only in process memory. Each write
is followed by a read-back of title and rendered-content hash; no secret or
source material is logged.

**Sources:**

- `docs/business/phase3_expert_operations/README.md`
- `docs/business/phase3_expert_operations/01_RECRUITING_KIT.md`
- `docs/business/phase3_expert_operations/02_EXPERT_ONBOARDING.md`
- `docs/business/phase3_expert_operations/03_OPERATOR_SOP.md`

---

### Task 1: Verify the publish target and avoid duplicates

1. Obtain a tenant access token from the controlled local secret file without
   printing credentials.
2. Read the configured user-owned Wiki root node and list only its immediate
   children.
3. Stop if a same-title operations root already exists; report its node instead
   of creating a duplicate.

### Task 2: Create the directory and four documents

1. Create one `docx` Wiki child called `第三期团队运营包` beneath the verified
   root.
2. Create the four source-aligned child documents beneath it, in source order.
3. Convert Markdown conservatively into doc blocks. Preserve headings,
   paragraphs, lists and tables as readable text; never include secrets,
   original buyer materials, raw evidence or Bitable state.

### Task 3: Verify publish results

1. Read every created Wiki node back and confirm its title and parent.
2. Read every document block tree and compare a SHA-256 hash of exported plain
   text with the locally rendered source text.
3. Report URLs, node/document titles, hashes and any conversion limitations.
   Do not claim success from a write response alone.

### Task 4: Record the event

1. Commit this plan only; the Feishu content itself is an external artifact.
2. Write a Compass observation containing only titles, document identifiers,
   source commit and verification result. It must not contain content, raw
   inputs, credentials or business records.
