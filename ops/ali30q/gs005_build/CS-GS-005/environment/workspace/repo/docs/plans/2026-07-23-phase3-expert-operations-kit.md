# Phase 3 Expert Operations Kit Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task.

**Goal:** Deliver a source-aligned, external-safe Phase 3 recruiting and operations kit that the recruiting team can use before online workflow activation.

**Architecture:** Keep one audience-specific Markdown package under `docs/business/phase3_expert_operations/`. The external expert document contains only public requirements and approved payment wording; the internal SOP points to controlled state transitions without duplicating runtime logic. A small deterministic test verifies required sections and rejects internal-only vocabulary in expert-facing content.

**Tech Stack:** Markdown, Python standard library, pytest.

---

### Task 1: Create the package entry point and recruiting kit

**Files:**
- Create: `docs/business/phase3_expert_operations/README.md`
- Create: `docs/business/phase3_expert_operations/01_RECRUITING_KIT.md`

**Step 1: Write the entry point**

State the intended audiences, approved source documents, use order, and the
explicit boundary that this package does not trigger an online workflow.

**Step 2: Write recruiting material**

Include target-expert profile/JD, poster copy, private invitation copy,
social/group copy, group welcome wording, the approved 200 RMB / three-business-day
settlement statement, and clear limits on what cannot be promised.

**Step 3: Verify content**

Run:

```powershell
rg -n "专家画像|私聊邀约|200 元|3 个工作日|不等于甲方通过" docs/business/phase3_expert_operations/01_RECRUITING_KIT.md
```

Expected: all required sections appear.

### Task 2: Create the expert onboarding guide

**Files:**
- Create: `docs/business/phase3_expert_operations/02_EXPERT_ONBOARDING.md`

**Step 1: Write the 15-minute lesson and operating SOP**

Cover the approved Office Task mode, fresh conversation, at least six relevant
turns, per-turn human reasons, 24-hour window, task-design criteria, attachment
requirements, and formal Form submission.

**Step 2: Add safe examples and support copy**

Add a fictional evidence-package completion template, daily reminders, FAQ,
and repair-notice templates. Mark examples as templates, not reusable evidence.

**Step 3: Verify content**

Run:

```powershell
rg -n "15 分钟|至少 6 轮|24 小时|证据包填写示例|返修通知" docs/business/phase3_expert_operations/02_EXPERT_ONBOARDING.md
```

Expected: all required sections appear.

### Task 3: Create the recruiting-team operator SOP

**Files:**
- Create: `docs/business/phase3_expert_operations/03_OPERATOR_SOP.md`

**Step 1: Define staff workflow**

Specify recruiting, screening, group creation, training, task assignment,
formal status lookup, repair handoff, buyer-acceptance settlement confirmation,
and escalation.

**Step 2: Enforce ownership boundaries**

State that the Form creates initial records; Nautilus alone controls later
business writes; buyer acceptance remains external; V5 and Compass receive only
eligible deidentified exports.

**Step 3: Verify content**

Run:

```powershell
rg -n "筛选|建群|派题|结算|Bitable read-back|Nautilus" docs/business/phase3_expert_operations/03_OPERATOR_SOP.md
```

Expected: every operational stage and authority boundary appears.

### Task 4: Add deterministic content coverage test

**Files:**
- Create: `phase3/backend/tests/test_fde_phase3_expert_operations_kit.py`

**Step 1: Write the failing test**

Assert that all four package files exist, each required heading appears, payment
wording is exact, and the expert-facing files do not contain internal-only
terms such as `revision_of`, `payload_hash`, or `manifest_hash`.

**Step 2: Run test to verify it fails**

Run:

```powershell
python -m pytest phase3/backend/tests/test_fde_phase3_expert_operations_kit.py -q
```

Expected: FAIL because the package files do not exist yet.

**Step 3: Create the documents**

Write the three audience documents and README to satisfy the test without
adding unapproved workflow claims.

**Step 4: Run the content test and relevant form regression**

Run:

```powershell
python -m pytest phase3/backend/tests/test_fde_phase3_expert_operations_kit.py phase3/backend/tests/test_fde_phase3_single_submission_forms.py -q
```

Expected: PASS.

**Step 5: Commit**

```powershell
git add docs/business/phase3_expert_operations phase3/backend/tests/test_fde_phase3_expert_operations_kit.py
git commit -m "docs(fde): add phase3 expert operations kit"
```
