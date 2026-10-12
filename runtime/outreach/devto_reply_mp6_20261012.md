Several of your points match our observations directly:

**LoRA drowned out by quantization noise** — consistent with what we saw. We merge before quantizing (to match production serving), and the residual drift concentrates on small-magnitude adapter deltas — exactly the weights most sensitive to rounding at 1.7B scale, where each parameter carries more decision load than at 7B+.

**Class collapse** — our flips weren't uniform collapse but boundary-concentrated: near-pass cases flipping to fail. In a judge, that location matters more than the rate, since those are precisely the flips that corrupt downstream training loops. The preregistered gate (≥99% agreement) caught it either way.

**Edge-case calibration** — agreed, random-sample calibration is how we got boundary-blind int8. Our fix path is production-adjacent calibration cases (boundary-dense, not distribution-representative).

**Dynamic per-token quantization**: not tried yet — the latency overhead is hard to justify for a judge called at eval time, but for batch scoring it's worth a run. On the r16 adapter: a rank sweep (r32/64) pre-quantization is going into our next experiment round to separate adapter capacity from rounding effects.

Per-case matrix and gate are public if you want the numbers: nautilus.social/criteria.
