Per the boundary we agreed in #1 (self-reported claims earn no AGG credit without an independent, goal-specific verifier), here is the improvement ticket we committed to. The theme is the biggest problem we see with RSI loops: **signal decay** — apparent gains across loops shrink once you account for recoverable losses.

## Case (our own, adversarial as always)

We just finished a dual-harness evaluation: same model (MiniMax-M3), two harnesses (our in-house harness vs mini-swe-agent 2.4.6), n=30 stratified sample of SWE-bench Verified, independently judged on a separate machine. Results, all artifacts sha16-anchored:

- Apparent gap: **+10.0pp** resolved (8/30 vs 5/30).
- But format-layer errors consumed 15/30 (arm A) and 11/30 (arm B) of all runs — malformed patch hunks, a collector `.strip()` corrupting patch tails (fixed since, with tests), out-of-repo files entering diffs.
- **Effective orchestration signal < apparent signal.** A chunk of the measured gap is recoverable by mechanical fixes, not capability.

## Proposal: margin-gain gate

For each improvement loop, report **effective gain = resolved gain − gain recoverable by mechanical fixes** (format/env layer), classified by an independent verifier before any AGG credit:

1. Classify every failed run: capability-fail vs recoverable-fail (format, environment, infra).
2. Publish both numbers (apparent + effective) with the classification rubric.
3. Gate: a loop's credited gain is the effective one.

The classification is cheap and fully machine-checkable — our rubric and a 25-case regression set (the format-error instances from the run above, with preds + judge reports) can be contributed as the first public example.

## Question

Would this fit the certification track (PR #2 replay protocol)? If yes, we can open the rubric + regression set as a follow-up PR.

---

*Disclosure: drafted with AI assistance by an independent verification org (compass / nautilus-compass). All numbers above are reproducible from the linked artifacts; negative results included by design.*
