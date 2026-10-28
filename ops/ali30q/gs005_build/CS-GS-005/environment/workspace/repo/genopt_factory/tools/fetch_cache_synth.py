"""Synthetic cache workload generator.

Mixes:
  - looping pattern (LRU-friendly)
  - scan pattern (LRU-hostile)
  - phase shift (LRU/ARC adaptation test)
"""

import hashlib
import json
import os
import random
import sys


def gen_looping(rng, capacity, total_ops):
    """Zipfian-like access over working set ~= 2*capacity (LRU strongly wins)."""
    working = list(range(capacity * 2))
    weights = [1.0 / (i + 1) for i in range(len(working))]
    Z = sum(weights)
    weights = [w / Z for w in weights]
    ops = []
    for _ in range(total_ops):
        k = rng.choices(working, weights=weights, k=1)[0]
        ops.append(("get", k))
        if rng.random() < 0.5:
            ops.append(("put", k, rng.randint(0, 100000)))
    return ops


def gen_scan(rng, capacity, total_ops):
    """Sequential scan, but smaller than capacity and tail-reuse — LRU keeps
    recently-seen, scan evicts older → scan within 1.5x capacity items benefits
    from LRU vs FIFO."""
    ops = []
    scan_size = max(1, int(capacity * 1.5))
    scan_keys = list(range(capacity, capacity + scan_size))
    for k in scan_keys[:total_ops]:
        ops.append(("get", k))
    # Re-access first half so LRU still wins some hits.
    for k in scan_keys[: scan_size // 2]:
        ops.append(("get", k))
    return ops


def gen_phase_shift(rng, capacity, total_ops):
    """Two phases: working set A then working set B (small overlap).
    LRU punishes phase A when phase B starts; ARC adapts faster."""
    ops = []
    A = list(range(0, capacity * 2))
    B = list(range(int(capacity * 1.5), int(capacity * 3.5)))
    half = total_ops // 2
    for _ in range(half):
        k = rng.choice(A)
        ops.append(("get", k))
        if rng.random() < 0.4:
            ops.append(("put", k, rng.randint(0, 100000)))
    for _ in range(total_ops - half):
        k = rng.choice(B)
        ops.append(("get", k))
        if rng.random() < 0.4:
            ops.append(("put", k, rng.randint(0, 100000)))
    return ops


def gen_mixed(rng, capacity, total_ops):
    """YCSB-like: 80% working set, 20% random scan — LRU strongly beats FIFO."""
    ops = []
    working = list(range(capacity * 3))
    for _ in range(total_ops):
        r = rng.random()
        if r < 0.8:
            k = rng.choice(working[:capacity * 2])
        else:
            k = rng.randint(capacity * 5, capacity * 30)
        ops.append(("get", k))
        if rng.random() < 0.3:
            ops.append(("put", k, rng.randint(0, 100000)))
    return ops


SPECS = [
    ("looping_c100_n5k",   gen_looping,    100, 5000),
    ("scan_c100_n10k",     gen_scan,       100, 10000),
    ("phase_c100_n8k",     gen_phase_shift,100, 8000),
    ("mixed_c200_n10k",    gen_mixed,      200, 10000),
    ("looping_c500_n15k",  gen_looping,    500, 15000),
]


def main():
    out_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) >= 2 \
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(out_dir, exist_ok=True)
    inst_dir = os.path.join(out_dir, "instances")
    os.makedirs(inst_dir, exist_ok=True)
    sources = []
    for name, gen, cap, n in SPECS:
        rng = random.Random(20260702)
        ops = gen(rng, cap, n)
        inst = {"name": name, "capacity": cap, "ops": ops}
        path = os.path.join(inst_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(inst, f, ensure_ascii=False)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        sources.append((name, sha, cap, n))
        print(f"  {name}: cap={cap} ops={len(ops)} size={os.path.getsize(path)//1024}KB")
    src_path = os.path.join(out_dir, "SOURCE.txt")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write("Provenance: SYNTHETIC cache workload traces (controlled, deterministic)\n")
        f.write("Generator: genopt_factory/tools/fetch_cache_synth.py\n")
        f.write("Master seed: 20260702 (fixed across runs)\n\n")
        for name, sha, cap, n in sources:
            f.write(f"{name}\tcap={cap}\tn_ops={n}\tsha256={sha}\n")
    print(f"wrote {len(SPECS)} cache traces to {out_dir}")


if __name__ == "__main__":
    main()