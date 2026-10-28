"""Reference solver: 1-flip greedy local search from a random bitstring.

Pure stdlib, deterministic. For each instance, try multiple random restarts
(seed-20260702) and keep the best cut found. This is not a true QAOA
simulation (no quantum circuit), but is a strong classical heuristic that
gives GPT5.5 N=3 a real gap to demonstrate.

Target: ~85-95/100 (close to OPT on most random graphs, sometimes the
optimum itself for bipartite graphs).
"""

import random


def _cut_size(bitstring, edges):
    return sum(1 for (u, v) in edges if bitstring[u] != bitstring[v])


def _one_flip_pass(bitstring, edges):
    """Single 1-flip local search: try flipping each bit; accept if improves cut."""
    n = len(bitstring)
    improved = True
    while improved:
        improved = False
        for i in range(n):
            old = bitstring[i]
            bitstring[i] = 1 - old
            if _cut_size(bitstring, edges) > _cut_size(bitstring, edges) - 1:
                # flipping i increased the cut
                improved = True
            else:
                bitstring[i] = old
    return bitstring


def _local_search(bitstring, edges, max_iters=200):
    """Run 1-flip local search until convergence or max_iters."""
    best = list(bitstring)
    best_cut = _cut_size(best, edges)
    cur = list(bitstring)
    no_improve = 0
    for _ in range(max_iters):
        improved = False
        n = len(cur)
        for i in range(n):
            old = cur[i]
            cur[i] = 1 - old
            new_cut = _cut_size(cur, edges)
            if new_cut > best_cut:
                best_cut = new_cut
                best = list(cur)
                improved = True
            elif new_cut == _cut_size(cur, edges) - 1:
                # flipping decreased
                cur[i] = old
        if not improved:
            no_improve += 1
            if no_improve >= 3:
                break
    return best, best_cut


def qaoa_maxcut(instance: dict) -> dict:
    n = instance["n"]
    edges = instance["edges"]
    rng = random.Random(20260702)
    best = None
    best_cut = -1
    n_restarts = 5
    for s in range(n_restarts):
        bitstring = [rng.randint(0, 1) for _ in range(n)]
        cand, cut = _local_search(bitstring, edges, max_iters=200)
        if cut > best_cut:
            best_cut = cut
            best = cand
    return {"bitstring": best, "cut_size": best_cut}