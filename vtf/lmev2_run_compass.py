"""run_compass.py · Compass memory driver for LME-V2.

Bypasses run_eval.py's method whitelist by materializing runtime questions/
haystack itself, then invoking evaluation.harness with a compass memory config.

Usage (on GPU machine):
  python3 run_compass.py --domain web --tier small --limit 3          # smoke
  python3 run_compass.py --domain web   --tier small                  # full
  python3 run_compass.py --domain enterprise --tier small
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.public_data import (  # noqa: E402
    materialize_runtime_haystack,
    materialize_runtime_questions,
)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--domain", choices=["web", "enterprise"], required=True)
    p.add_argument("--tier", default="small", choices=["small", "medium"])
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--memory-config", default="/root/compass_cfg.json")
    p.add_argument("--output-root", default="/root/lmev2_runs")
    p.add_argument("--base-url", default="http://localhost:8023/v1")
    p.add_argument("--model", default="Qwen/Qwen3.5-9B")
    p.add_argument("--evaluator-model", default=None)
    p.add_argument("--evaluator-base-url", default=None)
    p.add_argument("--evaluator-timeout-seconds", type=float, default=180.0)
    p.add_argument("--reader-concurrency", type=int, default=16)
    p.add_argument("--prompt-workers", type=int, default=4)
    p.add_argument("--timeout-seconds", type=float, default=43200.0)
    args = p.parse_args()

    data_root = REPO_ROOT / "data" / "longmemeval-v2"
    runtime_dir = Path(args.output_root) / f"compass_{args.domain}_{args.tier}_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    qs = materialize_runtime_questions(
        data_root=data_root,
        domain=args.domain,
        question_ids=None,
        limit=args.limit,
        output_path=runtime_dir / "questions.json",
    )
    materialize_runtime_haystack(
        data_root=data_root,
        tier=args.tier,
        selected_questions=qs,
        output_path=runtime_dir / "haystack.json",
    )
    print(f"materialized {len(qs)} questions -> {runtime_dir}", flush=True)

    out_dir = Path(args.output_root) / f"compass_{args.domain}_{args.tier}"
    cmd = [
        sys.executable, "-m", "evaluation.harness",
        "--domain", args.domain,
        "--questions-path", str(runtime_dir / "questions.json"),
        "--haystack-path", str(runtime_dir / "haystack.json"),
        "--trajectories-path", str(data_root / "trajectories.jsonl"),
        "--memory-config-path", args.memory_config,
        "--output-dir", str(out_dir),
        "--model", args.model,
        "--base-url", args.base_url,
        "--temperature", "0.6",
        "--top-p", "0.95",
        "--top-k", "20",
        "--reader-max-concurrent-requests", str(args.reader_concurrency),
        "--prompt-build-max-workers", str(args.prompt_workers),
        "--timeout-seconds", str(args.timeout_seconds),
    ]
    if args.evaluator_model:
        cmd += ["--evaluator-model", args.evaluator_model,
                "--evaluator-timeout-seconds", str(args.evaluator_timeout_seconds)]
        if args.evaluator_base_url:
            cmd += ["--evaluator-base-url", args.evaluator_base_url]
    print("RUN:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
