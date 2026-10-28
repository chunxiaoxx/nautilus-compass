"""Worker: run the *naive* attention (the slow one used as baseline reference
for speedup calculation). Writes elapsed.txt in cwd.

Mirrors baseline/init.py naive algorithm (so timing is reproducible across runs).
"""

import argparse
import json
import math
import os
import time


def attention_naive(instance):
    B = instance["B"]; H = instance["H"]; N = instance["N"]; d = instance["d"]
    Q = instance["Q"]; K = instance["K"]; V = instance["V"]
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
                scores = [sum(Qbh[i][k] * Kbh[j][k] for k in range(d)) * scale
                          for j in range(N)]
                m = max(scores)
                exps = [math.exp(s - m) for s in scores]
                Z = sum(exps)
                weights = [e / Z for e in exps]
                out_row = [0.0] * d
                for j in range(N):
                    wj = weights[j]
                    Vj = Vbh[j]
                    for k in range(d):
                        out_row[k] += wj * Vj[k]
                Obh.append(out_row)
            out.extend(Obh)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--instance", required=True)
    args = ap.parse_args()

    with open(args.instance, encoding="utf-8") as f:
        inst = json.load(f)

    t0 = time.monotonic()
    _ = attention_naive(inst)
    elapsed = time.monotonic() - t0

    with open("elapsed.txt", "w", encoding="utf-8") as f:
        f.write(f"{elapsed:.4f}")


if __name__ == "__main__":
    main()