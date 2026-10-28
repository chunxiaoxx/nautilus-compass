"""Task pricing - cost calculation for all task types."""
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Prices in RMB (yuan). 1 credit = 1 RMB
# Market rate ~3000 RMB/task. We price at 30-50% for competitive advantage.
TASK_PRICES: Dict[str, float] = {
    # Academic tasks (market: 1000-5000 RMB, ours: 30-50%)
    "general_computation": 200,
    "curve_fitting": 500,
    "ode_simulation": 800,
    "pde_simulation": 1000,
    "monte_carlo": 500,
    "statistical_analysis": 500,
    "ml_training": 1200,
    "data_visualization": 300,
    "physics_simulation": 1000,
    "jc_constitutive": 1500,
    "thmc_coupling": 2500,

    # Labeling tasks (per item) - market: 0.5-5 RMB/item, ours: ~30%
    "sentiment": 0.15,
    "classification": 0.25,
    "entity_extraction": 0.50,
    "intent": 0.30,
    "spam": 0.15,
    "toxicity": 0.25,
    "object_detection": 1.00,
    "scene_classification": 0.80,
    "action_recognition": 1.00,
    "safety_critical": 1.50,
    "environmental": 0.50,

    # Simulation tasks (market: 2000-8000 RMB, ours: 30-50%)
    "physics_simulation_sim": 1000,
    "motion_planning": 1500,
    "dynamics_simulation": 1200,
    "scenario_generation": 800,
    "collision_detection": 1000,
    "environment_simulation": 800,
    "sensor_simulation": 1000,
}

_LABELING_TYPES = frozenset({
    "sentiment", "classification", "entity_extraction", "intent",
    "spam", "toxicity", "object_detection", "scene_classification",
    "action_recognition", "safety_critical", "environmental",
})

_SIMULATION_TYPES = frozenset({
    "physics_simulation_sim", "motion_planning", "dynamics_simulation",
    "scenario_generation", "collision_detection", "environment_simulation",
    "sensor_simulation",
})


def get_task_price(task_type: str, num_items: int = 1) -> float:
    """Get price for a task. For labeling, multiply by num_items."""
    base_price = TASK_PRICES.get(task_type, 500.0)  # default 500 RMB
    if task_type in _LABELING_TYPES:
        return round(base_price * num_items, 2)
    return base_price


def get_price_list() -> dict:
    """Return full price list grouped by category."""
    academic = {
        k: v for k, v in TASK_PRICES.items()
        if k not in _LABELING_TYPES and k not in _SIMULATION_TYPES
    }
    labeling = {k: v for k, v in TASK_PRICES.items() if k in _LABELING_TYPES}
    simulation = {k: v for k, v in TASK_PRICES.items() if k in _SIMULATION_TYPES}
    return {
        "academic": academic,
        "labeling_per_item": labeling,
        "simulation": simulation,
        "currency": "RMB",
    }
