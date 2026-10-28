"""FlashAttention2-simplified: block-tiled streaming softmax in pure stdlib.

The key trick: never materialize the full N x N matrix. Tile Q into blocks of
size BLOCK_N; for each Q-block, stream over K/V blocks accumulating
(m_i, l_i, O_i) running statistics (online softmax). Output identical to naive
up to fp reassociation.

This is the STRONG reference. The naive baseline cannot beat it on long
sequences — GPT5.5 N=3 must either:
  - implement a true FlashAttention-style block-tiled softmax
  - or find some pure-stdlib shortcut (e.g. exploit symmetry, batching tricks)

target ~95/100 (numerically correct + ~3-5x speedup on long N).
"""

import math


BLOCK_N = 32  # tile size


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
            base = (b * H + h) * N * d
            Qbh = [Q[base + i * d : base + (i + 1) * d] for i in range(N)]
            Kbh = [K[base + i * d : base + (i + 1) * d] for i in range(N)]
            Vbh = [V[base + i * d : base + (i + 1) * d] for i in range(N)]
            Obh = []
            for i in range(N):
                Qi = Qbh[i]
                # Online softmax over K/V blocks
                m_i = -float("inf")
                l_i = 0.0
                O_i = [0.0] * d
                for kblk in range(0, N, BLOCK_N):
                    kend = min(kblk + BLOCK_N, N)
                    # scores in this block
                    blk_max = -float("inf")
                    blk_scores = []
                    for j in range(kblk, kend):
                        s = sum(Qi[t] * Kbh[j][t] for t in range(d)) * scale
                        blk_scores.append(s)
                        if s > blk_max:
                            blk_max = s
                    # update running stats (online softmax rescaling)
                    new_m = max(m_i, blk_max)
                    if m_i == -float("inf"):
                        alpha = 1.0
                    else:
                        alpha = math.exp(m_i - new_m)
                    beta = math.exp(blk_max - new_m)
                    # rescale O_i by alpha; accumulate V contributions scaled by beta/Z
                    Z_blk = sum(math.exp(s - blk_max) for s in blk_scores)
                    O_i = [alpha * x for x in O_i]
                    l_i = alpha * l_i + beta * Z_blk
                    for j in range(kblk, kend):
                        wj = beta * math.exp(blk_scores[j - kblk] - blk_max)
                        Vj = Vbh[j]
                        for t in range(d):
                            O_i[t] += wj * Vj[t]
                    m_i = new_m
                # finalize
                Obh.append([x / l_i for x in O_i])
            out.extend(Obh)
    return {"O": out, "elapsed_s": 0.0}