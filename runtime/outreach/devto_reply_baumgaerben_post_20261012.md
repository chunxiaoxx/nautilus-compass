Posting this reply now (apologies for the delay — it slipped through our queue during launch week).

This is a technically substantive review, and your four points map closely to what we saw.

**On calibration data**: agreed, and this matches our failure mode precisely. Our int8 flips clustered exactly at the decision boundary (near-pass cases flipping to fail), which is consistent with activation range mis-estimation on sparse regions. Our fix path (more production-adjacent calibration cases) follows your point.

**On per-channel scaling**: correct — our int8 path uses bitsandbytes LLM.int8, which already does vector-wise absmax scaling, and our int4 path is nf4 with per-block quantization constants. So the asymmetric/per-channel mechanism you describe is largely in place; the residual drift is likely from the low-rank adapter weights being quantized together with the base (we merge before quantizing to match production serving) — small-magnitude LoRA deltas are exactly the weights most sensitive to that rounding.

**On your rank suggestion (r32-64)**: worth testing. Our r16 setup at 88.5% accuracy may be leaving headroom, and a rank sweep pre-quantization would separate "adapter capacity" from "quantization rounding" effects. We'll add this to the r88 experiment design with credit.

**On KV cache**: we serve with fp16 KV cache (no quantization), so this specific failure mode doesn't apply to our current numbers — but it's the right question for anyone reproducing at scale.

One addition from our side that complements your framework: the largest degradation wasn't uniform — it concentrated on boundary cases (near-pass/fail), which is precisely where judge flips corrupt downstream training loops. So the metric that matters isn't average agreement but **flip location relative to decision boundaries**. Your point 1 and this observation are two faces of the same issue.

The preregistered gate and per-case matrix are public (nautilus.social/criteria, GitHub artifacts) if you want to dig further. Genuinely appreciate the depth of this review.
