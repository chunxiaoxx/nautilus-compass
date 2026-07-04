"""Naive matrix-multiplication reference oracle (read-only)."""

from __future__ import annotations


def naive_matmul(A, B):
    M = len(A)
    K = len(A[0]) if M > 0 else 0
    Kb = len(B)
    N = len(B[0]) if Kb > 0 else 0
    C = [[0.0] * N for _ in range(M)]
    for i in range(M):
        Ai = A[i]
        Ci = C[i]
        for k in range(K):
            aik = Ai[k]
            Bk = B[k]
            for j in range(N):
                Ci[j] += aik * Bk[j]
    return C
