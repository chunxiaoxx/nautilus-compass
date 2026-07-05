"""conv2d_tiling_v1_002 · baseline starting point.

Pure stdlib naive 7-loop nested iteration. Verifier imports
`conv2d`. Candidate edits only this file."""

from __future__ import annotations

import time


def conv2d(input, kernel, stride=1, padding=0):
    """Naive O(C_out * C_in * H_out * W_out * K_h * K_w) 2D convolution.

    input:  list of C_in matrices, each H x W (lists of lists of floats)
    kernel: list of C_out tensors, each C_in matrices, each K_h x K_w
    returns dict with keys "output" (list of C_out matrices, each H_out x W_out)
    and "elapsed_s" (float).
    """
    C_in = len(input)
    assert C_in > 0, "input must have at least one channel"
    H = len(input[0])
    W = len(input[0][0]) if H > 0 else 0

    C_out = len(kernel)
    assert C_out > 0 and len(kernel[0]) > 0, "kernel must be non-empty"
    K_h = len(kernel[0][0])
    K_w = len(kernel[0][0][0]) if K_h > 0 else 0

    # Pad input along H and W
    H_p = H + 2 * padding
    W_p = W + 2 * padding
    # Build padded input as list of zero-filled lists with original copied in middle
    padded = []
    for c in range(C_in):
        rows = [[0.0] * W_p for _ in range(H_p)]
        for y in range(H):
            for x in range(W):
                rows[padding + y][padding + x] = input[c][y][x]
        padded.append(rows)

    H_out = (H_p - K_h) // stride + 1
    W_out = (W_p - K_w) // stride + 1

    t0 = time.perf_counter()
    output = [[[0.0] * W_out for _ in range(H_out)] for _ in range(C_out)]

    for out_c in range(C_out):
        for in_c in range(C_in):
            k_ch = kernel[out_c][in_c]   # K_h × K_w matrix
            p_ch = padded[in_c]
            for oy in range(H_out):
                for ox in range(W_out):
                    acc = 0.0
                    for ky in range(K_h):
                        for kx in range(K_w):
                            iy = oy * stride + ky
                            ix = ox * stride + kx
                            acc += p_ch[iy][ix] * k_ch[ky][kx]
                    output[out_c][oy][ox] = acc
    elapsed = time.perf_counter() - t0
    return {"output": output, "elapsed_s": float(elapsed)}
