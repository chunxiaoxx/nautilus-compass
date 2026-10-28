"""Best-Fit Decreasing (BFD) reference for bin packing.

Sort items descending, then place each in the bin with the smallest leftover
space that still fits. Classic approximation algorithm with proven bound
(uses at most 11/9 * OPT + 1 bins asymptotically).

Target score ~70-90 vs the naive First-Fit baseline.
"""

def pack_bins(instance: dict) -> dict:
    cap = instance["bin_capacity"]
    items = list(instance["items"])
    n = len(items)
    # Sort indices by item size descending
    order = sorted(range(n), key=lambda i: items[i], reverse=True)
    bin_remain = []
    assignment = [0] * n
    for idx in order:
        sz = items[idx]
        # find bin with smallest leftover >= sz
        best_b = -1
        best_rem = float("inf")
        for b in range(len(bin_remain)):
            if bin_remain[b] >= sz - 1e-9 and bin_remain[b] - sz < best_rem:
                best_rem = bin_remain[b] - sz
                best_b = b
        if best_b >= 0:
            bin_remain[best_b] -= sz
            assignment[idx] = best_b
        else:
            bin_remain.append(cap - sz)
            assignment[idx] = len(bin_remain) - 1
    return {"num_bins": len(bin_remain), "assignment": assignment}