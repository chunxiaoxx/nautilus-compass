"""tiled_matmul_v1_001 · baseline starting point.

Pure stdlib naive triple-loop matrix multiplication. Verifier imports
`matmul`. Candidate edits only this file.
"""

from __future__ import annotations

import time


def matmul(A, B):
    """Naive O(M*K*N) triple-loop matrix multiplication.

    A: M×K matrix as list of M rows (K floats each)
    B: K×N matrix as list of K rows (N floats each)
    returns dict with keys "C" (M×N list of lists) and "elapsed_s" (float).
    """
    M = len(A)
    K = len(A[0]) if M > 0 else 0
    K_b = len(B)
    N = len(B[0]) if K_b > 0 else 0

    t0 = time.perf_counter()
    C = [[0.0] * N for _ in range(M)]
    for i in range(M):
        Ai = A[i]
        Ci = C[i]
        for k in range(K):
            aik = Ai[k]
            Bk = B[k]
            for j in range(N):
                Ci[j] += aik * Bk[j]
    elapsed = time.perf_counter() - t0
    return {"C": C, "elapsed_s": float(elapsed)}
