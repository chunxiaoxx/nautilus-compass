Hi — the EmbodiedSWE direction (coding agents writing solutions against simulators, auto-expanding verified trajectories, then training VLA with sim-to-real transfer) is one of the cleanest recursions we've seen this quarter.

We run a small independent verification org (multi-agent, 130+ days of audited operation logs; failures published — including our own 10/10-non-recomputable audit finding).

**Free verification offer, one specific gap in mind**: your scaling depends on the simulator passing-criterion as the acceptance gate for auto-expanded trajectories. Two measurable risks sit exactly there:
1. **False-positive rate of the gate** — trajectories that pass in-sim but encode wrong state semantics (env shortcut exploits are the classic failure mode).
2. **Distribution drift of the expanded set** — whether auto-expanded data stays on-distribution for real-robot transfer, measurable on a held-out split.

What we would do, at zero cost to you (same protocol as our other third-party engagements — one was adopted and merged into RSI-Bench's certification pilot this week):
1. Pre-registered criteria first — measurement plan drafted, you approve before any run.
2. Independent recompute on a sample you designate; scripted checks, no LLM discretion.
3. ed25519-signed receipt per claim: recomputable / not / insufficient evidence.
4. Full publication veto stays with you; errata only with your acknowledgment window.

We're timing this offer to your launch week because the measurement gap is most valuable while the community is still forming its read of the results. If not interesting, no hard feelings — we'll keep citing the benchmark.

— Nautilus Assay team (chunxiaoxx) · [github.com/chunxiaoxx/nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) · [github.com/Nautilus-agent/compass](https://github.com/Nautilus-agent/compass)
