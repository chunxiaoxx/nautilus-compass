---
name: orgfuel-OUTR-rsibench_signal_decay_ti-1-63ed219a5c
description: "## Case (our own, adversarial as always)  We just finished a"
metadata:
  type: reference
  source: org_fuel:outreach
  pf_id: OUTR-rsibench_signal_decay_ti-1
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

## Case (our own, adversarial as always)

We just finished a dual-harness evaluation: same model (MiniMax-M3), two harnesses (our in-house harness vs mini-swe-agent 2.4.6), n=30 stratified sample of SWE-bench Verified, independently judged on a separate machine. Results, all artifacts sha16-anchored:

- Apparent gap: **+10.0pp** resolved (8/30 vs 5/30).
- But format-layer errors consumed 15/30 (arm A) and 11/30 (arm B) of all runs — malformed patch hunks, a collector `.strip()` corrupting patch tails (fixed since, with tests), out-of-repo files entering diffs.
- **Effective orchestration signal < apparent signal.** A chunk of the measured gap is recoverable by mechanical fixes, not capability.
