"""ARC (Adaptive Replacement Cache) reference implementation, simplified.

ARC balances between recency (LRU) and frequency (LFU) via two ghost lists:
  T1: recency list (recently seen keys)
  T2: frequency list (seen ≥ 2x)
  B1: ghost recency (recently evicted from T1)
  B2: ghost frequency (recently evicted from T2)
The 'p' parameter adapts based on ghost hits, shifting between LRU and LFU.

This is a strong reference; GPT5.5 N=3 must implement a real LRU (or 2Q /
TinyLFU / ARC) to close the gap. Reference target ~80-95 / 100.
"""

from collections import OrderedDict


def run_cache(instance: dict) -> dict:
    cap = instance["capacity"]
    c = cap
    T1 = OrderedDict()  # recency
    T2 = OrderedDict()  # frequency
    B1 = OrderedDict()  # ghost recency (keys only)
    B2 = OrderedDict()  # ghost ghost (keys only)
    p = 0  # adaptation parameter in [0, c]
    misses = 0
    total_gets = 0

    def replace(key):
        nonlocal p
        # Decide which list to evict from.
        if T1 and ((key in B2 and len(T1) == p) or (len(T1) > p)):
            # evict LRU of T1
            old, _ = T1.popitem(last=False)
            B1[old] = True
            if len(B1) > c:
                B1.popitem(last=False)
        else:
            old, _ = T2.popitem(last=False)
            B2[old] = True
            if len(B2) > c:
                B2.popitem(last=False)

    def adjust_p(key):
        nonlocal p
        if key in B1:
            delta = max(1, len(B2) // max(1, len(B1)))
            p = min(c, p + delta)
        elif key in B2:
            delta = max(1, len(B1) // max(1, len(B2)))
            p = max(0, p - delta)

    for op in instance["ops"]:
        kind = op[0]
        if kind == "get":
            key = op[1]
            total_gets += 1
            if key in T1:
                # promote to T2 (frequency)
                v = T1.pop(key)
                T2[key] = v
            elif key in T2:
                T2.move_to_end(key)
                v = T2[key]
                _ = v
            else:
                misses += 1
                if key in B1:
                    adjust_p(key)
                    replace(key)
                    T1[key] = None
                elif key in B2:
                    adjust_p(key)
                    replace(key)
                    T2[key] = None
                else:
                    replace(key) if (len(T1) + len(T2)) >= c else None
                    T1[key] = None
        elif kind == "put":
            key, value = op[1], op[2]
            if key in T1:
                T1[key] = value
                v = T1.pop(key)
                T2[key] = v
                T2[key] = value
            elif key in T2:
                T2[key] = value
                T2.move_to_end(key)
            else:
                if key in B1:
                    adjust_p(key)
                    replace(key)
                    T1[key] = value
                    del B1[key]
                elif key in B2:
                    adjust_p(key)
                    replace(key)
                    T2[key] = value
                    del B2[key]
                else:
                    if (len(T1) + len(T2)) >= c:
                        replace(key)
                    T1[key] = value
    return {"misses": misses,
            "miss_rate": (misses / total_gets) if total_gets else 0.0}