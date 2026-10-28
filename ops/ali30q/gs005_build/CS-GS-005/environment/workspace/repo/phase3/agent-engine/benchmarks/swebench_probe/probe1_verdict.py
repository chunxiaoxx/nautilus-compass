"""Probe 1 verdict — paired escape-noise on arm1 (baseline) vs arm3 (treatment).

Takes the two official-harness report JSONs (one per arm) over the SAME instances,
builds a single-seed paired record, and runs aggregate_paired_multiseed. With one
seed and small N the conservative gate will usually report escapes_noise=False — that
is the honest answer (a small paired set cannot clear the sign-test bar). Add more
seeds / a larger N to gain power.

Usage:
  python probe1_verdict.py --arm1-report <arm1.json> --arm3-report <arm3.json>
  # optionally repeat --arm1-report/--arm3-report in matched order for multi-seed.
"""
import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_HERE))  # benchmarks/ holds escape_noise_stats
from escape_noise_stats import aggregate_paired_multiseed  # noqa: E402


def _items_from_report(path: str) -> dict:
    """{instance_id: resolved_bool} for every submitted instance in a harness report."""
    d = json.load(open(path, encoding="utf-8"))
    resolved = set(d.get("resolved_ids", []))
    submitted = (d.get("resolved_ids", []) + d.get("unresolved_ids", [])
                 + d.get("error_ids", []) + d.get("empty_patch_ids", []))
    return {iid: (iid in resolved) for iid in submitted}


def _pass_at_1(items: dict) -> float:
    return sum(items.values()) / len(items) if items else 0.0


def build_seed_records(arm1_reports, arm3_reports):
    seeds = []
    for r1, r3 in zip(arm1_reports, arm3_reports):
        i1, i3 = _items_from_report(r1), _items_from_report(r3)
        common = set(i1) & set(i3)            # pair only on shared instances
        i1 = {k: i1[k] for k in common}
        i3 = {k: i3[k] for k in common}
        seeds.append({
            "arm1": {"pass_at_1": _pass_at_1(i1), "items": i1},
            "arm3": {"pass_at_1": _pass_at_1(i3), "items": i3},
        })
    return seeds


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm1-report", action="append", required=True)
    ap.add_argument("--arm3-report", action="append", required=True)
    args = ap.parse_args(argv)

    seeds = build_seed_records(args.arm1_report, args.arm3_report)
    agg = aggregate_paired_multiseed(seeds, baseline_key="arm1", treatment_key="arm3")

    n = len(next(iter(seeds))["arm1"]["items"]) if seeds else 0
    il, net = agg["item_level"], agg["treatment_net"]
    print("=" * 60)
    print("  PROBE 1 VERDICT — arm1 (mono) vs arm3 (decomp), matched budget")
    print(f"  seeds={agg['n_seeds']}  N(paired)={n}")
    print(f"  arm1 pass@1 mean: {agg['baseline']['mean']:.1%}  per-seed {agg['baseline']['per_seed']}")
    print(f"  arm3 pass@1 mean: {agg['treatment']['mean']:.1%}  per-seed {agg['treatment']['per_seed']}")
    print(f"  arm3 net (3-1) mean: {net['mean']:+.1%}  per-seed {net['per_seed']}  all_positive={net['all_seeds_positive']}")
    print(f"  item-level arm3/arm1 wins: {il['treatment_wins']}/{il['baseline_wins']} "
          f"(discordant={il['discordant']}, sign p={il['sign_test_p']:.4f})")
    print(f"  ESCAPES NOISE: {agg['escapes_noise']}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
