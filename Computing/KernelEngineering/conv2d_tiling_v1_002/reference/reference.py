"""Naive 7-loop 2D convolution reference oracle (read-only)."""

from __future__ import annotations


def conv2d_naive(input, kernel, stride=1, padding=0):
    C_in = len(input)
    H = len(input[0])
    W = len(input[0][0]) if H > 0 else 0
    C_out = len(kernel)
    K_h = len(kernel[0][0])
    K_w = len(kernel[0][0][0]) if K_h > 0 else 0

    H_p = H + 2 * padding
    W_p = W + 2 * padding
    padded = []
    for c in range(C_in):
        rows = [[0.0] * W_p for _ in range(H_p)]
        for y in range(H):
            for x in range(W):
                rows[padding + y][padding + x] = input[c][y][x]
        padded.append(rows)

    H_out = (H_p - K_h) // stride + 1
    W_out = (W_p - K_w) // stride + 1

    output = [[[0.0] * W_out for _ in range(H_out)] for _ in range(C_out)]

    for out_c in range(C_out):
        for in_c in range(C_in):
            k_ch = kernel[out_c][in_c]
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

    return output
