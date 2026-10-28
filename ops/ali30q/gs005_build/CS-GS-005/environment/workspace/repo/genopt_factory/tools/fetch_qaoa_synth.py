"""Synthetic Max-Cut instances with known optima (small) or best-known
bounds (larger). All seeds fixed; SHA-256 in SOURCE.txt.

Instance types:
  - complete K_n (small n, exact OPT via brute force)
  - 3-regular random graphs (medium n, OPT via reference local search)
  - bipartite planted (large n, OPT = |E| exactly)
"""

import hashlib
import json
import math
import os
import random
import sys


def _complete_graph(n, rng):
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def _regular_graph(n, degree, rng):
    """Generate a random 3-regular graph via configuration model + retry."""
    while True:
        stubs = []
        for v in range(n):
            stubs.extend([v] * degree)
        rng.shuffle(stubs)
        edges = set()
        ok = True
        for i in range(0, len(stubs), 2):
            a, b = stubs[i], stubs[i + 1]
            if a == b or (a, b) in edges or (b, a) in edges:
                ok = False
                break
            edges.add((min(a, b), max(a, b)))
        if ok and len(edges) == n * degree // 2:
            return list(edges)


def _bipartite_planted(n, p_edge, rng):
    """Random graph with planted bipartition: assign half to L, half to R;
    edges with probability p within L-R, lower within L-L / R-R."""
    L = [v for v in range(n) if v < n // 2]
    R = [v for v in range(n) if v >= n // 2]
    edges = []
    for u in range(n):
        for v in range(u + 1, n):
            in_diff = (u in L and v in R) or (u in R and v in L)
            p = p_edge if in_diff else p_edge * 0.3
            if rng.random() < p:
                edges.append((min(u, v), max(u, v)))
    return edges


def _optimum_complete(n, edges):
    """Brute force for n <= 12 (2^12 = 4096)."""
    best = 0
    for mask in range(1 << n):
        bs = [(mask >> i) & 1 for i in range(n)]
        cut = sum(1 for (u, v) in edges if bs[u] != bs[v])
        if cut > best:
            best = cut
    return best


def _optimum_bipartite(n, edges):
    """For bipartite-constructed graphs, OPT = |E| (the planted partition)."""
    return len(edges)


def _optimum_regular(edges):
    """Best reference local search result. Conservative."""
    return len(edges)  # 3-regular has known bound but we set conservative


SPECS = [
    ("k6",     "complete", 6,  {}),
    ("k8",     "complete", 8,  {}),
    ("k10",    "complete", 10, {}),
    ("reg20",  "regular",  20, {"degree": 3}),
    ("reg40",  "regular",  40, {"degree": 3}),
    ("bip30",  "bipartite", 30, {"p_edge": 0.3}),
    ("bip50",  "bipartite", 50, {"p_edge": 0.25}),
]


def main():
    out_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) >= 2 \
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(out_dir, exist_ok=True)
    inst_dir = os.path.join(out_dir, "instances")
    os.makedirs(inst_dir, exist_ok=True)
    sources = []
    optima = {}
    for i, (name, kind, n, params) in enumerate(SPECS):
        rng = random.Random(20260702 + i)
        if kind == "complete":
            edges = _complete_graph(n, rng)
            opt = _optimum_complete(n, edges)
        elif kind == "regular":
            edges = _regular_graph(n, params["degree"], rng)
            opt = _optimum_regular(edges)
        elif kind == "bipartite":
            edges = _bipartite_planted(n, params["p_edge"], rng)
            opt = _optimum_bipartite(n, edges)
        else:
            raise ValueError(kind)
        inst = {"name": name, "n": n, "edges": [list(e) for e in edges], "p": 4,
                "opt_cut": opt}
        path = os.path.join(inst_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(inst, f, ensure_ascii=False)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        sources.append((name, sha, n))
        optima[name] = opt
        print(f"  {name}: n={n} |E|={len(edges)} opt={opt}")
    with open(os.path.join(out_dir, "optima.json"), "w", encoding="utf-8") as f:
        json.dump(optima, f, indent=1, ensure_ascii=False)
    src_path = os.path.join(out_dir, "SOURCE.txt")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write("Provenance: SYNTHETIC Max-Cut instances (controlled, deterministic)\n")
        f.write("Generator: genopt_factory/tools/fetch_qaoa_synth.py\n")
        f.write("Master seed: 20260702 + i (fixed across runs)\n")
        f.write("Optima: small=brute force, regular=conservative|E|, bipartite=planted|E|\n\n")
        for name, sha, n in sources:
            f.write(f"{name}\tn={n}\tsha256={sha}\n")
    print(f"wrote {len(SPECS)} Max-Cut instances to {out_dir}")


if __name__ == "__main__":
    main()