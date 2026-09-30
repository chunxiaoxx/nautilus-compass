Hi mem0 team — we recently ran a controlled experiment that involved mem0 2.2.0, and we think the results are useful to you (plus a concrete offer at the end).

**What we did (already public, full artifacts)**

We built a 30-question exam that tests whether AI agents can recall their own operational history, and ran a controlled three-arm experiment — same backbone model, same questions, only the memory path changed:

- Direct access to structured logs: **16/18**
- Through mem0 (default config, write-time semantic compression ON): **11/18**
- Through mem0 (write-time compression disabled, the *only* variable changed): **18/18**

One config flag = 7 points. The failure anatomy: write-time compression rewrites structured logs into prose and drops the exact machine-checkable fields (e.g. `artifact: null`) that audit-style recall needs. Full artifacts, failure samples, and the config diff are public here:
https://github.com/chunxiaoxx/nautilus-compass/blob/main/docs/benchmarks/BC1_LAUNCH.md

Our one suggestion for the docs: for compliance/forensics/audit use cases, recommending `infer=False`-style no-compression writes (or a preset) would save users a real footgun. Happy to open a small docs PR if you'd take one.

**The DolphinBench question**

Your September 22 blog post (mem0 vs OpenAI Memory / LangMem / MemGPT on DolphinBench) quotes comparative scores. We couldn't find the DolphinBench grader protocol / dataset / per-item outputs published — is the evaluation pipeline public anywhere? If it is, just point us at it.

**The offer**

We run a small independent verification lab (Assay). Our one job: making benchmark numbers *reproducible* — pre-registered criteria, full request/artifact archiving, third-party recompute, public errata with a 90-day challenge window. We applied it to ourselves first (our own grader failed 7/18 items; we published the errors).

We're offering a free, no-strings independent recompute run of the DolphinBench public results:

- You (optionally) share criteria + run config; frozen once shared
- We rerun independently and publish: criteria, full artifacts, pass/fail per claim, every failure sample verbatim
- Co-attributed report (your benchmark + our recompute); you keep full errata rights via the challenge window
- If anything doesn't reproduce, you get the failure data before anyone else — that's the whole point

We made the same offer to the MemTensor/MemOS team for OmniMemEval (issue #2440 there). No strings: if you're not interested, the 3-arm data above is yours to use regardless.

— Assay (independent verification for AI claims) · github.com/chunxiaoxx/nautilus-compass
