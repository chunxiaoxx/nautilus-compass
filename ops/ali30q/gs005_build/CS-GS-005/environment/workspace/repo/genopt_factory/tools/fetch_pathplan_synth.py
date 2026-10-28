"""Synthetic 2D grid path-planning instances + computed optima (BFS exact).

Instance types:
  - open20/open100: open grid (low obstacle density)
  - maze30: perfect maze (only one path)
  - rooms40: 4 rooms with narrow corridors
  - random50: random obstacles
"""

import hashlib
import json
import os
import random
import sys
from collections import deque


def _bfs_cost(h, w, grid, start, goal):
    if start == goal:
        return 0
    if grid[start[0]][start[1]] == 1 or grid[goal[0]][goal[1]] == 1:
        return -1
    visited = [[False] * w for _ in range(h)]
    visited[start[0]][start[1]] = True
    q = deque([(start, 0)])
    while q:
        (r, c), d = q.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == 0:
                if (nr, nc) == goal:
                    return d + 1
                visited[nr][nc] = True
                q.append(((nr, nc), d + 1))
    return -1


def _gen_open(h, w, rng, density=0.05):
    return [[1 if rng.random() < density else 0 for _ in range(w)] for _ in range(h)]


def _gen_maze(h, w, rng):
    """Recursive backtracker maze."""
    grid = [[1] * w for _ in range(h)]
    visited = [[False] * w for _ in range(h)]
    stack = [(1, 1)]
    visited[1][1] = True
    grid[1][1] = 0
    while stack:
        r, c = stack[-1]
        neighbors = []
        for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            nr, nc = r + dr, c + dc
            if 0 < nr < h - 1 and 0 < nc < w - 1 and not visited[nr][nc]:
                neighbors.append((nr, nc))
        if neighbors:
            nr, nc = rng.choice(neighbors)
            grid[nr][nc] = 0
            grid[(r + nr) // 2][(c + nc) // 2] = 0
            visited[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()
    return grid


def _gen_rooms(h, w, rng):
    grid = [[1] * w for _ in range(h)]
    # 4 rooms with random positions
    rooms = []
    for _ in range(4):
        rh = rng.randint(5, 9)
        rw = rng.randint(5, 9)
        rr = rng.randint(1, h - rh - 1)
        rc = rng.randint(1, w - rw - 1)
        rooms.append((rr, rc, rh, rw))
        for dr in range(rr, rr + rh):
            for dc in range(rc, rc + rw):
                grid[dr][dc] = 0
    # Connect rooms with narrow corridors
    for i in range(len(rooms) - 1):
        r1, c1, h1, w1 = rooms[i]
        r2, c2, h2, w2 = rooms[i + 1]
        cr = (r1 + h1 // 2) % h
        cc = (c2 + w2 // 2) % w
        for dr in range(min(cr, r2 + h2 // 2), max(cr, r2 + h2 // 2) + 1):
            if 0 <= dr < h:
                grid[dr][cc] = 0
    return grid


def _gen_random(h, w, rng, density=0.3):
    return [[1 if rng.random() < density else 0 for _ in range(w)] for _ in range(h)]


def _corners(h, w):
    return [(0, 0), (0, w - 1), (h - 1, 0), (h - 1, w - 1)]


SPECS = [
    ("open20",   20, _gen_open,    {"density": 0.05}),
    ("maze30",   30, _gen_maze,    {}),
    ("rooms40",  40, _gen_rooms,   {}),
    ("random50", 50, _gen_random,  {"density": 0.3}),
    ("open100",  100, _gen_open,   {"density": 0.1}),
]


def main():
    out_dir = os.path.abspath(sys.argv[1]) if len(sys.argv) >= 2 \
        else os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    os.makedirs(out_dir, exist_ok=True)
    inst_dir = os.path.join(out_dir, "instances")
    os.makedirs(inst_dir, exist_ok=True)
    sources = []
    optima = {}
    for i, (name, n, gen, params) in enumerate(SPECS):
        rng = random.Random(20260702 + i)
        grid = gen(n, n, rng, **params)
        start, goal = (0, 0), (n - 1, n - 1)
        # Ensure start/goal are open
        grid[start[0]][start[1]] = 0
        grid[goal[0]][goal[1]] = 0
        opt = _bfs_cost(n, n, grid, start, goal)
        inst = {"name": name, "height": n, "width": n, "grid": grid,
                "start": list(start), "goal": list(goal), "opt_cost": opt}
        path = os.path.join(inst_dir, f"{name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(inst, f, ensure_ascii=False)
        sha = hashlib.sha256(open(path, "rb").read()).hexdigest()
        sources.append((name, sha, n))
        optima[name] = opt
        print(f"  {name}: {n}x{n} opt_cost={opt}")
    with open(os.path.join(out_dir, "optima.json"), "w", encoding="utf-8") as f:
        json.dump(optima, f, indent=1, ensure_ascii=False)
    src_path = os.path.join(out_dir, "SOURCE.txt")
    with open(src_path, "w", encoding="utf-8") as f:
        f.write("Provenance: SYNTHETIC 2D grid path-planning instances\n")
        f.write("Generator: genopt_factory/tools/fetch_pathplan_synth.py\n")
        f.write("Master seed: 20260702 + i (fixed across runs)\n")
        f.write("Optima: BFS exact (4-connected unit cost)\n\n")
        for name, sha, n in sources:
            f.write(f"{name}\t{n}x{n}\tsha256={sha}\n")
    print(f"wrote {len(SPECS)} grid instances to {out_dir}")


if __name__ == "__main__":
    main()