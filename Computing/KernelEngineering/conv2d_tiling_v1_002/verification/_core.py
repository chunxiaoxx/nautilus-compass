"""stdlib-only verifier primitives shared with tiled_matmul_v1_001 schema."""

from __future__ import annotations



def max_abs_diff_3d(C, C_ref):
    """Element-wise max absolute difference for 3D tensors (C_out, H, W)."""
    dmax = 0.0
    for ci in range(len(C)):
        Ci = C[ci]
        Cref_i = C_ref[ci]
        for y in range(len(Ci)):
            Ci_y = Ci[y]
            Cref_iy = Cref_i[y]
            for x in range(len(Ci_y)):
                d = abs(Ci_y[x] - Cref_iy[x])
                if d > dmax:
                    dmax = d
    return dmax


def gflops_conv2d(C_out, C_in, K_h, K_w, H_out, W_out, elapsed_s):
    """FLOPs for 2D conv: 2 * C_out * C_in * K_h * K_w * H_out * W_out."""
    if elapsed_s <= 0:
        return 0.0
    return float(2.0 * C_out * C_in * K_h * K_w * H_out * W_out) / float(elapsed_s) / 1e9


def import_lock_no_numpy(import_func, module_name):
    """Import candidate under import-lock that blocks numpy/scipy/numba/etc.

    Reused from tiled_matmul_v1_001 schema.
    """
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
