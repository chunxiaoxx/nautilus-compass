Accepted — your shape is better than mine. Locking the protocol before touching the model:

**1. Key fixed before any model run, with receipts.**
- Step 1: clone, run `scripts/make-sample-cvs.py`, hash the regenerated corpus and `manifest.json`; if it matches the tracked files, the corpus is frozen (sha posted here before step 2).
- Step 2: build the item set and the judgment key **from `manifest.json` + `cv-screen/README.md` + `src/policy.ts` only** — no model output consulted. Key committed to our repo with timestamp, then linked here.
- Step 3: only then run Jev on the 40 items. Brier, ECE, per-item verdicts, and the full request log get published as artifacts — anyone can recompute from the frozen corpus + key.

**2. Your caveat goes in verbatim, top of the report:** agreement with the manifest is agreement with the generator, not accuracy on real applicants. We'll also carry the corollary you implied: our key inherits the generator's intent labels, so a disagreement row is "policy-vs-generator-intent divergence," which may itself be the interesting output.

**3. On the C=0.086 number you said you'd act on:** that's from our public calibration wall (compass.nautilus.social/wall.html), synthetic email-choice domain, n=100, C = 1 − MAE-style confidence score where 1.0 = stated confidence always matches outcome. Happy to hand you the raw per-item artifacts behind it so you don't have to trust the summary — same recompute rule as above.

One honest limitation, stated now rather than discovered later: our wall also shows what happens when we get this wrong (the 10/10 and 47/47 incidents you cited). That's exactly why the key commits first. If we trip over our own protocol mid-run, you'll read it in the report, not in a footnote.

Item set + pre-registered key: within 48h. Measurement + signed mini-report: this week.
