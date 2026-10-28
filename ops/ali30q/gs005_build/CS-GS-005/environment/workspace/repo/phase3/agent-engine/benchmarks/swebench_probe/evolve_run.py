"""Probe 3 Phase B driver — recursive self-improvement on EXTERNAL benchmark fitness.

Each cycle: a proposer (M3) reads the current-best agent system_template + its probe
failures and proposes ONE revised system_template; the modified agent runs the FIXED
probe set; the escape-noise gate (consider_candidate) decides whether it becomes the
new best. ENHANCED OBSERVATION: every candidate is ALSO scored on a held-out VALIDATION
set the loop never selects on — so we can separate "the proposer can't improve" from
"the conservative gate is too strict to register improvement at this N". The verdict is
the validation trend, not the probe trend (anti-Goodhart).

Self-mod target = agent.system_template ONLY (the strategy prompt). The instance_template
— which carries {{task}} and the submission marker — is left untouched, so a bad proposal
can never break the submission mechanism.

Pure helpers (unit-tested) + injected fns let the driver be tested with fakes. The real
M3 / Docker effects live in make_propose_fn / make_run_agent_fn / make_score_fn and are
exercised only by the live smoke + main().
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))  # benchmarks/ holds escape_noise_stats

from escape_noise_stats import aggregate_paired_multiseed  # noqa: E402
from evolution import EvolutionState, consider_candidate, _mean  # noqa: E402
from proposer import build_proposer_prompt, extract_proposed_prompt  # noqa: E402

MODEL_CONFIG = {
    "model_name": "anthropic/MiniMax-M3",
    "model_kwargs": {"api_base": "https://api.minimaxi.com/anthropic"},
    "cost_tracking": "ignore_errors",
}


# ---------------------------------------------------------------- pure helpers

def inject_system_template(base_config: dict, system_template: str) -> dict:
    """Return a copy of ``base_config`` with agent.system_template replaced.

    The input is not mutated; instance_template (submission mechanism) is preserved.
    """
    out = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base_config.items()}
    out["agent"] = dict(base_config.get("agent", {}))
    out["agent"]["system_template"] = system_template
    return out


def report_filename(model_name_or_path: str, run_id: str) -> str:
    """Official-harness report file name (slashes become double underscores)."""
    return f"{model_name_or_path.replace('/', '__')}.{run_id}.json"


def parse_resolve_map(report_path: str) -> dict:
    """{instance_id: resolved_bool} for every submitted instance in a harness report."""
    d = json.load(open(report_path, encoding="utf-8"))
    resolved = set(d.get("resolved_ids", []))
    submitted = (d.get("resolved_ids", []) + d.get("unresolved_ids", [])
                 + d.get("error_ids", []) + d.get("empty_patch_ids", []))
    return {iid: (iid in resolved) for iid in submitted}


def _paired_escape(base_items: dict, cand_items: dict) -> bool:
    common = set(base_items) & set(cand_items)
    if not common:
        return False
    b = {k: base_items[k] for k in common}
    c = {k: cand_items[k] for k in common}
    seed = [{"b": {"pass_at_1": _mean(b), "items": b},
             "c": {"pass_at_1": _mean(c), "items": c}}]
    agg = aggregate_paired_multiseed(seed, baseline_key="b", treatment_key="c")
    return bool(agg["escapes_noise"])


# ------------------------------------------------------------------- driver

def run_evolution(probe_instances, validation_instances, n_cycles, base_prompt,
                  base_probe_items, *, propose_fn, run_agent_fn, score_fn, on_cycle=None):
    """Drive N evolution cycles with enhanced (per-candidate) validation observation.

    ``base_probe_items`` = the cycle-0 resolve map of the DEFAULT prompt on the probe
    set (reused from a prior run, so cycle 0 does not re-run the probe). Returns
    {"cycles": [...], "verdict": {...}}.
    """
    val0 = score_fn(run_agent_fn(base_prompt, validation_instances), validation_instances)
    state = EvolutionState(base_prompt, _mean(base_probe_items), [])
    cur_base_items = dict(base_probe_items)
    cycles = [{"cycle": 0, "prompt": base_prompt,
               "probe_mean": _mean(base_probe_items),
               "val_mean": _mean(val0), "val_items": val0, "accepted": None}]
    best_val_mean, best_val_cycle, best_val_items = _mean(val0), 0, val0
    val_best_accepted_mean = _mean(val0)
    by_id = {x["instance_id"]: x for x in probe_instances}
    if on_cycle:
        on_cycle({"cycles": cycles, "verdict": None})

    for c in range(1, n_cycles + 1):
        failed = [
            {"instance_id": iid,
             "problem_statement": by_id.get(iid, {}).get("problem_statement", ""),
             "error": "unresolved by current best"}
            for iid in by_id if not cur_base_items.get(iid, False)
        ]
        proposer_prompt = build_proposer_prompt(state.best_prompt, failed)
        cand = extract_proposed_prompt(propose_fn(proposer_prompt))
        if not cand:
            cycles.append({"cycle": c, "noop": True, "accepted": False,
                           "reason": "empty proposal"})
            if on_cycle:
                on_cycle({"cycles": cycles, "verdict": None})
            continue

        cand_items = score_fn(run_agent_fn(cand, probe_instances), probe_instances)
        cand_val = score_fn(run_agent_fn(cand, validation_instances), validation_instances)
        accepted, new_state = consider_candidate(state, cand, cand_items, cur_base_items)
        entry = new_state.history[-1]
        cycles.append({
            "cycle": c, "prompt": cand,
            "probe_mean": _mean(cand_items), "base_mean": _mean(cur_base_items),
            "probe_items": cand_items,
            "escapes_noise": entry["escapes_noise"], "sign_test_p": entry["sign_test_p"],
            "accepted": accepted,
            "val_mean": _mean(cand_val), "val_items": cand_val,
        })
        if _mean(cand_val) > best_val_mean:
            best_val_mean, best_val_cycle, best_val_items = _mean(cand_val), c, cand_val
        if accepted:
            state = new_state
            cur_base_items = cand_items
            val_best_accepted_mean = _mean(cand_val)
        if on_cycle:
            on_cycle({"cycles": cycles, "verdict": None})

    verdict = {
        "val_cycle0_mean": _mean(val0),
        "val_best_accepted_mean": val_best_accepted_mean,
        "val_best_any_mean": best_val_mean,
        "val_best_any_cycle": best_val_cycle,
        "val_best_any_escapes_noise": _paired_escape(val0, best_val_items),
        "n_accepts": sum(1 for c in cycles if c.get("accepted") is True),
        "n_cycles": n_cycles,
    }
    return {"cycles": cycles, "verdict": verdict}


# ----------------------------------------------------------- real effect fns

def _tag(prompt: str, instances) -> str:
    """Unique, collision-free run id per (prompt, instance-set)."""
    ids = ",".join(sorted(i["instance_id"] for i in instances))
    h = hashlib.sha1((prompt + "::" + ids).encode("utf-8")).hexdigest()[:12]
    return f"evo_{h}"


def make_propose_fn():
    """M3 (litellm route A) single completion -> raw text (proposer parses the fence)."""
    def propose_fn(proposer_prompt: str) -> str:
        import litellm
        resp = litellm.completion(
            model="anthropic/MiniMax-M3",
            api_base="https://api.minimaxi.com/anthropic",
            api_key=os.environ["ANTHROPIC_API_KEY"],
            messages=[{"role": "user", "content": proposer_prompt}],
        )
        return resp.choices[0].message.content or ""
    return propose_fn


def make_run_agent_fn(cap: int, out_root: str):
    """arm1 (mono DefaultAgent) with the candidate system_template injected.

    Returns a patches handle {"preds_path","instance_ids","model_name","run_id"} that
    score_fn feeds to the official harness. Each (prompt,set) gets a unique run_id so
    harness reports never collide.
    """
    from probe1_runner import _load_base_config, _new_model, _fresh_env, _cleanup
    from predictions import write_predictions

    def run_agent_fn(system_template: str, instances):
        run_id = _tag(system_template, instances)
        out_dir = os.path.join(out_root, run_id)
        os.makedirs(out_dir, exist_ok=True)
        preds_path = os.path.join(out_dir, "preds.jsonl")
        handle = {"preds_path": preds_path, "instance_ids": [i["instance_id"] for i in instances],
                  "model_name": run_id, "run_id": run_id}
        if os.path.exists(preds_path) and os.path.getsize(preds_path) > 0:
            print(f"[agent {run_id}] RESUME — preds exist, skip agent", flush=True)
            return handle
        items = []
        for inst in instances:
            t0 = time.time()
            base = _load_base_config()
            cfg = inject_system_template(base, system_template)
            print(f"[agent {run_id}] {inst['instance_id']} ...", flush=True)
            try:
                from minisweagent.agents.default import DefaultAgent
                env, cfg2 = _fresh_env(cfg, inst)
                # _fresh_env copies cfg; ensure injected template survived the copy
                cfg2["agent"] = dict(cfg.get("agent", {}))
                model = _new_model(cap)
                try:
                    agent = DefaultAgent(model, env, **cfg2.get("agent", {}))
                    try:
                        info = agent.run(task=inst["problem_statement"])
                        patch = info.get("submission", "")
                    except Exception:
                        patch = ""
                finally:
                    _cleanup(env)
            except Exception as e:
                print(f"[agent {run_id}] {inst['instance_id']} ERROR {type(e).__name__}: {e}", flush=True)
                patch = ""
            print(f"[agent {run_id}] {inst['instance_id']} done {time.time()-t0:.0f}s len={len(patch)}", flush=True)
            items.append({"instance_id": inst["instance_id"], "model_patch": patch,
                          "model_name_or_path": run_id})
        write_predictions(preds_path, run_id, items)
        return handle
    return run_agent_fn


def make_score_fn(work_root: str, proxy: str = "http://host.docker.internal:52889"):
    """Run the official swebench harness in a python:3.11 container -> resolve map."""
    def score_fn(patches, instances):
        preds_path = patches["preds_path"]
        run_id = patches["run_id"]
        ids = patches["instance_ids"]
        work_dir = os.path.dirname(preds_path)
        existing = os.path.join(work_dir, report_filename(run_id, run_id))
        if not os.path.exists(existing):
            cand = [f for f in os.listdir(work_dir) if f.endswith(f".{run_id}.json")]
            if cand:
                existing = os.path.join(work_dir, cand[0])
        if os.path.exists(existing):
            print(f"[score {run_id}] RESUME — report exists, skip harness", flush=True)
            m = parse_resolve_map(existing)
            for iid in ids:
                m.setdefault(iid, False)
            return m
        cmd = [
            "docker", "run", "--rm",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "-v", f"{work_dir}:/work",
            "-e", f"HTTP_PROXY={proxy}", "-e", f"HTTPS_PROXY={proxy}",
            "-e", "NO_PROXY=host.docker.internal,localhost,127.0.0.1",
            "python:3.11", "bash", "-lc",
            "pip install -q swebench && cd /work && python -m swebench.harness.run_evaluation "
            f"--predictions_path preds.jsonl --dataset_name princeton-nlp/SWE-bench_Lite "
            f"--instance_ids {' '.join(ids)} --run_id {run_id} --cache_level env --clean true",
        ]
        print(f"[score {run_id}] harness on {len(ids)} instances ...", flush=True)
        subprocess.run(cmd, check=False)
        report = os.path.join(work_dir, report_filename(run_id, run_id))
        if not os.path.exists(report):
            # harness writes the report in the cwd it ran from (/work -> work_dir)
            cand = [f for f in os.listdir(work_dir) if f.endswith(f".{run_id}.json")]
            report = os.path.join(work_dir, cand[0]) if cand else report
        if not os.path.exists(report):
            print(f"[score {run_id}] NO REPORT — all unresolved", flush=True)
            return {iid: False for iid in ids}
        m = parse_resolve_map(report)
        for iid in ids:
            m.setdefault(iid, False)
        return m
    return score_fn


# --------------------------------------------------------------------- main

def _prepull(ids):
    for iid in ids:
        img = "docker.io/swebench/sweb.eval.x86_64." + iid.replace("__", "_1776_").lower() + ":latest"
        print(f"[prepull] {img}", flush=True)
        subprocess.run(["docker", "pull", img], check=False)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--sets", default=os.path.join(_HERE, "evolve_sets.json"))
    ap.add_argument("--base-report", default=os.path.join(_HERE, "probe1_n15_arm1_result.json"),
                    help="cycle-0 probe resolve map (default system_template)")
    ap.add_argument("--cycles", type=int, default=3)
    ap.add_argument("--cap", type=int, default=5_000_000, help="per-instance token cap (natural-budget)")
    ap.add_argument("-o", "--output", required=True, help="run dir for preds/reports")
    ap.add_argument("--result", default=os.path.join(_HERE, "evolve_result.json"))
    ap.add_argument("--prepull", action="store_true", help="docker pull validation images first")
    ap.add_argument("--smoke", action="store_true", help="N=1, tiny probe/validation subset")
    args = ap.parse_args(argv)

    from subset_loader import load_subset_instances
    sets = json.load(open(args.sets, encoding="utf-8"))
    probe_ids, valid_ids = sets["probe_ids"], sets["validation_ids"]
    base_prompt = sets["base_system_template"]
    base_probe_items = parse_resolve_map(args.base_report)

    if args.smoke:
        # lightest end-to-end wiring check: one already-pulled probe instance that is
        # known-resolved at base + one light validation instance, N=1.
        probe_ids = ["pallets__flask-4045"]
        valid_ids = ["psf__requests-2674"]
        base_probe_items = {k: base_probe_items[k] for k in probe_ids}
        args.cycles = 1

    probe_instances = load_subset_instances(subset=probe_ids)
    validation_instances = load_subset_instances(subset=valid_ids)

    if args.prepull:
        _prepull(valid_ids + (probe_ids if args.smoke else []))

    os.makedirs(args.output, exist_ok=True)
    propose_fn = make_propose_fn()
    run_agent_fn = make_run_agent_fn(args.cap, args.output)
    score_fn = make_score_fn(args.output)

    print(f"=== Probe 3 evolution: {len(probe_instances)} probe / {len(validation_instances)} "
          f"validation / N={args.cycles} cycles / cap={args.cap} ===", flush=True)
    def _checkpoint(partial):
        json.dump(partial, open(args.result, "w", encoding="utf-8"), indent=2)
        print(f"[checkpoint] {len(partial['cycles'])} cycle(s) -> {args.result}", flush=True)

    out = run_evolution(probe_instances, validation_instances, args.cycles, base_prompt,
                        base_probe_items, propose_fn=propose_fn, run_agent_fn=run_agent_fn,
                        score_fn=score_fn, on_cycle=_checkpoint)
    json.dump(out, open(args.result, "w", encoding="utf-8"), indent=2)
    v = out["verdict"]
    print("=" * 60)
    print("  PROBE 3 VERDICT — recursive self-improvement on external benchmark")
    print(f"  validation @ cycle 0:        {v['val_cycle0_mean']:.1%}")
    print(f"  validation @ best ACCEPTED:  {v['val_best_accepted_mean']:.1%}  (accepts={v['n_accepts']})")
    print(f"  validation @ best ANY cand:  {v['val_best_any_mean']:.1%}  (cycle {v['val_best_any_cycle']}, "
          f"escapes_noise={v['val_best_any_escapes_noise']})")
    print(f"  -> result written to {args.result}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
