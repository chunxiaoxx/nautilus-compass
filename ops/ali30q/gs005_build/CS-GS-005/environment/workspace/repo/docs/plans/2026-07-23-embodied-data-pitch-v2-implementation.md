# Embodied Data Pitch v2.0 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the 21-page general introduction with a new 13-page customer-facing deck that explains the unified embodied-training loop, EGO/UMI routes, and the base/crowd/vertical supply model without overstating current capability.

**Architecture:** Preserve v1.2 as a historical artifact and build a distinct v2.0 PPTX from a new artifact-tool builder. The v2 story has two orthogonal layers: EGO/UMI are data-capture protocols; cooperative base, distributed crowd and vertical work sites are supply-and-operations units. Every page must distinguish current, configurable and roadmap claims.

**Tech Stack:** Markdown evidence records, PowerShell OOXML acceptance tests, JavaScript ES modules, `@oai/artifact-tool`, QR PNG asset, bundled presentation renderer, OpenCV QR decoding, Git.

---

### Task 1: Write the v2.0 RED acceptance test and update evidence records

**Files:**
- Create: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/qa/v2_0_13_page_acceptance_test.ps1`
- Create: `docs/presentations/guoshu-embodied-data-network/slide-content-v2-13.md`
- Modify: `docs/presentations/guoshu-embodied-data-network/evidence-ledger.md`
- Modify: `docs/presentations/guoshu-embodied-data-network/source-notes.md`

**Step 1: Write a failing PowerShell acceptance test**

Extract `ppt/slides/slide*.xml` text from a passed PPTX and assert:

```powershell
$required = @(
  'EGO', 'UMI', '协同基地', '分布式众包', '垂直现场',
  '合格 episode', '付费 POC', '上海国曙人工智能有限公司',
  '王春晓', '18510625230', '樊金亮', '17621151002',
  'fde.nautilus.social/embodied/public/'
)
$forbidden = @(
  '已建成全国网络', '全自动验收已上线', '第三方验收认证已商用',
  '尚无具身数据首单', '旧网页与旧 PPT'
)
if ($slideEntries.Count -ne 13) { throw "Expected 13 slides, found $($slideEntries.Count)" }
```

Use the existing `claim_boundary_test.ps1` XML-reading pattern. Required phrases must all be present and no forbidden phrase may appear.

**Step 2: Verify RED against v1.2**

Run:

```powershell
& "$scratch\qa\v2_0_13_page_acceptance_test.ps1" `
  -Pptx "output\国曙具身数据生产网络_业务介绍_v1.2.pptx"
```

Expected: FAIL with `Expected 13 slides, found 21`.

**Step 3: Add source and claim boundaries**

Add the following evidence rules:

- EGO: first-person wearable route; only claim task/scene/human-workflow coverage, not direct robot-action transfer without alignment.
- UMI: a portable end-effector-adjacent collection interface; only claim route-level reference, not a current Guoshu device or zero-adaptation transfer.
- Add official source URLs for NVIDIA EgoScale, EgoMimic and UMI.
- Reclassify base as current project-start resource; crowd, vertical at-work collection and automated operations as evidence-gated roadmap.
- State that the two primary buyers share one embodied-training loop; their different priorities are different views of one data package.

**Step 4: Create the 13-page content baseline**

Write the final on-screen copy, visual purpose, evidence IDs, stage labels and forbidden claims for pages 01–13 from the approved redesign document. Include the 13 titles exactly as designed, and specify the three required diagrams:

1. Embodied training loop.
2. EGO/UMI × base/crowd/vertical matrix.
3. Evidence-gated POC-to-scale flow.

**Step 5: Commit evidence and content**

```powershell
git add -- docs/presentations/guoshu-embodied-data-network/evidence-ledger.md `
  docs/presentations/guoshu-embodied-data-network/source-notes.md `
  docs/presentations/guoshu-embodied-data-network/slide-content-v2-13.md
git commit -m "docs: define embodied data pitch v2 content"
```

### Task 2: Build a new 13-page visual system and PPTX

**Files:**
- Create: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/deck-v2.mjs`
- Reuse: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/assets/guoshu-public-qr.png`
- Modify: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/qa/qa-ledger.txt`
- Create: `output/国曙具身数据生产网络_业务介绍_v2.0.pptx`

**Step 1: Start with the same canvas, but not the old slide layouts**

Use 1280×720, warm-white/ink/orange/cyan colors and Microsoft YaHei. Do not copy a v1.2 composition. Build three diagram-first layouts:

- Slide 03: horizontal embodied-training loop with EGO and UMI as separate colored lanes merging into an accepted episode and diverging to world-model and robot-policy uses.
- Slide 06: 2×3 matrix with EGO/UMI columns and cooperative base/distributed crowd/vertical worksite rows. Use an orange `当前/POC` marker only for the cooperative-base cell; use cyan `条件触发` markers for crowd and vertical expansion.
- Slide 12: gated flow with four visible gates: sample acceptance, rights/authorization, reproducibility, and pricing/settlement.

**Step 2: Build each slide from the approved copy**

Use page roles exactly:

```text
01 cover / partner position
02 four-part data gap
03 unified training loop
04 EGO technical route
05 UMI technical route
06 three supply units matrix
07 base quality-anchor operating model
08 crowd controlled-capacity operating model
09 vertical-worksite operating model
10 accepted episode and quality protocol
11 Guoshu delivery responsibility and current boundary
12 paid POC to evidence-gated scale
13 company, system accumulation, contacts and QR
```

For slides 04–05, include only vector technical diagrams and structured labels. No generic AI imagery may substitute for sensors, data fields, quality gates or limitations.

**Step 3: Apply claim labels and footers**

Use a small, consistent label per page:

- `当前可启动` only for cooperative-base POC, project responsibility and personnel organization.
- `按项目配置` for the customer-selected EGO/UMI data specification.
- `条件触发路径` for crowd, vertical worksite scale-out and Agent automation.

Include official source URLs in low-profile footers on EGO/UMI pages and never state research results as Guoshu performance.

**Step 4: Export without replacing v1.2**

Run the builder from `C:/Users/chunx`, then copy its output to:

```text
C:/Users/chunx/Projects/nautilus-main-rebuild/output/国曙具身数据生产网络_业务介绍_v2.0.pptx
```

Expected builder output: `slides: 13`.

### Task 3: Verify the new deck, inspect every page and commit it

**Files:**
- Test: `output/国曙具身数据生产网络_业务介绍_v2.0.pptx`
- Inspect: `tmp/final-render-v2.0/slide-1.png` through `slide-13.png`

**Step 1: Verify GREEN acceptance**

Run the test from Task 1 against v2.0.

Expected: 13 slides, every required phrase present, zero forbidden phrases.

**Step 2: Verify QR and structural integrity**

Decode both `guoshu-public-qr.png` and the QR rendered on slide 13 with OpenCV. Each result must equal:

```text
https://fde.nautilus.social/embodied/public/
```

Verify 13 OOXML slide entries and confirm the final PPTX hash matches the scratch export hash.

**Step 3: Render all pages at 1600×900 and inspect individually**

Run:

```powershell
$env:PYTHONPATH="$scratch\pydeps"
python "$presentationsSkill\container_tools\render_slides.py" `
  "$main\output\国曙具身数据生产网络_业务介绍_v2.0.pptx" `
  --output_dir "$scratch\final-render-v2.0" --width 1600 --height 900
```

Inspect all 13 PNGs at full size. Specifically verify:

- Slides 03, 06 and 12 make the two-layer model legible without reading body text.
- Slides 04 and 05 show non-overlapping technical fields and limitations.
- Slides 07–09 do not imply that crowd/vertical operations already exist at scale.
- Slide 13 metrics are visibly labeled as Guoshu-system accumulation and contacts/QR are readable.

**Step 4: Run overflow and claim QA**

```powershell
python "$presentationsSkill\container_tools\slides_test.py" `
  "$main\output\国曙具身数据生产网络_业务介绍_v2.0.pptx" `
  --width 1600 --height 900
```

Expected: `Test passed. No overflow detected.` Update `qa-ledger.txt` with the RED/GREEN result, render review and QR decode result.

**Step 5: Commit only the final customer artifact and content records**

```powershell
git add -- "output/国曙具身数据生产网络_业务介绍_v2.0.pptx"
git commit -m "docs: deliver 13-page embodied data pitch v2"
```
