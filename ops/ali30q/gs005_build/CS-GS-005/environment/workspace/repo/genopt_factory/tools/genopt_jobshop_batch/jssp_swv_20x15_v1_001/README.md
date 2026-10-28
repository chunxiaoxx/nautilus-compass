# Storer-Wu-Vaccari 20 jobs x 15 machines

JSSP GenOpt task. Instances: swv06, swv07, swv08, swv09, swv10.
Baseline = naive list scheduler (suboptimal). Optimize toward known optima.
Self-contained: data/instances/*.json + data/optima.json included.

## Reproduce the full artifact set
Run `sh reproduce.sh` (or `docker build -t t . && docker run --rm t`).
Regenerates every file in `frontier_eval/artifact_files.txt`:
- `metrics.json`, `artifacts.json` — written by `verification/evaluate.py`
- `eval.stdout.txt`, `eval.stderr.txt` — captured stdout/stderr of the eval command
