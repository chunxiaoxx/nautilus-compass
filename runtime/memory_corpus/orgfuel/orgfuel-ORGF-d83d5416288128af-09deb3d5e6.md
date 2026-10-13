---
name: orgfuel-ORGF-d83d5416288128af-09deb3d5e6
description: "flywheel 档案 2026-08-12-dreamdojo-m2a-v1-1-implementation-pla"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-d83d5416288128af
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-08-12-dreamdojo-m2a-v1-1-implementation-plan.md
# DreamDojo M2A v1.1 Correction Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close the M2A evidence-authority, action-space, experimental-profile, and trust-boundary gaps before resuming raw-byte replay and golden-vector completion.

**Architecture:** Keep the existing four M2 contract documents and the offline-only adapter, but insert explicit evidence objects where v1 used assertions. A byte-pinned M1 loader becomes the only formal M1 entry, a strict action-space document is required before `ready_for_authorized_runtime`, run requests use smoke/pilot/evidence profiles, and run receipts remain untrusted until a future external verifi
