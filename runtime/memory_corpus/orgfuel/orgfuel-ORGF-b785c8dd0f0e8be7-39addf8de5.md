---
name: orgfuel-ORGF-b785c8dd0f0e8be7-39addf8de5
description: "flywheel 档案 2026-08-10-nautilus-flywheel-identity-migration."
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-b785c8dd0f0e8be7
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-08-10-nautilus-flywheel-identity-migration.md
# Nautilus Flywheel Identity Migration Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将已提交的智涌飞轮身份从旧本地目录迁移到 `nautilusflywheel`，并发布为同名私有 GitHub 仓库。

**Architecture:** 先提交品牌决定和迁移计划，再以精确绝对路径移动整个独立 Git 工作树，
确保提交、分支和 `.git` 元数据保持不变。随后使用 GitHub CLI 创建唯一的私有远端、添加
`origin`、推送 `main`，最后通过 GitHub 与 Git 两侧读回核验名称、可见性、默认分支和 SHA。

**Tech Stack:** Git for Windows、GitHub CLI (`gh`)、GitHub SSH/HTTPS 凭据；不涉及应用运行时、
数据库、对象存储、设备、采集数据或外部业务系统。

---

### Task 1: 提交迁移计划

**Files:**

- Create: `docs/plans/2026-08-10-nautilus-flywheel-identity-migration.md`
- Test: Markdown header and Git diff integrity checks.

**Step 1: 验证计划标题、目标路径和 GitHub 目标**

Run:

```powershell

