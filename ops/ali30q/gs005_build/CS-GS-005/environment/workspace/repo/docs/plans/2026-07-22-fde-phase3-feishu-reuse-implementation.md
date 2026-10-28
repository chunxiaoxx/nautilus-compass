# Phase 3 Feishu Reuse Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Reuse the existing Zhiyong Nautilus Feishu application to add a tested,
field-owned Phase 3 adapter without creating a new application, replacing the
legacy v06 runner, or exposing buyer evidence.

**Architecture:** Add a small Phase 3 adapter beside the existing FDE runners.
It loads the existing application identity, performs schema probes and Bitable
operations through injected clients, keeps field ownership in a versioned map,
and emits bounded requests for the existing Bitable automation extension.

**Tech Stack:** Python standard library HTTP, pytest, existing Feishu
`tenant_access_token` flow, and existing `ecc-shared` documentation.

---

## Preconditions

- Work only in `C:\Users\chunx\Projects\nautilus-core\.worktrees\fde-phase3-recruiting-ops`.
- Load the existing credential file only into a short-lived process. Never print,
  commit, copy, or transmit credentials.
- Do not read original buyer submissions. The only external read before approval
  is target schema metadata and approved feedback fields.
- Do not modify R3/Reborn, push, merge, or change legacy v06 field maps.
- Do not create a form, record, automation, or buyer-Sheet write before the
  field map is approved.

## Task 1: Register existing Feishu assets

**Files:**
- Create: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Write the registry**

Record only non-secret facts: the existing Zhiyong Nautilus application, a
controlled reference to the Bitable automation extension (not its resource
identifier), secret-source location, tenant-token verification date, reusable
runner patterns, and the requirement that this application is the only Phase 3
Feishu identity.

Use the statuses `verified`, `needs_schema_probe`, `deprecated`, and
`blocked`. Exclude app IDs, base tokens, record IDs, personal names, and buyer
content.

**Step 2: Validate and commit**

```powershell
git diff --check
git add docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md
git commit -m "docs(fde): register existing phase 3 feishu assets"
```

Expected: `git diff --check` exits `0`.

## Task 2: Add a pure field-ownership contract

**Files:**
- Create: `phase3/backend/services/fde_phase3_feishu.py`
- Create: `phase3/backend/tests/test_fde_phase3_feishu.py`

**Step 1: Write failing tests**

```python
from services.fde_phase3_feishu import FieldOwner, FieldRule, FieldMap, Transition

def test_field_map_rejects_duplicate_external_owner():
    rules = [
        FieldRule("buyer_verdict", FieldOwner.BUYER, "buyer_verdict"),
        FieldRule("buyer_verdict_copy", FieldOwner.BUYER, "buyer_verdict"),
    ]
    with pytest.raises(ValueError, match="duplicate external field"):
        FieldMap(rules)

def test_transition_rejects_revision_without_direct_predecessor():
    with pytest.raises(ValueError, match="revision_of"):
        Transition.repair("opaque-task", "attempt-2", revision_of=None)

def test_compass_payload_excludes_prohibited_fields():
    mapping = FieldMap([
        FieldRule("p0_status", FieldOwner.INTERNAL, "P0"),
        FieldRule("buyer_verdict", FieldOwner.BUYER, "验收"),
        FieldRule("share_reference", FieldOwner.PROHIBITED, "分享链接"),
    ])
    assert mapping.compass_payload({
        "p0_status": "pass", "buyer_verdict": "Gold", "share_reference": "secret-url",
    }) == {"p0_status": "pass", "buyer_verdict": "Gold"}
```

**Step 2: Verify failure**

```powershell
Set-Location phase3\backend
python -m pytest tests/test_fde_phase3_feishu.py -q
```

Expected: FAIL because the module does not exist.

**Step 3: Implement the minimum contract**

Implement immutable `FieldOwner`, `FieldRule`, `FieldMap`, and
`Transition`. Allow only `BUYER`, `INTERNAL`, `OUTBOUND`, and
`PROHIBITED`. Reject duplicate external bindings, unknown ownership, and a
repair command without a direct predecessor. The new-task contract must keep
the business fields explicit: `title`, `task_type`, `attachment_format_tags`,
`source_materials`, `expected_output`, and `key_steps`. An Evidence Pack is
additive proof; it must never replace these fields.

`FieldMap.compass_payload` must emit only schema-approved fields. It must
exclude Bitable record IDs, `revision_of`, raw evidence, attachments, share
references, credentials, and buyer identity.

**Step 4: Verify and commit**

```powershell
Set-Location phase3\backend
python -m pytest tests/test_fde_phase3_feishu.py -q
git add services/fde_phase3_feishu.py tests/test_fde_phase3_feishu.py
git commit -m "feat(fde): add phase 3 field ownership contract"
```

Expected: PASS.

## Task 3: Add a read-only authenticated schema probe

**Files:**
- Modify: `phase3/backend/services/fde_phase3_feishu.py`
- Create: `phase3/backend/scripts/probe_phase3_feishu_schema.py`
- Modify: `phase3/backend/tests/test_fde_phase3_feishu.py`

**Step 1: Write failing tests**

```python
def test_schema_probe_calls_only_list_tables_and_list_fields(fake_client):
    result = probe_schema(fake_client, base_token="base-token")
    assert result.table_names == ("任务", "审核")
    assert fake_client.calls == [
        "list_tables", "list_fields:tbl_task", "list_fields:tbl_review",
    ]

def test_schema_probe_hashes_schema_without_values(fake_client):
    result = probe_schema(fake_client, base_token="base-token")
    assert len(result.schema_hash) == 64
    assert "raw_value" not in result.to_audit_dict()
```

**Step 2: Verify failure**

```powershell
Set-Location phase3\backend
python -m pytest tests/test_fde_phase3_feishu.py -q
```

Expected: FAIL because `probe_schema` does not exist.

**Step 3: Implement the probe**

Add an injected `FeishuBitableClient` protocol with `list_tables` and
`list_fields`. Implement the HTTP client with the established tenant-token and
`code != 0` envelope check. The probe must make no record, form, automation,
or Sheet-value call.

The CLI must require an explicit `--base-token`, print only table names, field
names/types/options and a schema SHA-256, redact all tokens, and refuse writes.

**Step 4: Verify and commit**

```powershell
Set-Location phase3\backend
python -m pytest tests/test_fde_phase3_feishu.py -q
python scripts/probe_phase3_feishu_schema.py --help
git add services/fde_phase3_feishu.py scripts/probe_phase3_feishu_schema.py tests/test_fde_phase3_feishu.py
git commit -m "feat(fde): add read-only phase 3 schema probe"
```

Expected: focused tests PASS; help has no write command.

## Task 4: Add idempotent Bitable transitions with mandatory read-back

**Files:**
- Modify: `phase3/backend/services/fde_phase3_feishu.py`
- Modify: `phase3/backend/tests/test_fde_phase3_feishu.py`

**Step 1: Write failing tests**

```python
def test_transition_writer_reads_back_created_attempt(fake_client):
    receipt = writer.submit_attempt(command)
    assert receipt.record_id == "rec_attempt_1"
    assert fake_client.calls[-1] == "get_record:rec_attempt_1"

def test_transition_writer_replays_idempotency_key_without_duplicate(fake_client):
    assert writer.submit_attempt(command).record_id == writer.submit_attempt(command).record_id
    assert fake_client.create_count == 1

def test_transition_writer_refuses_verdict_and_buyer_owned_fields(fake_client):
    with pytest.raises(ValueError, match="buyer-owned|verdict"):
        writer.submit_attempt(command_with_verdict)
```

**Step 2: Verify failure**

```powershell
Set-Location phase3\backend
python -m pytest tests/test_fde_phase3_feishu.py -q
```

Expected: FAIL because the writer does not exist.

**Step 3: Implement the minimum writer**

Implement `BitableTransitionWriter` with an injectable idempotency store.
Permit only: create a task draft with its first linked interaction attempt,
create a later interaction attempt for an existing task, create a review
record, and write an export receipt. A new-task command must atomically bind
the explicit task specification to its first attempt; a revision command must
resolve the direct predecessor internally. Every command must use an opaque
internal task anchor, reject buyer-owned and final-verdict fields, perform one
bounded write sequence, then read back the returned records and validate
requested values.

Map any failure to an explicit blocked receipt. Do not add a generic update
method or last-write-wins sync.

**Step 4: Verify and commit**

```powershell
Set-Location phase3\backend
python -m pytest tests/test_fde_phase3_feishu.py -q
git add services/fde_phase3_feishu.py tests/test_fde_phase3_feishu.py
git commit -m "feat(fde): add idempotent phase 3 bitable transitions"
```

Expected: PASS, including duplicate replay and read-back assertions.

## Task 5: Add a reviewed field-map template and asset registry update

**Files:**
- Create: `docs/business/FDE_PHASE3_BUYER_FIELD_MAP_TEMPLATE.md`
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Create the template**

Define columns for external field name, internal logical field, field owner,
direction, type/allowed values, redaction rule, idempotency anchor, read-back
proof, and approval status. Use logical examples only.

Explicitly prohibit raw conversation, attachment, share reference, platform log
identifier, account information, buyer identity, Bitable record identity, and
`revision_of` from Compass.

**Step 2: Update and commit**

```powershell
git diff --check
git add docs/business/FDE_PHASE3_BUYER_FIELD_MAP_TEMPLATE.md docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md
git commit -m "docs(fde): add phase 3 field map review template"
```

Expected: exit code `0`.

## Task 6: Update existing skills without adding a new one

**Files:**
- Modify: `C:\Users\chunx\.agents\skills\ecc-shared\SKILL.md`
- Modify: `C:\Users\chunx\.agents\skills\ecc-shared\agents\interface.yaml`
- Mirror: `C:\Users\chunx\.claude\skills\ecc-shared\SKILL.md`
- Mirror: `C:\Users\chunx\.claude\skills\ecc-shared\agents\interface.yaml`
- Modify: `docs/business/FDE_PHASE3_SKILL_SUITE_V4.md`

**Step 1: Update the skill contract**

Point `ecc-shared` to the new schema probe and transition writer. State that
it reuses Zhiyong Nautilus and the existing automation BlockTypeID, is the sole
Bitable writer/read-back owner, and cannot decide P0, buyer verdict, Repair, or
payment.

**Step 2: Mirror and verify**

```powershell
$agent = 'C:\Users\chunx\.agents\skills\ecc-shared'
$claude = 'C:\Users\chunx\.claude\skills\ecc-shared'
Get-FileHash "$agent\SKILL.md", "$claude\SKILL.md" -Algorithm SHA256
python -c "import yaml, pathlib; yaml.safe_load(pathlib.Path(r'C:\Users\chunx\.agents\skills\ecc-shared\agents\interface.yaml').read_text(encoding='utf-8')); print('yaml=valid')"
```

Expected: matching skill hashes and `yaml=valid`.

**Step 3: Record and commit repository evidence**

Record only adapter entrypoint and mirror hashes in the repository-owned skill
suite receipt. Do not include a credential, app ID, or base ID.

```powershell
git add docs/business/FDE_PHASE3_SKILL_SUITE_V4.md
git commit -m "docs(fde): register reused phase 3 feishu adapter"
```

## Task 7: Run the gated live schema probe and stop for map approval

**Files:**
- Create: `docs/business/FDE_PHASE3_SCHEMA_PROBE_RECEIPT.md`
- Modify: `docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md`

**Step 1: Obtain the target identifiers**

Require the internal Phase 3 Bitable base token and separate authorization for
the buyer Sheet schema. Do not infer either from a Wiki URL.

**Step 2: Run the read-only probe**

```powershell
Set-Location phase3\backend
python scripts/probe_phase3_feishu_schema.py --base-token '<provided-at-runtime>'
```

Expected: table and field metadata plus schema hash; no records or forms written.

**Step 3: Record a redacted receipt**

Store probe time, application identity label, table-count, schema hash, and
missing permissions. Exclude tokens, IDs, field samples, and buyer content.

**Step 4: Stop and request map approval**

Present the completed buyer/internal field map. Do not create the online form,
records, buyer-Sheet sync, V5 export, or Compass import until it is approved.

**Step 5: Commit**

```powershell
git add docs/business/FDE_PHASE3_SCHEMA_PROBE_RECEIPT.md docs/business/FDE_PHASE3_FEISHU_ASSET_REGISTRY.md
git commit -m "docs(fde): record phase 3 schema probe"
```

## Task 8: Implement the one-record form and automation after map approval

**Files:**
- Modify: `phase3/backend/services/fde_phase3_feishu.py`
- Modify: `phase3/backend/scripts/probe_phase3_feishu_schema.py`
- Modify: `phase3/backend/tests/test_fde_phase3_feishu.py`
- Modify: `docs/business/FDE_PHASE3_BITABLE_FORM_BLUEPRINT.md`
- Create: `docs/business/FDE_PHASE3_FIRST_RECORD_RECEIPT.md`

**Step 1: Add failing command-validation tests**

Cover form payload normalization, explicit new-task fields, six-round metadata,
new-task creation of one task plus one first attempt, revision-only creation of
one later attempt, internal `revision_of` enforcement, and rejection of
review/export fields in an external-form payload.

**Step 2: Implement bounded provisioning**

Expose explicit `--dry-run` and `--apply` commands. `--apply` requires a
user-approved field-map SHA and an explicit one-record flag. The existing
automation BlockTypeID may call the validated transition entrypoint; it may not
write arbitrary records.

**Step 3: Execute and independently read back one authorized record**

Collect Bitable read-back, V5 manifest hash, Compass receipt hash, and no raw
evidence. On any missing condition, record a blocked receipt and stop.

**Step 4: Verify and commit**

```powershell
Set-Location phase3\backend
python -m pytest tests/test_fde_phase3_feishu.py -q
git add services/fde_phase3_feishu.py scripts/probe_phase3_feishu_schema.py tests/test_fde_phase3_feishu.py docs/business/FDE_PHASE3_BITABLE_FORM_BLUEPRINT.md docs/business/FDE_PHASE3_FIRST_RECORD_RECEIPT.md
git commit -m "feat(fde): run guarded phase 3 first record loop"
```

Expected: tests PASS and the receipt contains independent read-back evidence.
