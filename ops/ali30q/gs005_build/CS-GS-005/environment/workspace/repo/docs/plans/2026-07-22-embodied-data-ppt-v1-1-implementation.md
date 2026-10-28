# Embodied Data Pitch Deck v1.1 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Revise the external pitch deck so it presents the verified partner-base operating arrangement as a credible delivery-start condition without claiming a named endorsement or completed customer case.

**Architecture:** Keep the existing 20-slide visual system and rebuild only the content-bearing objects on slides 6, 9, 10, 15, and 18. Update the repository evidence records first, then edit the external artifact-tool source, export a distinct v1.1 PPTX, render and inspect the changed slides, and finally run whole-deck mechanical and claim-boundary QA.

**Tech Stack:** Markdown evidence records, JavaScript ES modules, `@oai/artifact-tool`, bundled presentation renderer, PowerShell verification, Git.

---

### Task 1: Update the claim ledger and audience-facing slide copy

**Files:**
- Modify: `docs/presentations/guoshu-embodied-data-network/evidence-ledger.md`
- Modify: `docs/presentations/guoshu-embodied-data-network/source-notes.md`
- Modify: `docs/presentations/guoshu-embodied-data-network/slide-content.md`
- Modify: `docs/presentations/guoshu-embodied-data-network/slide-content-09-16.md`

**Step 1: Replace the outdated current-state fact**

Record the user-confirmed facts:

- cooperation with a “头部具身数据企业代理方”;
- access to a cooperation base and a path to co-build capacity;
- Guoshu supplies and organizes personnel;
- the partner supports guidance, training, base operations and dispatch coordination;
- Guoshu remains responsible for project operations, quality closure and final delivery.

Remove the current-state statement “尚无具身数据首单”. Preserve the restriction against claiming completed cases, named endorsement, operating scale, revenue or fixed acceptance performance.

**Step 2: Update slide 6, 9, 10, 15 and appendix A2 copy**

Use these exact audience-facing claims:

- Slide 6 title: `国曙的起点，是协同基地与组织交付能力`
- Slide 6 callout: `合作基础已建立，规模能力随订单验证并扩展`
- Slide 9 title: `合作从边界清晰、可验收的付费 POC 开始`
- Slide 10 chain: `甲方需求 → 国曙项目负责 → 合作方基地/培训/派单支持 → 国曙人员执行与质控 → 联合验收`
- Slide 15 stage 1: `协同基地启动｜合作基地 / 人员组织 / 小批验收`
- Appendix A2 stage: `运营设计基线｜需项目验证`

**Step 3: Run text-boundary checks**

Run:

```powershell
rg -n "尚无具身数据首单|需首单验证|与光轮智能合作|光轮智能代理|光轮授权" docs/presentations/guoshu-embodied-data-network
```

Expected: no matches. Public target-company research may remain in internal source notes, but it must not be connected to the cooperation claim.

**Step 4: Commit**

```powershell
git add -- docs/presentations/guoshu-embodied-data-network/evidence-ledger.md docs/presentations/guoshu-embodied-data-network/source-notes.md docs/presentations/guoshu-embodied-data-network/slide-content.md docs/presentations/guoshu-embodied-data-network/slide-content-09-16.md
git commit -m "docs: correct embodied data delivery readiness claims"
```

### Task 2: Revise the artifact-tool presentation source

**Files:**
- Modify: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/deck.mjs`
- Modify: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/qa/qa-ledger.txt`

**Step 1: Rebuild slide 6 copy**

Replace the title, four operating claims and bottom callout. Keep the current photograph and label `概念视觉｜非项目现场`. Do not add a partner logo.

**Step 2: Reword slide 9**

Replace `FIRST ORDER` with `STARTING POINT` and remove “首单” from the title while keeping the four-step paid-POC structure.

**Step 3: Rebuild slide 10 responsibility chain**

Use five nodes in this order:

1. 甲方需求
2. 国曙项目负责
3. 合作方支持
4. 国曙执行与质控
5. 联合验收

The third node subcopy must read `基地支持｜指导培训｜派单协同`. Connectors must be created behind nodes and point left-to-right.

**Step 4: Update slide 15 and appendix A2**

Replace “首单验证” and “需首单验证” with the approved copy. Keep all future quality-infrastructure and data-market claims labeled as roadmap.

**Step 5: Update the QA ledger**

Add the v1.1 claim checks and remove the v1 check that required the deck to state there was no first order.

### Task 3: Export a distinct v1.1 deck

**Files:**
- Create: `output/国曙具身数据生产网络_业务介绍_v1.1.pptx`

**Step 1: Build the scratch deck**

Run from `C:/Users/chunx` so the bundled artifact runtime resolves:

```powershell
node "C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/deck.mjs"
```

Expected: exit code 0 and `slides: 20`.

**Step 2: Copy without overwriting v1**

Copy the generated scratch PPTX to `output/国曙具身数据生产网络_业务介绍_v1.1.pptx`.

### Task 4: Render and verify the v1.1 deck

**Files:**
- Test: `output/国曙具身数据生产网络_业务介绍_v1.1.pptx`
- Inspect: scratch rendered slides 6, 9, 10, 15 and 18

**Step 1: Render the entire deck**

Use the bundled `render_slides.py` with the isolated `pydeps` path. Expected: 20 PNG files.

**Step 2: Inspect changed slides at full size**

Verify:

- no title wrapping or text overlap;
- slide 6 visibly communicates the partner-base operating model;
- slide 10 arrows flow left-to-right and do not cross labels;
- slide 15 stage 1 copy fits inside its card;
- appendix A2 says `需项目验证`;
- no partner name or logo appears.

**Step 3: Run mechanical overflow QA**

Run `slides_test.py` on the final v1.1 PPTX.

Expected: `Test passed. No overflow detected.`

**Step 4: Run claim-boundary QA**

Inspect the artifact-tool NDJSON and assert:

- required: `头部具身数据企业代理方`, `指导培训`, `派单协同`, `规模能力随订单验证并扩展`;
- absent: `尚无具身数据首单`, `需首单验证`, `与光轮智能合作`, `光轮智能代理`, `光轮授权`, `战略合作`, `独家合作`, `官方合作基地`;
- slide count is 20 and the final file is a valid OOXML archive.

**Step 5: Commit the final artifact**

```powershell
git add -- "output/国曙具身数据生产网络_业务介绍_v1.1.pptx"
git commit -m "docs: revise embodied data pitch deck delivery readiness"
```
