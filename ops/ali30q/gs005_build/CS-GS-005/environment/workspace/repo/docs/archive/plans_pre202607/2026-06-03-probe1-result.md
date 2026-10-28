# Probe 1 result — arm 1 (mono) vs arm 3 (decomp), first paired datapoint

> 2026-06-03 · Phase 4 · natural-budget regime, N=5, 1 seed. Honest verdict below.

## Setup

- Arms: **arm 1** = mono/generic (stock mini-swe-agent), **arm 3** = decomp/generic
  (localize→edit→test, isolated per-stage context, same bash tool) — only context
  partitioning differs (design §2).
- Model: MiniMax-M3 (litellm route A). Each arm wrapped in its own `BudgetedModel`.
- **Budget regime: natural** (cap 5M ≫ arm1's measured natural max 809k → neither arm
  crippled). Cap calibration: arm1 natural usage on the 5 instances = 128k–809k tokens
  (this is why the earlier 600k smoke cap crippled flask-4045, which needs 808k).
  A strict matched-*binding* cap (e.g. ~250k that forces both to the same ceiling) is
  the headline confound-control follow-up; this run is the natural-budget figure
  (design §4 reports both).
- Instances (5, light-repo, ≥2-hunk core subset): pallets__flask-4045 / 4992 / 5063,
  psf__requests-2148 / 2317.
- Scoring: official `swebench` harness in the container-eval path.

## Verdict (aggregate_paired_multiseed)

```
seeds=1  N(paired)=5
arm1 (mono)   pass@1: 20.0%   (1/5 resolved)
arm3 (decomp) pass@1: 60.0%   (3/5 resolved)
arm3 net (3-1): +40.0%        (the single seed is positive)
item-level arm3/arm1 wins: 3/1  (discordant=4, sign-test p=0.6250)
ESCAPES NOISE: False
```

arm1 resolved: flask-4045. arm3 resolved: 3 of the 5 (per `probe1_arm3_result.json`).

## Honest interpretation (conservative gate held)

- **Suggestive, NOT confirmed.** arm 3 (context-isolation) is +40pp raw (3/5 vs 1/5).
  That is a *much* larger raw effect than Phase 3's persona moat (+1.83pp, plainly
  noise) — an encouraging hint that decomposed clean context may genuinely help.
- **But it does not escape noise.** With N=5 / 1 seed there are only 4 discordant
  pairs; a 3–1 split has sign-test p=0.625, far from <0.05. The conservative gate
  (mean>0 AND every seed positive AND sign p<0.05) fails on the sign-test. So +40pp at
  this N is **statistically indistinguishable from chance** — we do NOT claim a signal.
- This is the design working as intended: a real, large-looking hint, correctly held
  below the "confirmed" bar until it survives more data.

## Next step (gated)

The +40pp hint is large enough to justify scaling — the design §6 "expand only if
Probe 1 shows signal" branch. Scale-up to get statistical power:
1. **Larger N** (toward the full 110 subset) and **2–3 seeds** (temp>0 reruns) so the
   paired sign-test has enough discordant pairs to reach p<0.05 if the effect is real.
2. Re-run the verdict; only `escapes_noise: True` (replicated across seeds, ideally
   across M3 + DeepSeek) counts as confirming the Paradigm-B context-isolation claim.
3. Add the strict matched-*binding* budget figure alongside the natural-budget figure.

**Do not** wire this into soul-fitness yet (the benchmark-as-soul-fitness design is
gated on the ruler showing a real, escape-noise signal — this is a hint, not that).

## N=15 update (2026-06-04, /loop scale-up) — the hint did NOT survive

Added 10 harder instances (3 astropy + 2 pylint + 5 pytest) at the same natural cap;
re-ran the paired verdict on N=15:

```
N(paired)=15  seeds=1
arm1 (mono)   pass@1: 33.3%  (5/15)
arm3 (decomp) pass@1: 33.3%  (5/15)
arm3 net (3-1): +0.0%   item-level arm3/arm1 wins 3/3 (6 discordant, sign p=1.0)
ESCAPES NOISE: False
```

**Verdict: NEGATIVE — Paradigm B (decomp / context-isolation) shows NO advantage.**
- The N=5 +40pp hint **regressed to a dead tie** at N=15 (both 5/15). The early hint
  was noise — exactly as the conservative gate flagged at N=5 (escapes_noise=False).
  The discipline of not over-claiming the +40pp paid off; it evaporated.
- Item-level is perfectly symmetric (3 arm3-wins, 3 arm1-wins) — no directional signal.
- **Compute confound makes it worse than a tie for decomp:** arm3 burned **3.9M–5M
  tokens** per instance (3-stage decomp) vs arm1's natural **128k–809k** — i.e. **3–5×
  more compute for the SAME resolve rate.** One arm3 instance (pytest-5103) hit the 5M
  cap and produced an empty patch. Under a strict matched-*binding* budget (cap both at
  ~800k), arm3 would do **worse**, not better. So at equal resolve rate, decomp is
  strictly less efficient.
- arm1 had 4 empty patches vs arm3's 1 (decomp completes more often) — but the extra
  completeness did NOT convert to more resolves.

**Consistent with Phase 3** (persona-moat also negative): the multi-agent structural
advantage keeps failing to materialize under honest, scaled measurement.

**What this means strategically (not a failure of the apparatus):**
- The **ruler works** — it caught a real-looking N=5 false hint and settled to a clean,
  honest tie at N=15. A stable, discriminating, non-over-claiming external measure is
  exactly what the soul-fitness design needs; the ruler is validated even though this
  hypothesis lost.
- For V5's economic-darwin P4 (outbound #17): **the data says do NOT lean on multi-agent
  decomposition/voting as fitness** — it doesn't beat single-agent here and costs 3–5×.
  Lean on the automated validation gate (resolve-rate), single-agent. Sharpens the #17
  red-line.
- benchmark-as-soul-fitness direction is intact: the fitness (external resolve-rate) is
  the right signal; this particular multi-agent *variation* just isn't the win.

N=15 artifacts: `probe1_n15_arm1_result.json` / `probe1_n15_arm3_result.json`.

## Artifacts

- `probe1_arm1_result.json` / `probe1_arm3_result.json` (official harness reports).
- `probe1_runner.py` (arms), `probe1_verdict.py` (this verdict), `decomp_solver.py`
  (arm 3), `budget.py` (matched budget), `escape_noise_stats.py` (the gate).
