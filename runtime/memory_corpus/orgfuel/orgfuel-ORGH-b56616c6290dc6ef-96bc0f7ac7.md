---
name: orgfuel-ORGH-b56616c6290dc6ef-96bc0f7ac7
description: "commit f871c4b0be31 2026-04-27 feat: zenmind-mem v0.5 · init"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b56616c6290dc6ef
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f871c4b0be31 2026-04-27
feat: zenmind-mem v0.5 · initial release
Memory plugin for Claude Code · 基于 V5 nautilus 治理实战
+ 借鉴 zenmind.chat 禅心 AI 长期记忆栈

核心能力:
  · UserPromptSubmit hook · metadata + age 警告 + strategy 命中 (0.5s)
  · CLI BGE daemon · 真语义召回 + Persona drift detection (1.8s warm)
  · Stop hook · 自动 strategy 蒸馏 + Ebbinghaus decay
  · A-MEM cross-cosine · supersede 检测
  · Persona Vectors L3 · 25+25 锚点 · 反锚点 alert
  · DPT-Agent strategy lookup · 推理路径注入
  · API embedder option · gemini-embedding 250ms

蓝图源:
  · NAUTILUS_V5_ARCHITECTURE_FINAL.md (line 483/489/498/501/504)
  · zenmind.chat soulcore (用户原创架构)
  · 4-14 宪法第 3 条 AI 员工产品衍生品

测试覆盖:
  · selftest 9/10 · deeptest 18/19
