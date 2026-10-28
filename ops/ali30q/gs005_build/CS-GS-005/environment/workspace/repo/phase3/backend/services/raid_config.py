"""
Raid Harness Configuration Loader — reads YAML config with hot-reload support.
"""
import logging
import os
import time
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "config", "raid_harness.yaml"
)

_config_cache: Optional[Dict[str, Any]] = None
_config_mtime: float = 0


def load_raid_config(force_reload: bool = False) -> Dict[str, Any]:
    """Load raid harness config from YAML. Hot-reloads if file changed."""
    global _config_cache, _config_mtime

    try:
        mtime = os.path.getmtime(CONFIG_PATH)
    except OSError:
        logger.warning("raid_config: %s not found, using defaults", CONFIG_PATH)
        return _default_config()

    if _config_cache is not None and not force_reload and mtime <= _config_mtime:
        return _config_cache

    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            _config_cache = yaml.safe_load(f)
            _config_mtime = mtime
            logger.info("raid_config: loaded from %s", CONFIG_PATH)
            return _config_cache
    except Exception as e:
        logger.error("raid_config: failed to load %s: %s", CONFIG_PATH, e)
        return _config_cache or _default_config()


def get_raid_level_config(level: int) -> Dict[str, Any]:
    """Get configuration for a specific Raid level."""
    config = load_raid_config()
    levels = config.get("raid_levels", {})
    return levels.get(level, levels.get(config.get("default_raid_level", 3), {}))


def get_raid_level_for_task_type(task_type: str) -> int:
    """Get the recommended Raid level for a given task type."""
    config = load_raid_config()
    mapping = config.get("task_type_mapping", {})
    return mapping.get(task_type, config.get("default_raid_level", 3))


def get_complexity_raid_mapping() -> Dict[str, int]:
    """Get the complexity -> RAID level mapping (used by task_router)."""
    config = load_raid_config()
    return config.get("complexity_raid_mapping", {
        "simple": 1, "moderate": 2, "complex": 3, "critical": 5,
    })


def get_resource_governor_defaults() -> Dict[str, int]:
    """Get the resource governor's default complexity -> RAID mapping."""
    config = load_raid_config()
    return config.get("resource_governor_defaults", {
        "simple": 0, "moderate": 2, "complex": 3, "critical": 3,
    })


def get_engine_params(level: int) -> Dict[str, Any]:
    """Get raid engine execution parameters for a given level.

    Returns a dict with keys like agent_count, quality_threshold,
    max_rounds, expert_count, consensus_threshold, parallel_count, etc.
    Merges level-specific values with sensible defaults.
    """
    cfg = get_raid_level_config(level)
    defaults = {
        "agent_count": {1: 1, 2: 1, 3: 3, 5: 5}.get(level, 1),
        "quality_threshold": 0.8,
        "max_rounds": 3,
        "expert_count": 5,
        "consensus_threshold": 4,
        "parallel_count": cfg.get("agent_count", 3),
    }
    # Overlay YAML values on top of defaults
    for key in defaults:
        if key in cfg:
            defaults[key] = cfg[key]
    return defaults


def _default_config() -> Dict[str, Any]:
    """Fallback defaults if YAML not available."""
    return {
        "default_raid_level": 3,
        "raid_levels": {
            1: {"agent_count": 1, "parallel": False, "judge_enabled": False},
            2: {"agent_count": 2, "parallel": True, "judge_enabled": True, "max_rounds": 3, "quality_threshold": 0.8},
            3: {"agent_count": 3, "parallel": True, "judge_enabled": True},
            5: {"agent_count": 5, "parallel": True, "judge_enabled": True, "expert_count": 5, "consensus_threshold": 4},
        },
        "complexity_raid_mapping": {
            "simple": 1, "moderate": 2, "complex": 3, "critical": 5,
        },
        "resource_governor_defaults": {
            "simple": 0, "moderate": 2, "complex": 3, "critical": 3,
        },
        "task_type_mapping": {},
    }
