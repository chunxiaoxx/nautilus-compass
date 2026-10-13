---
name: orgfuel-ORGH-5e9ca956a6a837a8-ae8b9ff5ef
description: "commit 906e38692456 2026-05-10 docs: black-box framing refra"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-5e9ca956a6a837a8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 906e38692456 2026-05-10
docs: black-box framing reframe + cost/local caveats
After product audit + 6/6 verification of public memory layers
(Mem0/Letta/Cognee/Zep/MemOS/smrti all white-box), reframe compass as
"the only public OSS memory layer that does not call an LLM at index
time to extract facts or build a graph."

- paper/BLACKBOX_VS_WHITEBOX.md: new short post · 6 verifications +
  causal chain + trade-off (-30pt LongMemEval is architectural ceiling
  not tuning gap) + who-it-is-for · ~1700 words · single source of
  truth for this framing across PH/dev.to/HN
- paper/sections/00_abstract.tex (paper 1): inject zero-extraction
  framing + LongMemEval architectural ceiling caveat (1915/1920 chars)
- paper/sections/paper2_00_abstract.tex (paper 2): same framing +
  softened "tying
