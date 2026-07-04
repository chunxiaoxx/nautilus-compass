"""stdlib-only verifier primitives."""

from __future__ import annotations

import time


def max_abs_diff(C, C_ref):
    """Element-wise max absolute difference (matches shape)."""
    dmax = 0.0
    M = len(C)
    for i in range(M):
        Ci = C[i]
        Cref_i = C_ref[i]
        N = len(Ci)
        for j in range(N):
            d = abs(Ci[j] - Cref_i[j])
            if d > dmax:
                dmax = d
    return dmax


def gflops(M, K, N, elapsed_s):
    if elapsed_s <= 0:
        return 0.0
    return float(2.0 * M * K * N) / float(elapsed_s) / 1e9


def import_lock_no_numpy(import_func, module_name):
    """Import candidate under import-lock that blocks numpy import."""
    import sys
    import importlib.util

    blocked = {"numpy", "scipy", "numba", "torch", "jax", "tensorflow"}

    class BlockedFinder:
        def find_spec(self, fullname, path, target=None):
            if fullname.split(".")[0] in blocked:
                raise ImportError(
                    f"BLOCKED: {module_name} is not allowed to import {fullname}"
                )
            return None

    sys.meta_path.insert(0, BlockedFinder())
    try:
        spec = importlib.util.spec_from_file_location(module_name, import_func)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.meta_path = [m for m in sys.meta_path if not isinstance(m, BlockedFinder)]
