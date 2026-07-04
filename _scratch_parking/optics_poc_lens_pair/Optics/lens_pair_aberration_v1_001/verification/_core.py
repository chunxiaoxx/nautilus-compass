"""honest geometric ray-tracer primitives · read-only."""

from __future__ import annotations

import numpy as np


def thin_lens_refract(
    points: np.ndarray,  # (N, 3) at lens plane (z=0 slice)
    directions: np.ndarray,  # (N, 3) ray direction before lens
    z_local: float,  # not used (thin-lens at plane)
    lens_focal: float,
) -> np.ndarray:
    """Apply thin-lens refraction · Snell-equivalent paraxial in 3D.

    For each ray: the transverse position is unchanged; the direction's
    slope gets + r / f where r = sqrt(x^2 + y^2) + spherical correction.
    """
    x = points[:, 0]
    y = points[:, 1]
    r2 = x * x + y * y
    # Spherical aberration proxy: add radial quadratic
    spherical = 0.005 * r2 / (lens_focal * lens_focal)
    new_dirs = directions.copy()
    new_dirs[:, 0] += (x + spherical * x) / lens_focal
    new_dirs[:, 1] += (y + spherical * y) / lens_focal
    # Renormalize
    norms = np.linalg.norm(new_dirs, axis=1, keepdims=True)
    norms = np.where(norms < 1e-12, 1.0, norms)
    return new_dirs / norms


def propagate(points, directions, distance):
    return points + distance * directions


def propagate_to_z(points, directions, target_z, z_current):
    dz = target_z - z_current
    # Find t for each ray to reach target_z: points[:,2] + t*directions[:,2] = target_z
    dz_dir = directions[:, 2]
    t = np.where(np.abs(dz_dir) > 1e-9, dz / dz_dir, 1e9)
    return points + t[:, None] * directions


def rms_spot_radius(points_at_target, source_xy):
    """RMS radial distance from the bundle centroid."""
    cx = points_at_target[:, 0].mean()
    cy = points_at_target[:, 1].mean()
    dx = points_at_target[:, 0] - cx
    dy = points_at_target[:, 1] - cy
    return float(np.sqrt(np.mean(dx * dx + dy * dy)))
