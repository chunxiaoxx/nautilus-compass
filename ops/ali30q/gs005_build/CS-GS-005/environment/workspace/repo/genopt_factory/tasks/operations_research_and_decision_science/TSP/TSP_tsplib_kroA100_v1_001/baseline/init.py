"""Weak baseline for TSP — only single-start nearest-neighbor, no 2-opt.

Designed to leave headroom over reference (which adds 2-opt multi-restart) so
that GPT5.5 N=3 has real gap to demonstrate (Hard 0.1-0.3 band per buyer §5.4).
"""

import math
import random


def _euclidean(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def solve_instance(instance: dict) -> dict:
    coords = instance["node_coords"]
    n = len(coords)
    if n == 0:
        return {"tour": []}

    # Single-start nearest-neighbor from city 0 — deterministic, weak.
    visited = [False] * n
    visited[0] = True
    tour = [0]
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
    return {"tour": tour}