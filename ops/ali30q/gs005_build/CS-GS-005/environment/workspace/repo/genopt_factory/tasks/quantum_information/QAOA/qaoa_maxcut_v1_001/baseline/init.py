"""Random uniform bitstring sampling — the weak baseline for QAOA Max-Cut.

Pure stdlib, deterministic.  The expected cut size for a random bitstring is
~ 0.5 * |E| (each edge cut with probability 0.5).

GPT5.5 N=3 should easily beat this by:
  - Implementing a real QAOA classical simulation
  - Or Goemans-Williamson SDP + randomized rounding
  - Or even simple greedy local search (1-flip) starting from the random
    baseline
"""

import random


def _cut_size(bitstring, edges):
    return sum(1 for (u, v) in edges if bitstring[u] != bitstring[v])


def qaoa_maxcut(instance: dict) -> dict:
    n = instance["n"]
    seed = 20260702
    rng = random.Random(seed)
    bitstring = [rng.randint(0, 1) for _ in range(n)]
    return {"bitstring": bitstring, "cut_size": _cut_size(bitstring, instance["edges"])}