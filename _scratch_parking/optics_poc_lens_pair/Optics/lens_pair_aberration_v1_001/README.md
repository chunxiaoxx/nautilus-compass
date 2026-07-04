# Lens Pair Aberration · Optics PoC

## Task

Optimize 6-DOF lens-pair placement (each lens: axial z + lateral x, y) to minimize RMS spot radius on the target focal plane under honest geometric ray-tracing.

## Run

```bash
cd Optics/Optics/lens_pair_aberration_v1_001

# baseline score (paraxial placement)
python verification/evaluate.py --candidate baseline/init.py --out metrics_baseline.json

# edit baseline/init.py to improve
python verification/evaluate.py --candidate baseline/init.py --out metrics.json
```

## Environment

- Python 3.11+
- numpy >= 1.24
- Pure CPU ray-tracer using Snell refraction in thin-lens approximation
- Reproducible: fixed seeds, fixed data, no stochastic elements in baseline init

## File layout

```
Task.md                  # problem spec (read first)
baseline/init.py         # candidate code (edit this)
verification/evaluate.py # read-only verifier
verification/_core.py    # ray-tracer primitives
data/instances.json      # 7 geometry configurations
requirements.txt         # numpy
frontier_eval/*.txt      # 9 metadata files for buyer harness
metrics.json             # verifier output (created on run)
metrics_baseline.json    # baseline run snapshot
gpt55_trajectory.json    # GPT-5.5 reference trajectory (N=3 rounds)
```

## Score interpretation

`_score = min(100, 100 * target_rms / achieved_rms)` where target_rms = 1.0 mm.
- baseline (paraxial) achieves ~ achieved_rms ≈ 1.0346 mm → score ≈ 96.66
- Hard target: rms well below baseline (off-axis corrected) for score ≥ 98
- Easy band: gap_closed ≥ 0.6 requires reaching ~score 99+ on at least 4/7 instances
