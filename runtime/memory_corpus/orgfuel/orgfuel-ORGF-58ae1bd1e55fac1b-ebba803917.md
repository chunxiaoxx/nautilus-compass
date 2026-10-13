---
name: orgfuel-ORGF-58ae1bd1e55fac1b-ebba803917
description: "flywheel 档案 2026-08-11-dreamdojo-m2a-adapter-implementation-"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-58ae1bd1e55fac1b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-08-11-dreamdojo-m2a-adapter-implementation-plan.md
# DreamDojo M2A Adapter Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an offline, independently replayable DreamDojo M2A preflight adapter that proves whether frozen control/treatment evidence is eligible for an authorized world-model evaluation without downloading weights, running inference, or widening data rights.

**Architecture:** Extend the existing strict JSON contract registry with four M2 contract versions, then layer DreamDojo-specific cross-document policy in `m2_contracts.py`. `m2_preflight.py` converts the frozen M1 evidence into a path-free preflight request, produces a deterministic `inference_not_run` receipt, 
