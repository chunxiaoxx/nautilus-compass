#!/usr/bin/env python3
"""Independent recheck of flywheel hand-geometry findings (palm triple + thumb).

Input: any (N, 301) states.npy conversion artifact, right-hand = cols 154:301.
Expected values from _INBOUND_FROM_FLYWHEEL_20260905_hand_geometry_findings.md:
  palm_len median ~0.022 · bow ~0.035 · sin_ang ~0.44 · thumb_d min > 0.08

Usage: python tools/hand_geometry_recheck.py <states.npy>
"""
from __future__ import annotations

import sys

import numpy as np

EXPECT = {"palm_len": 0.022, "bow": 0.035, "sin_ang": 0.44}


def main() -> int:
    if len(sys.argv) < 2:
        sys.exit("usage: hand_geometry_recheck.py <states.npy>")
    s = np.load(sys.argv[1])
    if s.ndim != 2 or s.shape[1] < 301:
        sys.exit(f"unexpected shape {s.shape} — need (N, 301) intermediate artifact, "
                 "not the (N, 7) final ego2libero_states (hand pose already collapsed)")
    N = s.shape[0]
    hand = s[:, 154:301].reshape(N, 21, 7)[..., :3]
    palm_vec = hand[:, [16, 17, 18, 19]].mean(1) - hand[:, 20]
    palm_len = np.linalg.norm(palm_vec, axis=-1)
    bow = np.linalg.norm(hand[:, 16] - hand[:, 19], axis=-1)
    sin_ang = (np.linalg.norm(np.cross(hand[:, 16] - hand[:, 19], palm_vec), axis=-1)
               / (bow * np.linalg.norm(palm_vec, axis=-1) + 1e-9))
    thumb_d = np.linalg.norm(hand[:, 0] - hand[:, 4], axis=-1)
    tip_mcp = np.linalg.norm(hand[:, 0] - hand[:, 3], axis=-1)
    print(f"file={sys.argv[1]} · N={N}")
    print(f"palm_len median = {np.median(palm_len):.4f}  (expect ~{EXPECT['palm_len']})")
    print(f"bow      median = {np.median(bow):.4f}  (expect ~{EXPECT['bow']})")
    print(f"sin_ang  median = {np.median(sin_ang):.4f}  (expect ~{EXPECT['sin_ang']})")
    print(f"thumb_d  min={thumb_d.min():.4f} max={thumb_d.max():.4f}  (expect min>0.08)")
    print(f"thumb TIP-MCP range = {tip_mcp.min():.3f}-{tip_mcp.max():.3f}  (letter: frozen 0.075-0.087)")
    ok = (abs(np.median(palm_len) - EXPECT["palm_len"]) < 0.01
          and abs(np.median(bow) - EXPECT["bow"]) < 0.01
          and abs(np.median(sin_ang) - EXPECT["sin_ang"]) < 0.1
          and thumb_d.min() > 0.08)
    print("\nVERDICT:", "agree — findings reproduce" if ok else "DISAGREE — signed receipt to flywheel")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
