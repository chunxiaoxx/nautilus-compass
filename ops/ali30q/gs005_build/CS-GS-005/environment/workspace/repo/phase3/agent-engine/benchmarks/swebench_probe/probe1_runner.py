"""Probe 1 runner — arm 1 (mono/generic) vs arm 3 (decomp/generic) at MATCHED budget.

Runs in the swebench-probe venv against real Docker instance containers. For each
instance, a FRESH container per arm (no cross-arm contamination), the SAME M3 model
(litellm route A), each wrapped in its own BudgetedModel with the SAME per-instance
token cap — so any arm-3 gain cannot be merely bought compute (design §4). Emits two
JSONL prediction files (arm1 / arm3) for the official harness; score them separately
and feed the paired booleans into aggregate_paired_multiseed.

Usage (from the venv):
  PYTHONUTF8=1 ANTHROPIC_API_KEY=... python probe1_runner.py \
      --instances pallets__flask-4045 --cap 400000 -o <out_dir>
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from budget import BudgetedModel, BudgetExceeded  # noqa: E402
from decomp_solver import make_stage_runner, solve_decomp  # noqa: E402
from predictions import write_predictions  # noqa: E402
from subset_loader import load_subset_instances  # noqa: E402

MODEL_CONFIG = {
    "model_name": "anthropic/MiniMax-M3",
    "model_kwargs": {"api_base": "https://api.minimaxi.com/anthropic"},
    "cost_tracking": "ignore_errors",
}


def _load_base_config() -> dict:
    from minisweagent.config import builtin_config_dir, get_config_from_spec
    spec = str(builtin_config_dir / "benchmarks" / "swebench.yaml")
    cfg = get_config_from_spec(spec)
    cfg["model"] = dict(MODEL_CONFIG)
    return cfg


def _fresh_env(base_config: dict, instance: dict):
    """Build a fresh Docker instance container (reuses mini-swe-agent's helper)."""
    from minisweagent.run.benchmarks.swebench import get_sb_environment
    # get_sb_environment mutates config["environment"]; give each arm its own copy.
    cfg = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base_config.items()}
    return get_sb_environment(cfg, instance), cfg


def _new_model(cap: int):
    from minisweagent.models import get_model
    return BudgetedModel(get_model(config=dict(MODEL_CONFIG)), max_total_tokens=cap)


def _cleanup(env):
    for attr in ("cleanup", "close", "stop", "__exit__"):
        fn = getattr(env, attr, None)
        if callable(fn):
            try:
                fn() if attr != "__exit__" else fn(None, None, None)
            except Exception:
                pass
            return


def run_arm1(base_config, instance, cap) -> dict:
    from minisweagent.agents.default import DefaultAgent
    env, cfg = _fresh_env(base_config, instance)
    model = _new_model(cap)
    try:
        agent = DefaultAgent(model, env, **cfg.get("agent", {}))
        try:
            info = agent.run(task=instance["problem_statement"])
            patch = info.get("submission", "")
        except BudgetExceeded:
            patch = ""
    finally:
        _cleanup(env)
    return {"patch": patch, "spent": model.spent}


def run_arm3(base_config, instance, cap) -> dict:
    env, cfg = _fresh_env(base_config, instance)
    model = _new_model(cap)
    try:
        run_stage = make_stage_runner(model, env)
        result = solve_decomp(instance["problem_statement"], run_stage=run_stage)
        patch = result.get("submission", "")
    finally:
        _cleanup(env)
    return {"patch": patch, "spent": model.spent}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--instances", nargs="+", required=True, help="instance_ids")
    ap.add_argument("--cap", type=int, default=400_000, help="per-instance token cap")
    ap.add_argument("-o", "--output", required=True, help="output dir for preds")
    ap.add_argument("--arms", nargs="+", default=["arm1", "arm3"])
    args = ap.parse_args(argv)

    os.makedirs(args.output, exist_ok=True)
    instances = load_subset_instances(subset=args.instances)
    runners = {"arm1": run_arm1, "arm3": run_arm3}

    for arm in args.arms:
        items = []
        for inst in instances:
            t0 = time.time()
            print(f"[{arm}] {inst['instance_id']} (cap={args.cap}) ...", flush=True)
            try:
                res = runners[arm](_load_base_config(), inst, args.cap)
            except Exception as e:  # degrade one instance, never abort the arm
                print(f"[{arm}] {inst['instance_id']} ERROR {type(e).__name__}: {e}", flush=True)
                res = {"patch": "", "spent": 0}
            print(f"[{arm}] {inst['instance_id']} done in {time.time()-t0:.0f}s "
                  f"patch_len={len(res['patch'])} spent={res['spent']}", flush=True)
            items.append({"instance_id": inst["instance_id"], "model_patch": res["patch"],
                          "model_name_or_path": f"MiniMax-M3-{arm}"})
        out = os.path.join(args.output, f"preds_{arm}.jsonl")
        write_predictions(out, f"MiniMax-M3-{arm}", items)
        print(f"[{arm}] wrote {len(items)} -> {out}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
