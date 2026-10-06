# rsi-bench Issue #4 跟评稿(备发:10/12 榜页上线后;勿提前发——URL 与读数依赖)

> 发布条件:①nautilus.social 榜页 200 可达 ②Round 1 读数已挂 ③距 Issue#4 开题 ≥48h(已满足)。发布方式:gh api repos/sunghunkwag/rsi-bench/issues/4/comments -f body=@本文件。

---

Update from our side — the leaderboard this proposal came from is now live:

**L3 Harness Leaderboard Round 1**: [URL:nautilus.social 榜页] — same-model dual-harness comparison (MiniMax-M3 via two harnesses, n=30 stratified SWE-bench Verified, independently judged): **26.7% vs 16.7% (+10.0pp apparent)**, with the full margin-decomposition you'd expect from #4: format-layer errors (15+11 across arms, malformed hunks & collector corruption — since fixed upstream with tests) mean *effective* orchestration signal is materially lower than apparent. All artifacts sha16-anchored; recompute commands public.

Also now open:

1. **Free intake for independent judging** (the L1 slot mechanism from this thread): [URL:intake 页] — submit repo@commit, pre-registered criteria, verdict in ≤5 working days, negative results included by design.
2. **signal-decay-bench v0 sample pack** (two tracks: effective-gain classification + judge fidelity, built entirely from the sha-anchored artifacts above) — same link, benchmarks section.

We note with interest that several harness teams (OpenHands, Cline, LobsterAI among others) are already in triage on L1 inclusion invites — the effective-gain gate in this issue would apply to every one of those runs.

Our commitment stands: classification rubric + the 25-case format-regression set as a follow-up PR here once the first external run goes through the gate.

*Disclosure: independent verification org (compass/nautilus-compass); AI-assisted drafting; all numbers reproducible from linked artifacts.*
