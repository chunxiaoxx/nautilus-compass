# Embodied Data Pitch Deck v1.2 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a verified company-and-contact closing slide, correct the public source page, and embed a scannable QR code for the canonical Guoshu embodied-data webpage.

**Architecture:** Preserve the v1.1 20-slide visual system, revise slide 20 in the existing artifact-tool builder, and append slide 21 as a new closing composition. Treat the old PPT as content provenance only, label its numbers as Guoshu-system accumulation, generate the QR as a raster asset outside the repository, and export a distinct v1.2 PPTX.

**Tech Stack:** Markdown evidence records, PowerShell OOXML tests, JavaScript ES modules, `@oai/artifact-tool`, QRServer PNG generation, OpenCV QR decoding, bundled presentation renderer, Git.

---

### Task 1: Add failing v1.2 acceptance tests and update content records

**Files:**
- Create: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/qa/v1_2_closing_test.ps1`
- Modify: `docs/presentations/guoshu-embodied-data-network/source-notes.md`
- Modify: `docs/presentations/guoshu-embodied-data-network/slide-content-09-16.md`

**Step 1: Write the failing acceptance test**

The PowerShell test must extract text from the final PPTX OOXML and assert:

- exactly 21 slides;
- required text: `上海国曙人工智能有限公司`, `王春晓`, `18510625230`, `樊金亮`, `17621151002`, `国曙具身数据服务能力页`, `fde.nautilus.social/embodied/public/`;
- required Guoshu-system metrics: `2017`, `4000+`, `500+`, `50+`, `105+`, `20+`;
- forbidden text: `旧网页与旧 PPT`, `仅作内容线索`.

**Step 2: Verify RED against v1.1**

Run the test against `output/国曙具身数据生产网络_业务介绍_v1.1.pptx`.

Expected: FAIL because the deck has 20 slides and lacks the company/contact close.

**Step 3: Update source and slide-content records**

Record:

- current company name and contacts as user-confirmed facts;
- old PPT metrics as “国曙体系积累”;
- canonical webpage `https://fde.nautilus.social/embodied/public/` with live HTTP 200 evidence;
- new A5 company slide and the corrected source-page item 11.

**Step 4: Commit content records**

```powershell
git add -- docs/presentations/guoshu-embodied-data-network/source-notes.md docs/presentations/guoshu-embodied-data-network/slide-content-09-16.md
git commit -m "docs: add Guoshu company close content"
```

### Task 2: Generate the QR asset and build slide 20–21

**Files:**
- Create: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/assets/guoshu-public-qr.png`
- Modify: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/deck.mjs`
- Modify: `C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b/codex-presentations/manual-20260722/guoshu-embodied-data-network/tmp/qa/qa-ledger.txt`

**Step 1: Generate a high-contrast QR PNG**

Request a 600×600 PNG from QRServer using the URL-encoded target:

`https://fde.nautilus.social/embodied/public/`

Save it in the scratch asset directory. Do not add a logo or crop the quiet zone.

**Step 2: Verify QR decoding before use**

Install `opencv-python-headless` into the existing scratch `pydeps` directory only if unavailable. Decode the PNG with `cv2.QRCodeDetector()`.

Expected decoded value:

`https://fde.nautilus.social/embodied/public/`

**Step 3: Correct slide 20**

- Item 11: `国曙具身数据服务能力页`
- Item 11 URL: `fde.nautilus.social/embodied/public/`
- Remove all visible references to old web/PPT production notes.
- Footer: `访问日期：2026-07-22｜公开来源支持行业研判；公司与合作信息以本公司确认口径为准`.

**Step 4: Append slide 21**

Use the approved layout:

- company name and positioning;
- main title: `把国曙体系的组织能力，转化为具身数据交付能力`;
- continuous evidence band with `2017`, `4000+`, `500+`, `50+`, `105+`, `20+`;
- three capability-transfer statements;
- contacts: 王春晓 / 18510625230 and 樊金亮 / 17621151002;
- large QR image, short URL and scan instruction;
- positive footnote attributing the metrics to Guoshu-system enterprise-service, workforce-organization and digital-operations accumulation.

**Step 5: Export v1.2 without overwriting v1.1**

Build from `C:/Users/chunx`, then copy the scratch PPTX to:

`output/国曙具身数据生产网络_业务介绍_v1.2.pptx`

Expected build output: `slides: 21`.

### Task 3: Verify, render and commit v1.2

**Files:**
- Test: `output/国曙具身数据生产网络_业务介绍_v1.2.pptx`
- Inspect: all 21 rendered slide PNGs

**Step 1: Verify GREEN acceptance test**

Run `v1_2_closing_test.ps1` against v1.2.

Expected: PASS with 21 slides and all required company/contact/web strings.

**Step 2: Verify the live webpage and QR**

- HTTP HEAD/GET to `https://fde.nautilus.social/embodied/public/` must return 200.
- Decode `guoshu-public-qr.png`; value must exactly match the public URL.

**Step 3: Render and inspect all slides**

Render the 21-slide deck at 1600×900. Inspect every slide individually at full size, with special attention to slides 20 and 21.

Verify:

- company title and six evidence values are readable;
- contact names and numbers are accurate;
- QR has sufficient quiet zone and is not stretched;
- slide 20 contains the corrected website source;
- no overlap, clipping, bad crop, broken connector or inconsistent footer.

**Step 4: Run overflow and archive checks**

Run `slides_test.py` and validate the PPTX contains 21 slide XML entries.

Expected: `Test passed. No overflow detected.`

**Step 5: Commit the final artifact**

```powershell
git add -- "output/国曙具身数据生产网络_业务介绍_v1.2.pptx"
git commit -m "docs: add Guoshu company and contact close"
```
