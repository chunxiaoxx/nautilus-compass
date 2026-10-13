---
name: orgfuel-ORGH-9dfb0453c618ee68-b97baadbc2
description: "commit f83ee8f86240 2026-05-21 ﻿feat(v1.7.1): gap fix 4 · ju"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-9dfb0453c618ee68
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit f83ee8f86240 2026-05-21
﻿feat(v1.7.1): gap fix 4 · judges/gemini_flash.py · opt-in Gemini Flash judge
NEW · nautilus_compass.judges subpackage (external LLM judges for benchmark/paper ONLY)

judges/__init__.py · CRITICAL CONSTRAINT docstring · "永远只 BGE local" rule preserved
judges/gemini_flash.py · ~135 LOC
  - is_enabled() · checks COMPASS_USE_GEMINI_FLASH env (default disabled)
  - GeminiFlashJudge class · lazy client init · vertexai project chunxiao-vm-260414
  - generate(prompt) · returns None if disabled (fail-soft)
  - judge(question, candidate, reference) · structured JSON eval prompt
  - Supports GOOGLE_APPLICATION_CREDENTIALS + COMPASS_GEMINI_SA_PATH env
  - service account already verified 5/20 · SDK google-genai 1.70.0 installed
  - PRESERVES daemon.py:12 "no LLM at inges
