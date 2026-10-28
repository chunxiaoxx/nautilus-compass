"""Strong TSP solver: nearest-neighbor + 2-opt with multi-restart.

Deterministic (fixed RNG seed). Designed to leave headroom over the naive baseline
(score target ~95 vs ~70) so that GPT5.5 N=3 has real improvement gap to demonstrate
(Hard 0.1-0.3 grading band per buyer §5.4).
"""

import math
import random


def _euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _tour_length(tour, coords):
    total = 0.0
    n = len(tour)
    for i in range(n):
        a = coords[tour[i]]
        b = coords[tour[(i + 1) % n]]
        total += _euclidean(a, b)
    return total


def _nearest_neighbor(start, coords, n):
    visited = [False] * n
    visited[start] = True
    tour = [start]
    for _ in range(n - 1):
        last = tour[-1]
        best_d = float("inf")
        best_j = -1
        for j in range(n):
            if not visited[j]:
                d = _euclidean(coords[last], coords[j])
                if d < best_d:
                    best_d = d
                    best_j = j
        tour.append(best_j)
        visited[best_j] = True
    return tour


def _two_opt(tour, coords, time_budget_ms):
    """Iterative 2-opt with first-improvement. Deterministic iteration order."""
    import time
    t0 = time.monotonic()
    n = len(tour)
    improved = True
    while improved:
        if (time.monotonic() - t0) * 1000 > time_budget_ms:
            return tour
        improved = False
        for i in range(1, n - 1):
            for j in range(i + 1, n):
                a_i = tour[i - 1]
                b_i = tour[i]
                c_j = tour[j]
                d_j = tour[(j + 1) % n]
                old = (_euclidean(coords[a_i], coords[b_i])
                       + _euclidean(coords[c_j], coords[d_j]))
                new = (_euclidean(coords[a_i], coords[c_j])
                       + _euclidean(coords[b_i], coords[d_j]))
                if new + 1e-9 < old:
                    tour[i:j + 1] = list(reversed(tour[i:j + 1]))
                    improved = True
                    break
            if improved:
                break
    return tour


def solve_instance(instance: dict) -> dict:
    n = len(instance["node_coords"])
    if n == 0:
        return {"tour": []}

    # Time budget: 100s for 2-opt, leave slack for verifier overhead.
    per_pass_ms = 100_000 // 5  # 20s per restart, 5 restarts

    best_tour = None
    best_len = float("inf")
    rng = random.Random(20260702)  # fixed seed for determinism
    starts = [0] + rng.sample(range(1, n), min(4, n - 1))
    for s in starts:
        t = _nearest_neighbor(s, instance["node_coords"], n)
        t = _two_opt(t, instance["node_coords"], per_pass_ms)
        L = _tour_length(t, instance["node_coords"])
        if L < best_len:
            best_len = L
            best_tour = t
    return {"tour": best_tour}