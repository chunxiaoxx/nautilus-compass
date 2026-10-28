"""FIFO cache — the weak baseline. Pure stdlib, deterministic.

Eviction policy: when put() brings cache over capacity, evict the OLDEST-inserted
entry (insertion order, not access order). This is the textbook O(1) FIFO.

GPT5.5 N=3 should easily beat this by switching to LRU, 2Q, ARC, or TinyLFU.
"""

from collections import OrderedDict


def run_cache(instance: dict) -> dict:
    cap = instance["capacity"]
    cache = OrderedDict()        # key -> value (insertion order)
    misses = 0
    total_gets = 0
    for op in instance["ops"]:
        kind = op[0]
        if kind == "get":
            key = op[1]
            total_gets += 1
            if key in cache:
                # FIFO does NOT update recency on read.
                _ = cache[key]
            else:
                misses += 1
        elif kind == "put":
            key, value = op[1], op[2]
            if key in cache:
                cache[key] = value
                # FIFO: do NOT move to end on update either (strict FIFO).
            else:
                cache[key] = value
                if len(cache) > cap:
                    cache.popitem(last=False)   # pop oldest
    return {"misses": misses,
            "miss_rate": (misses / total_gets) if total_gets else 0.0}