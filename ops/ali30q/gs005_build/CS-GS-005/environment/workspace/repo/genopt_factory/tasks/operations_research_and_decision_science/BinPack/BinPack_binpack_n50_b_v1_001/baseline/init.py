"""Naive First-Fit bin packing — weak baseline (no sorting, items in given order).

This MUST be byte-identical (algorithmically) to verifier._ff_bins(items, cap)
in evaluation/evaluate.py — if they diverge, the score formula breaks.
"""


def pack_bins(instance: dict) -> dict:
    items = instance["items"]
    cap = instance.get("bin_capacity", 1.0)
    remain = []
    assignment = []
    for sz in items:
        placed = False
        for b in range(len(remain)):
            if remain[b] >= sz - 1e-9:
                remain[b] -= sz
                assignment.append(b)
                placed = True
                break
        if not placed:
            remain.append(cap - sz)
            assignment.append(len(remain) - 1)
    return {"num_bins": len(remain), "assignment": assignment}