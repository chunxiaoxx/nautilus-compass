"""Generate attention workloads with controlled size and seed.

Sizes:
  - n128_d64_b2_h8   small
  - n256_d64_b2_h8   medium
  - n512_d64_b2_h8   medium-large
  - n1024_d64_b1_h4  large (Flash wins clearly)
  - n2048_d64_b1_h4  very large (Flash wins huge)
"""

import hashlib
import json
import math
import os
import random
import sys


def gen(B, H, N, d, seed):
    rng = random.Random(seed)
    flat_size = B * H * N * d
    # Use small ints to keep JSON small and load fast.
    Q = [[rng.uniform(-1.0, 1.0) for _ in range(d)] for _ in range(B * H * N)]
    K = [[rng.uniform(-1.0, 1.0) for _ in range(d)] for _ in range(B * H * N)]
    V = [[rng.uniform(-1.0, 1.0) for _ in range(d)] for _ in range(B * H * N)]
    return {
        "name": f"n{N}_d{d}_b{B}_h{H}",
        "B": B, "H": H, "N": N, "d": d,
        "Q": [x for row in Q for x in row],
        "K": [x for row in K for x in row],
        "V": [x for row in V for x in row],
    }


SPECS = [
    ("n128_d64_b2_h8",   2, 8, 128,  64),
    ("n256_d64_b2_h4",   2, 4, 256,  64),
    ("n512_d64_b1_h4",   1, 4, 512,  64),
    ("n1024_d64_b1_h2",  1, 2, 1024, 64),
]


def main():
    out_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) >= 2 \
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(out_dir, exist_ok=True)
    inst_dir = os.path.join(out_dir, "instances")
    os.makedirs(inst_dir, exist_ok=True)
    sources = []
    for name, B, H, N, d in SPECS:
        inst = gen(B, H, N, d, seed=20260702)
        path = os.path.join(inst_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(inst, f, ensure_ascii=False)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        sources.append((name, sha, N, d))
        print(f"  {name}: B={B} H={H} N={N} d={d} size={os.path.getsize(path)//1024}KB")
    src_path = os.path.join(out_dir, "SOURCE.txt")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write("Provenance: SYNTHETIC attention workloads (controlled, deterministic)\n")
        f.write("Generator: genopt_factory/tools/fetch_attention_synth.py\n")
        f.write("Master seed: 20260702 (fixed across runs)\n")
        f.write("Reference algorithm: FlashAttention2 (Dao et al. 2022) — block-tiled streaming softmax\n\n")
        for name, sha, N, d in sources:
            f.write(f"{name}\tN={N}\td={d}\tsha256={sha}\n")
    print(f"wrote {len(SPECS)} attention workloads to {out_dir}")


if __name__ == "__main__":
    main()