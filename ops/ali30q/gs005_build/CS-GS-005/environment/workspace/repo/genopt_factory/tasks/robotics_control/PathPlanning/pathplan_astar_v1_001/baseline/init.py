"""BFS 2D grid path planning — weak baseline.

4-connected, unit cost per move.  Pure stdlib, deterministic.

GPT5.5 N=3 should easily beat this on time (A* with Manhattan heuristic
or JPS for large open grids) and match on optimality.
"""

from collections import deque


def find_path(instance: dict) -> dict:
    h = instance["height"]
    w = instance["width"]
    grid = instance["grid"]
    sr, sc = instance["start"]
    gr, gc = instance["goal"]
    if (sr, sc) == (gr, gc):
        return {"path": [(sr, sc)], "cost": 0, "valid": True}
    if grid[sr][sc] == 1 or grid[gr][gc] == 1:
        return {"path": [], "cost": float("inf"), "valid": False}

    visited = [[False] * w for _ in range(h)]
    visited[sr][sc] = True
    q = deque([(sr, sc)])
    found = False
    max_iter = 200000  # safety cap: at 4-connected, this covers ~30s of pure Python
    iters = 0
    while q and iters < max_iter:
        iters += 1
        r, c = q.popleft()
        if (r, c) == (gr, gc):
            found = True
            break
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and not visited[nr][nc] and grid[nr][nc] == 0:
                visited[nr][nc] = True
                parent[nr][nc] = (r, c)
                q.append((nr, nc))

    if not found:
        return {"path": [], "cost": float("inf"), "valid": False}

    if parent[gr][gc] is None and (sr, sc) != (gr, gc):
        return {"path": [], "cost": float("inf"), "valid": False}

    path = []
    cur = (gr, gc)
    while cur is not None:
        path.append(cur)
        cur = parent[cur[0]][cur[1]]
    path.reverse()
    return {"path": path, "cost": len(path) - 1, "valid": True}