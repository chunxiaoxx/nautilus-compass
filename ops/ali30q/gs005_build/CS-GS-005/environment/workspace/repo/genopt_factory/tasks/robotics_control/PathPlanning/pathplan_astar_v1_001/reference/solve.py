"""A* with Manhattan distance heuristic for 2D grid path planning.

Pure stdlib, deterministic. Target: same optimal cost as BFS, much faster on
large open grids (heuristic guides search).

Uses a binary heap for the open set.
"""

import heapq


def _heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


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

    open_heap = []
    heapq.heappush(open_heap, (0 + _heuristic((sr, sc), (gr, gc)), 0, (sr, sc)))
    g_score = {(sr, sc): 0}
    parent = {(sr, sc): None}
    closed = set()
    while open_heap:
        f, g, cur = heapq.heappop(open_heap)
        if cur in closed:
            continue
        if cur == (gr, gc):
            path = []
            while cur is not None:
                path.append(cur)
                cur = parent[cur]
            path.reverse()
            return {"path": path, "cost": len(path) - 1, "valid": True}
        closed.add(cur)
        r, c = cur
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 0:
                ng = g + 1
                if (nr, nc) not in g_score or ng < g_score[(nr, nc)]:
                    g_score[(nr, nc)] = ng
                    parent[(nr, nc)] = cur
                    heapq.heappush(open_heap,
                                  (ng + _heuristic((nr, nc), (gr, gc)), ng, (nr, nc)))
    return {"path": [], "cost": float("inf"), "valid": False}