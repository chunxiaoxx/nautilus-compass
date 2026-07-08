"""stdlib-only verifier primitives shared schema with tiled_matmul / conv2d_tiling."""

from __future__ import annotations

import importlib.util
import sys


def max_abs_diff_2d(A, B):
    """Element-wise max abs diff for 2D lists (N x D)."""
    dmax = 0.0
    N = len(A)
    for i in range(N):
        Ai = A[i]
        Bi = B[i]
        D = len(Ai)
        for j in range(D):
            d = abs(Ai[j] - Bi[j])
            if d > dmax:
                dmax = d
    return dmax


def gflops_rmsnorm(N, D, elapsed_s):
    """RMSNorm flops: per element 1 mul + 1 division = 2 flops."""
    if elapsed_s <= 0:
        return 0.0
    return float(2.0 * N * D) / float(elapsed_s) / 1e9


def import_lock_no_numpy(import_func, module_name):
    """Import candidate under import-lock that blocks numpy/scipy/numba/torch/jax/tensorflow."""
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
