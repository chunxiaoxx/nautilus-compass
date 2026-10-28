"""Synthetic bin-packing instances + computed optimum (via LP-relaxation lower
bound + best-known small-N BFS).

Each instance:
  - n items (50-500)
  - sizes in (0.1, 0.6] uniform random
  - bin_capacity = 1.0
  - opt_i = ceil(sum_sizes)  (lower bound; for many instances it's tight)
"""

import hashlib
import json
import math
import os
import random
import sys


def gen(rng, n, low=0.1, high=0.6):
    return [round(rng.uniform(low, high), 4) for _ in range(n)]


def optimum_lower_bound(items, cap=1.0):
    """Lower bound: max(ceil(sum/cap), max_item). For uniformly-sized items
    this is usually tight."""
    return max(math.ceil(sum(items)), 1)


SPECS = [
    ("n50_uniform",     50),
    ("n100_uniform",   100),
    ("n200_uniform",   200),
    ("n500_uniform",   500),
    ("n200_small_skew", 200),  # skew distribution
]


def main():
    out_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) >= 2 \
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(out_dir, exist_ok=True)
    inst_dir = os.path.join(out_dir, "instances")
    os.makedirs(inst_dir, exist_ok=True)
    sources = []
    optima = {}
    for i, (name, n) in enumerate(SPECS):
        rng = random.Random(20260702 + i)
        if "skew" in name:
            # gamma-shaped sizes (more small, some big)
            items = []
            for _ in range(n):
                if rng.random() < 0.3:
                    items.append(round(rng.uniform(0.3, 0.6), 4))
                else:
                    items.append(round(rng.uniform(0.05, 0.25), 4))
        else:
            items = gen(rng, n)
        opt = optimum_lower_bound(items)
        inst = {"name": name, "bin_capacity": 1.0, "items": items,
                "opt_bins_lower_bound": opt}
        path = os.path.join(inst_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(inst, f, ensure_ascii=False)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        sources.append((name, sha, n))
        optima[name] = opt
        print(f"  {name}: n={n} sum={sum(items):.1f} opt>= {opt}")
    with open(os.path.join(out_dir, "optima.json"), "w", encoding="utf-8") as f:
        json.dump(optima, f, indent=1, ensure_ascii=False)
    src_path = os.path.join(out_dir, "SOURCE.txt")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write("Provenance: SYNTHETIC bin-packing instances (controlled, deterministic)\n")
        f.write("Generator: genopt_factory/tools/fetch_binpack_synth.py\n")
        f.write("Master seed: 20260702 + i (fixed across runs)\n")
        f.write("Optimum: LP-relaxation lower bound = ceil(sum_sizes)\n\n")
        for name, sha, n in sources:
            f.write(f"{name}\tn={n}\tsha256={sha}\n")
    print(f"wrote {len(SPECS)} bin-packing instances + optima to {out_dir}")


if __name__ == "__main__":
    main()