"""
Simulation templates for brain-body integration training tasks.

Each template provides a system prompt and metadata that guide the
CodeExecutor when generating simulation code.  Templates are designed
to work within the existing Docker scientific image (numpy, scipy,
matplotlib available).
"""
from typing import Any, Dict

SIMULATION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "physics_simulation": {
        "system_prompt": (
            "Expert in computational physics simulation. Use numpy/scipy "
            "for numerical integration. Model physical systems with proper "
            "units, initial/boundary conditions, and energy conservation "
            "checks. Output time-series data as JSON arrays."
        ),
        "hint": "Run a physics simulation with numerical integration.",
        "required_packages": ["numpy", "scipy", "matplotlib"],
        "default_parameters": {
            "dt": 0.01,
            "duration": 10.0,
        },
    },
    "motion_planning": {
        "system_prompt": (
            "Expert in robot motion planning. Implement RRT, A*, or "
            "potential field methods. Output: waypoints, velocities, "
            "joint angles. Validate collision-free paths. Use numpy for "
            "geometry and scipy.spatial for spatial queries."
        ),
        "hint": "Generate a collision-free motion plan.",
        "required_packages": ["numpy", "scipy"],
        "default_parameters": {
            "max_iterations": 5000,
            "step_size": 0.1,
        },
    },
    "sensor_simulation": {
        "system_prompt": (
            "Expert in sensor data simulation. Generate realistic synthetic "
            "sensor readings including camera images (as numpy arrays), "
            "LiDAR point clouds, and IMU data. Add configurable noise "
            "models (Gaussian, salt-and-pepper, drift). Output structured "
            "JSON with timestamps and sensor frames."
        ),
        "hint": "Generate synthetic sensor data with noise models.",
        "required_packages": ["numpy", "scipy"],
        "default_parameters": {
            "frequency_hz": 30,
            "noise_stddev": 0.01,
        },
    },
    "scenario_generation": {
        "system_prompt": (
            "Expert in driving/robotics scenario generation. Create "
            "diverse traffic or task scenarios with varying: weather "
            "conditions, road/terrain types, actor behaviors, edge cases. "
            "Output structured scenario data as JSON including actor "
            "positions, velocities, and event timelines."
        ),
        "hint": "Generate diverse simulation scenarios.",
        "required_packages": ["numpy"],
        "default_parameters": {
            "num_actors": 5,
            "duration": 30.0,
        },
    },
    "collision_detection": {
        "system_prompt": (
            "Expert in computational geometry and collision detection. "
            "Implement GJK, SAT, or bounding volume hierarchy methods "
            "to detect collisions between rigid bodies. Output collision "
            "reports with contact points, penetration depth, and normals."
        ),
        "hint": "Detect collisions between geometric bodies.",
        "required_packages": ["numpy", "scipy"],
        "default_parameters": {
            "tolerance": 1e-6,
        },
    },
    "dynamics_simulation": {
        "system_prompt": (
            "Expert in vehicle/robot dynamics. Model rigid body dynamics, "
            "contact forces, friction (Coulomb model). Use scipy.integrate "
            "for time integration (RK45). Output state trajectories "
            "(position, velocity, acceleration) as structured JSON."
        ),
        "hint": "Simulate rigid body or vehicle dynamics.",
        "required_packages": ["numpy", "scipy", "matplotlib"],
        "default_parameters": {
            "dt": 0.001,
            "duration": 5.0,
            "gravity": 9.81,
        },
    },
    "environment_simulation": {
        "system_prompt": (
            "Expert in environment simulation for embodied AI. Model "
            "weather effects (rain, fog, wind), terrain properties "
            "(friction coefficients, slope), and lighting conditions. "
            "Output environment state timelines as JSON suitable for "
            "Sim2Real transfer pipelines."
        ),
        "hint": "Simulate environmental conditions for training.",
        "required_packages": ["numpy"],
        "default_parameters": {
            "duration": 60.0,
            "update_interval": 1.0,
        },
    },
}


def get_template(simulation_type: str) -> Dict[str, Any]:
    """Return the template for *simulation_type*, or a sensible default."""
    return SIMULATION_TEMPLATES.get(simulation_type, {
        "system_prompt": (
            "Expert in scientific simulation. Use numpy and scipy to "
            "implement the requested simulation. Output results as JSON."
        ),
        "hint": "Run a scientific simulation.",
        "required_packages": ["numpy", "scipy"],
        "default_parameters": {},
    })
