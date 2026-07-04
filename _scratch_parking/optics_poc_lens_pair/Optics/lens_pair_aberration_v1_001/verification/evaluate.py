"""Honest geometric ray-tracing verifier · read-only.

Imports `align_lens_pair` from `baseline/init.py`, ray-traces through both
lenses, measures RMS spot radius on the target focal plane.
"""

from __future__ import annotations

import argparse
import json
import importlib.util
import sys
from pathlib import Path

import numpy as np

# Local ray-tracer primitives (verifier owns its own math)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _core import thin_lens_refract, propagate_to_z, rms_spot_radius  # noqa: E402

TARGET_RMS_ORACLE = 1.000  # mm · optimistic convergence bound

# Geometry setup
N_RAYS = 64
APERTURE_FRACTION = 0.85  # rays fill 85% of lens clear aperture


def make_ray_fan(source: dict, lens_a: dict):
    """Build off-axis ray fan launched from the source point.

    64 rays = 8 concentric rings × 8 azimuthal samples · uniform area weighting.
    """
    src_x = source.get("dy", 0.0)
    src_y = source.get("dz", 0.0)
    src_z = source["z"]

    aperture = lens_a["aperture_radius"]
    n_rings = 8
    n_az = 8
    # Concentric rings with sqrt(r) spacing for uniform area distribution
    ring_idx = np.arange(1, n_rings + 1)
    r_max = aperture * APERTURE_FRACTION
    ring_radii = r_max * np.sqrt(ring_idx / n_rings)
    az_grid = np.linspace(0.0, 2 * np.pi, n_az, endpoint=False)
    r_grid, az_grid = np.meshgrid(ring_radii, az_grid, indexing="ij")
    r_flat = r_grid.flatten()  # 64 entries
    az_flat = az_grid.flatten()

    x0 = src_x + r_flat * np.cos(az_flat)
    y0 = src_y + r_flat * np.sin(az_flat)
    z0 = np.full_like(x0, src_z)

    # Initial direction: aimed from source point toward each aperture sample.
    # The "current z plane" we are headed to is lens A (axial coordinate 0
    # in the local coordinate system; baseline API will offset later).
    dir_x = -x0 - 0 * src_x
    dir_y = -y0 - 0 * src_y
    dir_z = np.full_like(x0, -src_z)  # downstream = positive z; here we use
    # positive z = downstream convention. Use magnitude only for direction.
    dirs = np.stack([dir_x, dir_y, dir_z], axis=1).astype(float)
    norms = np.linalg.norm(dirs, axis=1, keepdims=True)
    dirs = dirs / np.maximum(norms, 1e-12)
    pts = np.stack([x0, y0, z0], axis=1).astype(float)
    return pts, dirs


def evaluate_instance(instance: dict) -> dict:
    source = instance["source"]
    lens_a = instance["lens_a"]
    lens_b = instance["lens_b"]
    target_z = instance["target_z"]

    spec = importlib.util.spec_from_file_location("candidate", _CANDIDATE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    placement = mod.align_lens_pair(source, lens_a, lens_b, target_z, n_rays=N_RAYS)

    # Hard constraint: z_b > z_a + 1e-6
    if not (placement["z_b"] > placement["z_a"] + 1e-6):
        return {
            "instance_id": instance["instance_id"],
            "valid": 0,
            "achieved_rms": None,
            "score": 0.0,
            "error": "constraint z_b > z_a violated",
        }

    pts, dirs = make_ray_fan(source, lens_a)

    # Propagate to lens A plane (axial z = placement["z_a"])
    pts = propagate_to_z(pts, dirs, placement["z_a"], source["z"])

    # Apply lateral offset for lens A (decentering)
    pts[:, 0] -= placement["x_a"]
    pts[:, 1] -= placement["y_a"]

    # Refract through lens A
    dirs = thin_lens_refract(pts, dirs, 0.0, lens_a["f"])

    # Propagate to lens B plane
    pts = propagate_to_z(pts, dirs, placement["z_b"], placement["z_a"])

    # Apply lateral offset for lens B
    pts[:, 0] -= placement["x_b"]
    pts[:, 1] -= placement["y_b"]

    # Refract through lens B
    dirs = thin_lens_refract(pts, dirs, 0.0, lens_b["f"])

    # Propagate to target plane
    pts = propagate_to_z(pts, dirs, target_z, placement["z_b"])

    rms = rms_spot_radius(pts, np.array([0.0, 0.0]))

    score = min(100.0, 100.0 * TARGET_RMS_ORACLE / max(rms, 1e-9))
    return {
        "instance_id": instance["instance_id"],
        "valid": 1,
        "achieved_rms": float(rms),
        "score": float(score),
    }


def main():
    global _CANDIDATE_PATH
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--instances", default=str(Path(__file__).parent.parent / "data" / "instances.json"))
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    _CANDIDATE_PATH = str(Path(args.candidate).resolve())

    with open(args.instances, "r", encoding="utf-8") as f:
        instances = json.load(f)

    per_instance = [evaluate_instance(i) for i in instances]
    valid_flags = [r["valid"] for r in per_instance]
    scores = [r["score"] for r in per_instance]
    combined = float(np.mean(scores)) if all(valid_flags) else 0.0
    valid = 1 if all(valid_flags) else 0

    metrics = {
        "task_id": "lens_pair_aberration_v1_001",
        "domain": "Optics and Communication Systems",
        "sub_domain": "Optics",
        "valid": valid,
        "combined_score": combined,
        "per_instance": per_instance,
        "n_instances": len(instances),
        "baseline_failures": sum(1 for f in valid_flags if f == 0),
        "target_rms_oracle": TARGET_RMS_ORACLE,
    }

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"valid={valid} combined_score={combined:.4f} instances={len(instances)}")
    for r in per_instance:
        print(
            f"  {r['instance_id']}: valid={r['valid']} "
            f"rms={r.get('achieved_rms')} score={r.get('score', 0.0):.4f}"
        )


if __name__ == "__main__":
    main()
