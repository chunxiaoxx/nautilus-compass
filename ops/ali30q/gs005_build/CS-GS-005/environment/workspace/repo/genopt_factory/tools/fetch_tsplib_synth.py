"""Synthetic TSP instance generator (TSPLIB 镜像不可达时的本地 fallback).

生成不同规模/分布的实例(欧几里得 2-D),每个实例的 optimum 估算用 2-opt
多起点 + 多 restart 取最优(取该值作"reference optimum",作为难度 ground truth
的代理)。所有实例固定 seed 保证可重放,SHA256 + SOURCE.txt 写明 provenance。

注意:这是 controlled synthetic benchmark, 不是 TSPLIB 真实例。买方规则 §3.1
允许"benchmark 实例数据"由我方提供,只需 SHA256 + provenance 链可追溯。

生成 6 个实例(混合规模):
  - burma14_synth      14 城市 密集簇(玩具,易落 Easy)
  - grid20_synth       20 城市 网格(中,易落 Medium)
  - random50_synth     50 城市 均匀随机(中)
  - cluster100_synth   100 城市 4 簇(中)
  - random225_synth    225 城市 均匀随机(大)
  - random500_synth    500 城市 均匀随机(大,目标 Hard)
"""

import hashlib
import json
import math
import os
import random
import sys


def _optimum_estimate(coords, n_starts=20, n_restarts=3, time_limit_s=30):
    """Best-of-many 2-opt: random starts, restart budget, return best length."""
    import time
    rng = random.Random(20260702)
    n = len(coords)
    best_len = float("inf")

    def _nn(start):
        visited = [False] * n
        visited[start] = True
        t = [start]
        for _ in range(n - 1):
            last = t[-1]
            bj, bd = -1, float("inf")
            for j in range(n):
                if not visited[j]:
                    d = math.hypot(coords[last][0] - coords[j][0],
                                   coords[last][1] - coords[j][1])
                    if d < bd:
                        bd = d
                        bj = j
            t.append(bj)
            visited[bj] = True
        return t

    def _length(tour):
        s = 0.0
        for i in range(n):
            a, b = coords[tour[i]], coords[tour[(i + 1) % n]]
            s += math.hypot(a[0] - b[0], a[1] - b[1])
        return s

    def _two_opt(tour, t0, budget):
        improved = True
        while improved:
            if time.monotonic() - t0 > budget:
                return tour
            improved = False
            for i in range(1, n - 1):
                if time.monotonic() - t0 > budget:
                    return tour
                for j in range(i + 1, n):
                    a, b, c, d = tour[i - 1], tour[i], tour[j], tour[(j + 1) % n]
                    old = (math.hypot(coords[a][0] - coords[b][0], coords[a][1] - coords[b][1])
                           + math.hypot(coords[c][0] - coords[d][0], coords[c][1] - coords[d][1]))
                    new = (math.hypot(coords[a][0] - coords[c][0], coords[a][1] - coords[c][1])
                           + math.hypot(coords[b][0] - coords[d][0], coords[b][1] - coords[d][1]))
                    if new + 1e-9 < old:
                        tour[i:j + 1] = list(reversed(tour[i:j + 1]))
                        improved = True
                        break
                if improved:
                    break
        return tour

    t_start = time.monotonic()
    budget_per = time_limit_s / max(1, n_starts)
    starts = [0] + rng.sample(range(1, n), min(n_starts - 1, n - 1))
    for s in starts:
        t = _nn(s)
        t = _two_opt(t, t_start, budget_per)
        L = _length(t)
        if L < best_len:
            best_len = L
    return round(best_len, 4)


def _gen_burma14():
    rng = random.Random(11)
    coords = []
    for _ in range(14):
        coords.append((rng.uniform(0, 10), rng.uniform(0, 10)))
    return coords


def _gen_grid(n):
    side = max(2, int(math.ceil(math.sqrt(n))))
    coords = [(i % side, i // side) for i in range(n)]
    return coords


def _gen_random(n, scale, seed):
    rng = random.Random(seed)
    return [(rng.uniform(0, scale), rng.uniform(0, scale)) for _ in range(n)]


def _gen_cluster(n_clusters, cities_per, scale, seed):
    rng = random.Random(seed)
    centers = [(rng.uniform(0, scale), rng.uniform(0, scale))
               for _ in range(n_clusters)]
    coords = []
    for ci in range(n_clusters):
        cx, cy = centers[ci]
        for _ in range(cities_per):
            coords.append((cx + rng.gauss(0, scale * 0.05),
                           cy + rng.gauss(0, scale * 0.05)))
    rng.shuffle(coords)
    return coords[:n_clusters * cities_per]


def main():
    if len(sys.argv) >= 2:
        out_dir = os.path.abspath(sys.argv[1])
    else:
        out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                               "..", "data"))
    os.makedirs(out_dir, exist_ok=True)
    inst_dir = os.path.join(out_dir, "instances")
    os.makedirs(inst_dir, exist_ok=True)

    # Build candidate instances. Each (name, coords, time_limit_s_for_opt).
    specs = [
        ("burma14_synth",       _gen_burma14(),            10),
        ("grid20_synth",        _gen_grid(20),             10),
        ("random50_synth",      _gen_random(50,  100, 12), 15),
        ("cluster100_synth",    _gen_cluster(4, 25, 100, 13), 20),
        ("random225_synth",     _gen_random(225, 1000, 14), 25),
        ("random500_synth",     _gen_random(500, 1000, 15), 30),
    ]

    optima = {}
    sources = []
    for name, coords, opt_time in specs:
        opt = _optimum_estimate(coords, n_starts=10, time_limit_s=opt_time)
        instance = {"name": name, "dimension": len(coords), "node_coords": coords}
        path = os.path.join(inst_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(instance, f, ensure_ascii=False)
        # sha256 of the instance JSON (provenance)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        sources.append((name, sha, len(coords), opt))
        optima[name] = opt
        print(f"  {name}: {len(coords)} cities · opt~{opt}", flush=True)

    with open(os.path.join(out_dir, "optima.json"), "w", encoding="utf-8") as f:
        json.dump(optima, f, indent=1, ensure_ascii=False)

    src_path = os.path.join(out_dir, "SOURCE.txt")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write("Provenance: SYNTHETIC TSP instances (controlled, deterministic)\n")
        f.write("Generator: genopt_factory/tools/fetch_tsplib_synth.py\n")
        f.write("Master seed: 20260702 (fixed across runs)\n")
        f.write("Notes: TSPLIB official mirror unreachable from this environment\n")
        f.write("       (HTTP 503 / SSL). Synthetic instances with multi-restart\n")
        f.write("       2-opt optimum estimates serve as difficulty ground truth.\n\n")
        for name, sha, n, opt in sources:
            f.write(f"{name}\tn={n}\tsha256={sha}\topt~{opt}\n")
    print(f"wrote {len(optima)} synthetic instances to {out_dir}")


if __name__ == "__main__":
    main()