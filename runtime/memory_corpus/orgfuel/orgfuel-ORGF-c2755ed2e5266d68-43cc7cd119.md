---
name: orgfuel-ORGF-c2755ed2e5266d68-43cc7cd119
description: "flywheel 档案 2026-08-11-ego-datalift-m1-synthetic-implementat"
metadata:
  type: reference
  source: org_fuel:flywheel
  pf_id: ORGF-c2755ed2e5266d68
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

flywheel 档案 2026-08-11-ego-datalift-m1-synthetic-implementation-plan.md
# Ego DataLift M1 Synthetic Demo Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 用项目自生成的第一人称操作微数据完成同源 control/treatment 严格 A/B，在冻结条件下输出
可重复的动作片段识别、时间边界定位和 `candidate_gain`/`no_gain`/`invalid_run` 审计报告。

**Architecture:** Flywheel 以纯 NumPy 生成 RGB episode，并在受控输出目录保存逐帧数据；control 与
treatment 只改变训练标签，共享数据、切分、特征、线性 probe 和评测真值。Runner 先通过 M0
source/experiment bundle 门，再运行两臂、计算指标、重放第二次并比较规范化报告哈希；Git 只接收
代码、Schema、测试、聚合指标、哈希和脱敏证据。

**Tech Stack:** Python 3.11+、NumPy 2.4.x、pytest、jsonschema、标准库 JSON/hashlib/pathlib；CPU-only，
无 FFmpeg、GPU、网络、数据库、外部 API、真实数据或外部系统调用。

---

## 冻结配置

以下值在正式 M1 结果产生前冻结，不根据 test 表现修改：

```python
M1_SEED = 20260811
