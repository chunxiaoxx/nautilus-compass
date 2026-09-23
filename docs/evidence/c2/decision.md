# Compass C2 formal causal A/B decision

Observed on 2026-08-05 from a frozen, deidentified task pack with two fixed live providers.

## Evidence result

- 80 pairs were scheduled; 73 complete paired episodes were admitted and 7 incomplete pairs were isolated.
- Overall flat success was 0.137 and governed success was 0.836, for a paired delta of +0.699.
- The stratified bootstrap 95% interval was [+0.589, +0.808].
- Both providers covered all four query classes. The smallest provider/query cell contained 5 valid pairs.
- The protected class delta was 0 for both providers.
- Poison admissions and replay failures were both 0.
- Replay rebuilt every outcome from signed flat/governed episode evidence, verified the signed run receipt, and exactly regenerated the stored summary.
- Known provider cost was USD 0.977008. The other provider did not return price data for 80 arms, so a complete total cost is not claimed.

## Decision

All internal C2 promotion-recommendation gates passed, so `promote_recommended=true` is supported by this run. This is not an automatic runtime promotion: runtime remains flat, the evidence remains candidate-only, and `improvement_claim=false` remains binding.

The next admissible step is a separately reviewed Super Agent signed-input adapter and then external baseline/SOTA evaluation. This commit does not merge, deploy, modify model weights, or enable a production routing policy.

Only aggregate metrics and cryptographic hashes are committed. Raw responses, episode bundles, checkpoints, credentials, and private signing material remain outside Git.
