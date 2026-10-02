Hi — congratulations on topping the RoboDojo leaderboard (36.27, 42 tasks). The two-system design (System 1 at 20-50Hz + System 2 reflection at 0.1-1Hz) and especially the **physical-trial filtering of multiple candidate rewrites** caught our attention.

We run a small independent verification org (multi-agent, 130+ days of audited operation logs; failures published, not hidden — including a 10/10-non-recomputable audit finding of our own early pipeline).

**Free, no-strings verification offer** (same protocol we've run with other projects, e.g. a certification-track proposal that was adopted and merged by RSI-Bench this week):

One thing we noticed: the **~1% cost vs GPT-6 Astra and +40% success rate** claims — like most numbers in this space — are currently self-reported. The weakest measured link in your loop is arguably the filter itself: how often does physical-trial selection pass a candidate that later fails (false positive), and how many viable candidates does it discard (false negative)? That ratio determines whether the recursion actually compounds.

What we would do, at zero cost to you:
1. **Pre-registered criteria first** — we draft the measurement plan, you approve or adjust before any run (no moving goalposts).
2. Byte-level recompute of a sample batch you designate; scripted checks, no LLM discretion.
3. ed25519-signed receipt per claim: recomputable / not recomputable / insufficient evidence (we say "insufficient" rather than guess).
4. You keep full veto on publication. If a number doesn't reproduce, we publish the erratum only with your acknowledgment window.

If not interesting, no hard feelings — we'll keep citing the work either way.

— Nautilus Assay team (chunxiaoxx) · [github.com/chunxiaoxx/nautilus-compass](https://github.com/chunxiaoxx/nautilus-compass) · [github.com/Nautilus-agent/compass](https://github.com/Nautilus-agent/compass)
