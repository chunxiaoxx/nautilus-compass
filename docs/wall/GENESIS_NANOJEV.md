# Genesis Receipt #2 · NanoJev recorded results · 2026-09-20

**Subject**: NanoJev (TianyuCodings) — nano replica of Jev (TypeSafe), 0.6B parallel
decision model. Claims under test (README tables): maze 50×50 three-system comparison
(NanoJev 244/36/goal vs Jev 2738/1044 vs Untuned Qwen 4726/2044) and snake 12×12
(NanoJev 27 food/256/alive vs Jev 30 vs Qwen 25/211/trapped).

**Verdict: agree** — at evidence-integrity + claim-results consistency level.

## Checks (all from public bytes)

1. **Manifest integrity**: side_by_side_data_manifest builder/output/cohort hashes —
   3/3 PASS (note: verifier's first probe FAILED all hashes due to git CRLF conversion
   on Windows; re-clone with `core.autocrlf=false` → all PASS. Probe falsified first,
   as discipline requires.)
2. **Source manifest**: SOURCE_MANIFEST.json per-file sha256 — random sample 10/10 PASS.
3. **Claim ↔ results consistency**: all six README numbers (attempts/collisions/food/
   steps/outcome, 3 systems × 2 games) exactly match `web/side_by_side_results.json`
   recorded summaries. Zero discrepancy.

## Boundary (honest scope)

This verifies (a) the published evidence is internally consistent and byte-intact, and
(b) the claim tables faithfully reflect the recorded runs. It does NOT replay episodes
with the model weights (available on HF; suitable for a deeper-tier receipt later).
Initial-state hashes and full controller rules are published, making that deeper
recompute unusually feasible.

## Note

NanoJev ships per-file sha256 manifests, provenance categories, frozen cohorts, and
explicit controller rules — the best public evidence hygiene we have audited to date
(better than most AI labs). Verification of honest work is a gift.

---
Protocol: Assay Protocol v0 · Verifier: 伊洛科技有限公司 (Nautilus Assay) · SDK assay-verify 0.1.0
Liability: docs/wall/ASSAY_LIABILITY.md (challenge window 90d)
