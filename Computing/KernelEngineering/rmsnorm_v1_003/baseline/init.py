"""rmsnorm_v1_003 · baseline starting point.

Naive 3-pass RMSNorm. Verifier imports `rmsnorm`. Candidate edits only this file.
"""

from __future__ import annotations

import math
import time


def rmsnorm(x, weight, eps=1e-6):
    """3-pass naive RMSNorm.

    pass 1: square all elements
    pass 2: row-reduce sum-of-squares, compute scalar rms
    pass 3: divide-and-weight element-wise

    Returns dict with keys "output" (N x D list of lists) and "elapsed_s" (float).
    """
    N = len(x)
    D = len(weight)
    assert N > 0 and D > 0

    t0 = time.perf_counter()

    # Pass 1: square (also compute sum to defer pass-2 work)
    row_sumsq = []
    for i in range(N):
        row = x[i]
        s = 0.0
        for k in range(D):
            v = row[k]
            s += v * v
        row_sumsq.append(s)

    # Pass 2: compute per-row rms
    row_rms = []
    for i in range(N):
        mean_sq = row_sumsq[i] / D
        rms = math.sqrt(mean_sq + eps)
        row_rms.append(rms)

    # Pass 3: divide-and-weight
    output = []
    for i in range(N):
        row = x[i]
        inv_rms = 1.0 / row_rms[i]
        out_row = []
        for k in range(D):
            out_row.append(row[k] * weight[k] * inv_rms)
        output.append(out_row)

    elapsed = time.perf_counter() - t0
    return {"output": output, "elapsed_s": float(elapsed)}
