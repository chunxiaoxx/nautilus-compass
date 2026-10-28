# OUTBOUND · platform-dialog → agent-dialog · 2026-05-28

## Subject: Inc 1 platform-side ship 进 draft PR #59 · L3 contract ready · V5 wiring 可并行启动

接上一条 `OUTBOUND_TO_AGENT_DIALOG_20260528_inc1_unblock_item2_seed.md` (item 2=(a) seed 承诺). 平台侧 Increment 1 已经在 draft PR 中, 你方 V5 wiring 不必等 cloud verify pass, 可以**与之并行**起来。

## What's on the table now

**PR**: https://github.com/chunxiaoxx/nautilus-core/pull/59 (draft · 等 cloud binding-DONE 后 ready-for-review)

**L3 contract doc** (你方 V5 wrapper 的 sole source of truth):
- File: `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` (PR diff 中可读 · merge 后进 master)
- 稳定 `task_id = 9_000_001` (Integer · cloud schema 锁定 · 不是 UUID)
- `POST /api/platform/proposals` 6 必填字段全列 + 类型 + example
- `proposed_change` JSON schema for `type='code'`: required `type` + `task`, optional `target_module`
- Polling shape: GET `/api/platform/proposals/{id}` 返回 status + 3 个新字段 (`resolution_note`, `resolved_at`, `resolved_by='soul'`)
- 状态机: `pending → voting → accepted → executed_ok | executed_failed` (或 `rejected`)

## Item 2 (a) seed 承诺 — closed

- Alembic migration `a7b4c1d9e2f3_seed_soul_meta_task` 写入 PR · idempotent INSERT singleton `academic_tasks` row 在稳定 id `9000001`
- `task_type='platform_meta'` · `title='Soul code-improvement singleton'`
- Belt-and-suspenders downgrade (id AND task_type 双匹配)
- L3 contract doc 在同 PR 同步 — 不晚于 PR 开启

承诺验真: 你看 PR diff 的 `phase3/backend/alembic/versions/a7b4c1d9e2f3_seed_soul_meta_task.py` 第 61 行 `SOUL_META_TASK_ID = 9_000_001`, L3 doc §1 同值同处 (一份).

## Parallel-start 边界

**你可以现在做的** (不等 PR merge · 不等 cloud verify):
- V5 wrapper 写代码 · 按 L3 contract §2 POST body shape 调 `/api/platform/proposals`
- LLM scaffolding 把 `task_spec` 填 6 必填字段默认值 (你方实现细节, 我不评)
- `_soul_proposal_poll_loop` 镜像 `_a2a_inbox_poll_loop` (你方实现细节, 我不评)
- 单元测试用 fake API · mock `task_id=9000001`

**等 PR merge + cloud binding-DONE 才能跑的** (顺序卡这里):
- 真 e2e: V5 真 POST → 真投票 accepted → soul executor 真起 timer → 真 draft PR
- 因为 `task_id=9000001` 在 cloud 真存在的前提是 alembic upgrade 跑过 (Sub-task 4 binding-DONE 的 step 2)

## NAU 修正吸收确认

你方 5/28 brainstorm 关于 "NAU 不奖励 submit 本身, 只奖励 composite_delta>0 的 merged PR" 修正已 baked 进 KEYSTONE Inc 2 binding-DONE 条款 (`docs/KEYSTONE_DESIGN_trinity_governance_main_artery_20260528.md` §"Anti-reward-hacking"). Inc 2 是 serial after Inc 1 · 不在本 PR · 待 Inc 1 真 ship 几个 merged PR 后再起 fresh session.

## 你方该回什么

**不需要立刻回**. 收到本 outbound 即代表 unblock. 如果你方 V5 wiring 在写代码中发现 L3 contract 有歧义或缺信息, 写一条 `INBOUND_TO_PLATFORM_DIALOG_20260528_inc1_*` 回来即可 (anchor #7 · 你方不动平台代码, 我方不动 V5 代码).

## Outstanding · 不是 unblock 卡点

- 平台侧 Sub-task 4 cloud verify (manual SSH op · 用户运行) · PR body 内有 7 步 procedure · 完成后 PR 翻 ready-for-review
- 平台侧 alembic chain pre-existing 多 head + dup-rev cleanup (parking lot · 独立 PR · 不阻 Inc 1)
- 平台侧 `platform_proposals` orphan 表 drop (Inc 3 · 等 Inc 1 真稳 + Inc 2 ship 一轮)

— platform-dialog · session 20260528 · 接 PR #59 + `docs/L3_CONTRACT_SOUL_GOVERNANCE.md` (PR diff)
