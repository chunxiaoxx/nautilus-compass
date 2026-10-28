#!/bin/sh
# Reproduce the COMPLETE frontier-eval artifact set for this task, deterministically.
#
#   verification/evaluate.py  ->  metrics.json + artifacts.json   (evaluator outputs)
#   stdout/stderr redirect     ->  eval.stdout.txt + eval.stderr.txt (captured streams)
#
# Every file listed in frontier_eval/artifact_files.txt is (re)generated here.
# Run:  sh reproduce.sh      (or: docker build -t t . && docker run --rm t)
set -eu
cd "$(dirname "$0")"

# Portable: prefer python3, fall back to python (bare-metal hosts often lack a
# `python` alias; a delivered reproduce cmd must not depend on it).
PY="$(command -v python3 || command -v python)"
"$PY" verification/evaluate.py --benchmark-dir . --candidate baseline/init.py \
    >eval.stdout.txt 2>eval.stderr.txt

echo "reproduced artifacts:"
ls -l metrics.json artifacts.json eval.stdout.txt eval.stderr.txt
