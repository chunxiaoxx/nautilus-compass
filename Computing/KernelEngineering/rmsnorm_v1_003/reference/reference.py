"""Naive 3-pass RMSNorm oracle (read-only)."""

from __future__ import annotations

import math


def rmsnorm_naive(x, weight, eps=1e-6):
    N = len(x)
    D = len(weight)
    output = []
    for i in range(N):
        row = x[i]
        s = 0.0
        for k in range(D):
            v = row[k]
            s += v * v
        mean_sq = s / D
        rms = math.sqrt(mean_sq + eps)
        inv_rms = 1.0 / rms
        out_row = []
        for k in range(D):
            out_row.append(row[k] * weight[k] * inv_rms)
        output.append(out_row)
    return output
