"""lens_pair_aberration_v1_001 · baseline starting point.

Paraxial double thin-lens placement (sub-optimal: ignores off-axis aberration).
Candidate edits only this file. Verifier imports `align_lens_pair`.
"""

from __future__ import annotations


def align_lens_pair(
    source: dict,
    lens_a: dict,
    lens_b: dict,
    target_z: float,
    n_rays: int = 64,
) -> dict:
    """Compute 6-DOF placement for a two-lens optical bench.

    Pure paraxial baseline — places each lens exactly at its paraxial image
    distance, ignores off-axis spherical + coma aberration.

    Returns dict with keys: z_a, z_b, x_a, x_b, y_a, y_b.
    """
    # Source object distance (relative to lens A axial position z_a)
    # Object distance from source.z (source at z=0 origin by convention) to
    # lens A axial position:
    u_a = source["z"]  # object distance magnitude, positive = upstream of lens A
    f_a = lens_a["f"]
    # Paraxial: 1/v = 1/f - 1/u
    v_a = 1.0 / (1.0 / f_a - 1.0 / u_a) if u_a > 0 else f_a

    # First image plane (after lens A) — place lens B at distance v_a from
    # lens A so that the image forms at lens B's entrance.
    z_a = 0.0
    z_b = z_a + v_a

    # Find where lens B should send the bundle to target_z.
    # Object distance for lens B = z_b - intermediate_image = ?
    # In a thin doublet, lens B receives the converging ray bundle from lens A
    # and re-collimates/focuses to the target.
    f_b = lens_b["f"]
    # After lens A, rays converge at z = v_a (intermediate image). Treat
    # this as the "object" for lens B at distance u_b = v_a from lens B.
    u_b = v_a
    # Paraxial lens B → 1/target_offset_from_lens_b = 1/f_b - 1/u_b
    v_b = 1.0 / (1.0 / f_b - 1.0 / (u_b if u_b != 0 else 1e-9)) if u_b != 0 else f_b
    # The target plane sits at target_z. Distance from lens B to target =
    # target_z - z_b. If v_b differs, scale z_b to match.
    desired_b_to_target = target_z - z_b
    # Parafocal solution: simply place z_b such that v_b matches the target gap.
    z_b = target_z - v_b

    # Lateral offsets — paraxial baseline assumes on-axis (no tilt/decenter).
    x_a = x_b = 0.0
    y_a = y_b = 0.0

    # Constraint: z_b > z_a + 1e-6
    if z_b <= z_a + 1e-6:
        z_b = z_a + f_b + 1e-3

    # Clip to evaluation window
    z_a = float(max(-50.0, min(250.0, z_a)))
    z_b = float(max(-50.0, min(250.0, z_b)))
    x_a = float(max(-50.0, min(50.0, x_a)))
    x_b = float(max(-50.0, min(50.0, x_b)))
    y_a = float(max(-50.0, min(50.0, y_a)))
    y_b = float(max(-50.0, min(50.0, y_b)))

    return {
        "z_a": z_a,
        "z_b": z_b,
        "x_a": x_a,
        "x_b": x_b,
        "y_a": y_a,
        "y_b": y_b,
    }
