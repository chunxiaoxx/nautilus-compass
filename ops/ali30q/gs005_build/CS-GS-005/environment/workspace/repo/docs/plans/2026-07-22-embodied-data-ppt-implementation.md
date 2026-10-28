# 国曙具身数据生产网络 PPT Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 制作一套完全重新设计、可对外投递、以首单 POC 为行动目标的“国曙具身数据生产网络”PowerPoint，并完成来源、事实边界和逐页视觉质量验证。

**Architecture:** 使用 16 页主叙事加附录的结构，先建立可验证的行业判断，再说明国曙作为单一责任方的产品、运营、商业模式、Agent 控制层、质量体系、飞轮和路线图。旧 PPT 只做内容线索；视觉从零设计。所有研究、脚本和预览放在仓库外的演示文稿 scratch workspace，最终 PPTX 输出到独立 worktree 的 output 目录。

**Tech Stack:** Node.js ES modules、@oai/artifact-tool、PowerPoint、Slides container tools、Web 一手来源、image search / imagegen、PowerShell、Git。

---

## 执行约束

- 当前分支：codex/embodied-data-ppt-v2。
- 工作树：C:/Users/chunx/Projects/nautilus-core/.worktrees/embodied-data-ppt-v2。
- 旧 PPT：C:/Users/chunx/Downloads/国曙集团_机器人数据采集_大模型训练师业务介绍.pptx，只读。
- 现有网页：https://fde.nautilus.social/embodied/partner/，仅作内容线索。
- 最终文件：output/国曙具身数据生产网络_业务介绍_v1.pptx。
- 不使用 python-pptx；必须使用 @oai/artifact-tool。
- 不使用旧 PPT 的版式、配色和页面结构。
- 不公开未经授权的合作方或客户名称、Logo 和案例。
- 不将计划、可协同能力或外部合作资源写成国曙已经验证的具身业务能力。
- 本任务未获授权使用子代理，执行时由当前会话单代理完成。

### Task 1: 建立外部演示文稿工作区

**Files:**
- Create: external scratch workspace under the host-provided visualization root
- Create: scratch/tmp/source-notes.txt
- Create: scratch/tmp/evidence-ledger.txt
- Create: scratch/tmp/slide-content.txt
- Create: scratch/tmp/visual-plan.txt
- Create: scratch/tmp/qa/qa-ledger.txt

**Step 1: 计算并记录路径**

Run:

    $env:PPT_TASK_SLUG='guoshu-embodied-data-network'
    $env:PPT_SCRATCH_ROOT='C:/Users/chunx/.codex/visualizations/2026/07/21/019f84e3-39b2-7771-b521-ec3ad2f4787b'
    $env:PPT_WORKSPACE="$env:PPT_SCRATCH_ROOT/codex-presentations/manual-20260722/$env:PPT_TASK_SLUG"
    $env:PPT_TMP="$env:PPT_WORKSPACE/tmp"

Expected: 所有 scratch 路径位于仓库外、宿主已提供的可写根目录内。

**Step 2: 创建目录**

Run:

    New-Item -ItemType Directory -Force -Path "$env:PPT_TMP/slides","$env:PPT_TMP/preview","$env:PPT_TMP/layout","$env:PPT_TMP/assets","$env:PPT_TMP/qa"

Expected: 目录均创建成功；仓库状态不发生变化。

**Step 3: 初始化来源、内容与 QA 台账**

Use apply_patch to create the five .txt files. Each file must begin with task name, date, version, and status.

**Step 4: 验证路径边界**

Run:

    Resolve-Path $env:PPT_WORKSPACE
    git -C 'C:/Users/chunx/Projects/nautilus-core/.worktrees/embodied-data-ppt-v2' status --short -- 'docs/plans' 'output'

Expected: scratch 不在 Git 工作树内；只有计划文件可能出现在指定路径状态中。

### Task 2: 建立事实与来源台账

**Files:**
- Modify: scratch/tmp/source-notes.txt
- Modify: scratch/tmp/evidence-ledger.txt

**Step 1: 登记用户确认的事实**

Add these as user-confirmed facts:

- 尚无具身数据采集首单。
- 国曙作为合同和交付责任主体。
- 已与不同合作方形成合作基础，但没有名称或 Logo 的公开授权。
- 首轮对象为光轮、大晓机器人、原力灵机。
- 以订单从 1 做到 10；基地、分布式网络、独立验收和数据市场均为发展方向。

**Step 2: 审计旧 PPT 与现有网页**

For every reusable claim, classify it as:

- VERIFIED_GROUP_FACT：可由集团资料核验。
- USER_CONFIRMED：用户已经确认。
- EXTERNAL_EVIDENCE：有一手外部来源。
- INFERENCE：基于来源的商业研判。
- ROADMAP：未来建设。
- REJECT：不进入新版。

Explicitly reject unverified customer logos, embodied delivery cases, owned data products, mature national capacity, guaranteed quality rates, pricing margins and model improvements.

**Step 3: 核验外部研究**

Use official or primary sources for:

- EgoScale technical evidence and its limitations.
- Shift task-platform, wearable collection, privacy and contractor model.
- Future Eye / relevant domestic benchmark identity and business model; do not conflate a company with the EgoScale research project.
- Base + distributed collection trends.
- Data quality, provenance, privacy and relevant standards.
- Public positioning of 光轮、大晓机器人、原力灵机 only for tailoring, not as evidence of cooperation.

Expected: each slide-bound claim has URL, source title, publisher, publication date, access date, claim summary, and usage limit.

**Step 4: 完成事实门禁**

Review every candidate fact. Any claim without USER_CONFIRMED, VERIFIED_GROUP_FACT or EXTERNAL_EVIDENCE is removed from visible slide copy or explicitly marked as inference/roadmap.

### Task 3: 写出逐页内容与证据映射

**Files:**
- Modify: scratch/tmp/slide-content.txt
- Modify: scratch/tmp/evidence-ledger.txt

**Step 1: 为 16 页主 deck 写观众可见文案**

For each slide record:

- takeaway title;
- one-sentence narrative job;
- visible body copy;
- visual concept;
- evidence IDs;
- status label: CURRENT / CONFIGURABLE / ROADMAP;
- prohibited claims.

**Step 2: 写附录**

Add concise appendix slides for:

- benchmark lessons: EgoScale / Shift / Future Eye;
- operating SOP;
- data rights and privacy;
- source list;
- three customer-tailoring placeholders that state proposal hypotheses, not existing relationships.

**Step 3: 检查叙事连续性**

Verify this sequence:

    Industry tension -> core judgments -> production-network answer -> why Guoshu -> customer product -> delivery/Agent/quality -> business model -> flywheel -> roadmap -> POC action

Expected: each slide creates the question answered by the next slide; no agenda-only section pages and no generic “Thank you” ending.

**Step 4: 检查字数**

Expected visible copy budget:

- cover: <= 25 Chinese characters excluding subtitle;
- slide title: ideally <= 24 Chinese characters;
- body: generally <= 90 Chinese characters, excluding source footer;
- appendix may be denser but must keep body font >= 16pt.

### Task 4: 设计视觉系统与素材计划

**Files:**
- Modify: scratch/tmp/visual-plan.txt
- Create: scratch/tmp/assets/*

**Step 1: 固定视觉系统**

Use a custom from-scratch visual route:

- 16:9 widescreen.
- graphite black base, industrial orange, data cyan, warm off-white.
- cinematic real-work imagery, first-person capture, robot manipulation, data trails.
- no old-PPT chrome, no dense dashboard cards, no repeated four-card grids.
- at least 50pt deck title, 35pt slide title, 24pt subheads, 16pt body.

**Step 2: 规划每页视觉**

Use one dominant composition per slide. Reuse no image except background texture. Reserve native PowerPoint shapes for only three necessary diagrams:

- base + distributed production network;
- end-to-end responsibility chain;
- order-driven flywheel.

**Step 3: 获取或生成素材**

Use image search for factual corporate/product imagery only when provenance and usage are acceptable. Use imagegen for conceptual hero images and privacy-safe scene compositions. Do not use Python or programmatic vectors to create illustrations.

**Step 4: 核对素材**

For each asset record source or generation prompt, intended slide, crop, aspect ratio, and license/provenance note in source-notes.txt.

### Task 5: 初始化并实现 PPT

**Files:**
- Create: scratch/tmp/deck.mjs
- Create: scratch/tmp/guoshu-embodied-data-network.pptx
- Create: output/国曙具身数据生产网络_业务介绍_v1.pptx

**Step 1: 阅读 artifact-tool 文档**

Read completely:

- artifact_tool/API_QUICK_START.md
- artifact_tool/api/API_DOCS.md

**Step 2: 初始化 artifact-tool workspace**

Run:

    node "$env:PPT_SKILL_DIR/container_tools/setup_artifact_tool_workspace.mjs" --workspace "$env:PPT_TMP"

Expected: @oai/artifact-tool resolves from the scratch workspace.

**Step 3: 写构建脚本**

Use apply_patch to create scratch/tmp/deck.mjs. The script must:

- use plain JavaScript ES modules;
- build every slide from the approved content file;
- apply a single visual system with varied compositions;
- add small, readable source footers only on evidence-bearing slides;
- keep all external-image paths absolute;
- export to scratch/tmp/guoshu-embodied-data-network.pptx.

**Step 4: 运行构建**

Run:

    node "$env:PPT_TMP/deck.mjs"

Expected: PPTX is created with all main and appendix slides; no unresolved asset path or placeholder error.

**Step 5: 复制最终候选文件**

Run:

    Copy-Item -LiteralPath "$env:PPT_TMP/guoshu-embodied-data-network.pptx" -Destination 'C:/Users/chunx/Projects/nautilus-core/.worktrees/embodied-data-ppt-v2/output/国曙具身数据生产网络_业务介绍_v1.pptx' -Force

Expected: old PPT remains untouched; final candidate exists only at the new output path.

### Task 6: 结构与视觉 QA

**Files:**
- Modify: scratch/tmp/qa/qa-ledger.txt
- Modify: scratch/tmp/deck.mjs
- Modify: output/国曙具身数据生产网络_业务介绍_v1.pptx

**Step 1: 运行边界检查**

Run:

    python "$env:PPT_SKILL_DIR/container_tools/slides_test.py" 'C:/Users/chunx/Projects/nautilus-core/.worktrees/embodied-data-ppt-v2/output/国曙具身数据生产网络_业务介绍_v1.pptx'

Expected: no slide content outside canvas.

**Step 2: 渲染所有页面**

Run:

    python "$env:PPT_SKILL_DIR/container_tools/render_slides.py" 'C:/Users/chunx/Projects/nautilus-core/.worktrees/embodied-data-ppt-v2/output/国曙具身数据生产网络_业务介绍_v1.pptx'

Expected: one PNG per slide.

**Step 3: 生成全局预览**

Run:

    python "$env:PPT_SKILL_DIR/container_tools/create_montage.py" --input_dir '<rendered-slide-dir>' --output_file "$env:PPT_TMP/qa/contact-sheet.png"

Use the contact sheet only for pacing, consistency and density review.

**Step 4: 逐页查看**

Inspect every slide PNG at full size. Record pass/fail for:

- title wrapping;
- body overflow;
- unintended overlap;
- contrast and readability;
- image crop and resolution;
- source footer accuracy;
- CURRENT / CONFIGURABLE / ROADMAP wording;
- absence of unauthorized logos and implied partnerships.

**Step 5: 修复并重复 QA**

Patch deck.mjs, rebuild, copy, rerun slides_test, rerender and reinspect until every slide passes. Do not waive overlap or clipping warnings without visual confirmation.

### Task 7: 内容复核与交付

**Files:**
- Modify: scratch/tmp/evidence-ledger.txt
- Modify: scratch/tmp/qa/qa-ledger.txt
- Final: output/国曙具身数据生产网络_业务介绍_v1.pptx

**Step 1: 完成内容核验**

Check every market, technical, standard and company claim against the evidence ledger. Remove claims that cannot be traced to a primary source or user confirmation.

**Step 2: 检查商业一致性**

Confirm the deck states:

- no existing embodied-data order;
- Guoshu is the accountable contracting party;
- partner names are not disclosed;
- network and certification are roadmap items;
- first action is a paid, scoped POC.

**Step 3: 验证最终文件**

Run:

    Get-Item 'C:/Users/chunx/Projects/nautilus-core/.worktrees/embodied-data-ppt-v2/output/国曙具身数据生产网络_业务介绍_v1.pptx'
    git -C 'C:/Users/chunx/Projects/nautilus-core/.worktrees/embodied-data-ppt-v2' status --short -- 'docs/plans' 'output'

Expected: final PPTX is non-empty; only this task's plan/output files appear in scope.

**Step 4: 提交最终产物**

Run:

    git add -- 'docs/plans/2026-07-22-embodied-data-ppt-implementation.md' 'output/国曙具身数据生产网络_业务介绍_v1.pptx'
    git commit -m "docs: deliver embodied data pitch deck"

Expected: commit contains only the implementation plan and final PPTX.

**Step 5: 返回用户**

Provide a short summary of the deck, mention that old PPT content and current website were audited and external claims were verified, then include exactly one standalone Markdown link to the final PPTX.
