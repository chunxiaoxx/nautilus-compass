"""Naive O(N^2) scaled dot-product attention. Materializes full N*N matrix.

This is the WEAK baseline: it's numerically correct but slow. The reference
(FlashAttention2-simplified) is correct AND faster — GPT5.5 N=3 has real gap
to demonstrate.
"""

import math


def attention_forward(instance: dict) -> dict:
    B = instance["B"]
    H = instance["H"]
    N = instance["N"]
    d = instance["d"]
    Q = instance["Q"]
    K = instance["K"]
    V = instance["V"]
    scale = 1.0 / math.sqrt(d)
    out = []
    for b in range(B):
        for h in range(H):
            # Slice Q[b][h], K[b][h], V[b][h] (each shape N x d)
            base = (b * H + h) * N * d
            Qbh = [Q[base + i * d : base + (i + 1) * d] for i in range(N)]
            Kbh = [K[base + i * d : base + (i + 1) * d] for i in range(N)]
            Vbh = [V[base + i * d : base + (i + 1) * d] for i in range(N)]
            Obh = []
            for i in range(N):
                # scores[i][j] = dot(Q[i], K[j]) * scale
                scores = [sum(Qbh[i][k] * Kbh[j][k] for k in range(d)) * scale
                          for j in range(N)]
                # softmax
                m = max(scores)
                exps = [math.exp(s - m) for s in scores]
                Z = sum(exps)
                weights = [e / Z for e in exps]
                # weighted sum of V
                out_row = [0.0] * d
                for j in range(N):
                    wj = weights[j]
                    Vj = Vbh[j]
                    for k in range(d):
                        out_row[k] += wj * Vj[k]
                Obh.append(out_row)
            out.extend(Obh)
    return {"O": out, "elapsed_s": 0.0}