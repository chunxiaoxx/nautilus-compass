# Optical Bench Alignment · Lens Pair Aberration Minimization

## Objective

Optimize the placement of **two thin lenses** along an optical bench so that rays emitted by a point source converge on the target focal plane with minimum RMS spot radius. The candidate edits `baseline/init.py` which exposes `align_lens_pair(...)` returning axial/horizontal offsets; the verifier runs an honest geometric ray tracer and reports the achieved RMS.

## Domain Problem (real-history anchor)

**grounded in: `feedback_anchor_optical_bench_spot_rms`** — classical two-lens conjugate geometry problem. Baseline solution independently places each lens at the paraxial focal distance and assumes thin-lens formula `1/v = 1/f − 1/u` is exact on-axis. With **off-axis** rays entering at non-zero height, spherical + coma aberration makes the paraxial position a strictly sub-optimal solution: a real ray-trace through both lenses exposes ~3% RMS drift vs the paraxial baseline, which leaves 30-60 score points on the floor for any double-Gaussian bench.

Real-world relevance: optical bench alignment of camera objectives, telescope doublets, microscope tube lenses, and laser relay systems. Off-axis correction matters in wide-aperture freeform optics.

## Contract (do NOT change)

`align_lens_pair(source, lens_a, lens_b, target_z, n_rays=64) -> dict`
- `source`: dict `{z: float, dy: float, dz: float}` — point source position relative to bench origin
- `lens_a`: dict `{f: float, aperture_radius: float}` — focal length + radius of lens A
- `lens_b`: dict `{f: float, aperture_radius: float}` — focal length + radius of lens B
- `target_z`: float — target focal plane axial position
- returns `{"z_a": float, "z_b": float, "x_a": float, "x_b": float, "y_a": float, "y_b": float}` — 6 degrees of freedom (axial z + lateral x/y for each lens)
- the candidate **MUST** keep `z_b > z_a + 1e-6` (lens B downstream of lens A)
- the candidate **MUST** keep all coordinates within `[-50.0, 250.0] mm`

## Scoring (buyer spec · ratiometric)

```python
def _score(target_rms, achieved_rms):
    if achieved_rms is None or achieved_rms <= 0 or target_rms is None:
        return None
    return min(100.0, 100.0 * float(target_rms) / float(achieved_rms))
```

- `target_rms` = `1.000 mm` (oracle convergence bound for this geometry)
- `achieved_rms` = RMS spot radius measured by ray-tracing on the target plane
- Lower RMS → higher score · score = 100 ⇔ achievable reaches the oracle bound
- `valid = 1.0` if every instance ray-traces successfully (no NaN, every ray exits the bench)
- `combined_score = mean(score_i across instances) if valid else 0.0`

## Verification

```bash
python verification/evaluate.py \
  --candidate baseline/init.py \
  --out metrics.json
```

`evaluate.py` is **read-only** (verifier invariant): it imports `align_lens_pair`, runs honest geometric ray tracing over `data/instances.json`, writes `metrics.json` with per-instance `achieved_rms`, `score`, and final `combined_score`, `valid`.

## Files

```
Optics/Optics/lens_pair_aberration_v1_001/
├── Task.md                  # this file
├── README.md                # environment + run instructions
├── baseline/init.py         # starting point (edit-me)
├── verification/evaluate.py # read-only honest ray-tracing verifier
├── verification/_core.py    # shared ray-tracer primitives
├── data/instances.json      # 7 source/lens/target configurations
├── requirements.txt         # numpy only
└── frontier_eval/           # 9 .txt metadata files
```

## Difficulty target

Easy (gap_closed ≥ 0.6) with allowed upper bound score < 95 (avoid trivial floor).
