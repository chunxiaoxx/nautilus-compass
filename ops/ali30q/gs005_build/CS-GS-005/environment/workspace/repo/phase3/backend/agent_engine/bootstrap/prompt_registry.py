"""
Prompt Registry - Versioned prompt management for A/B testing.

Each prompt has:
  - name: unique identifier (e.g., "labeling_system_v1")
  - template: the actual prompt text
  - version: auto-incremented
  - metrics: accuracy, latency, cost from evaluations
  - active: whether this is the current production prompt
"""
import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)

REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "prompt_versions.json")


@dataclass
class PromptVersion:
    name: str
    template: str
    version: int
    created_at: str = ""
    created_by: str = "human"  # "human" or "agent"
    active: bool = False
    metrics: Dict = field(default_factory=dict)
    # metrics: {"accuracy": 0.95, "avg_latency_s": 2.1, "eval_count": 10}

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class PromptRegistry:
    """
    Manages versioned prompts with A/B testing support.

    Usage:
        registry = PromptRegistry()
        registry.register("labeling_system", "You are a precise labeling AI...")
        registry.register("labeling_system", "Label each item accurately...", created_by="agent")

        active = registry.get_active("labeling_system")
        candidate = registry.get_latest("labeling_system")
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or REGISTRY_FILE
        self.prompts: Dict[str, List[PromptVersion]] = {}
        self._load()

    def register(
        self,
        name: str,
        template: str,
        created_by: str = "human",
        activate: bool = False,
    ) -> PromptVersion:
        """Register a new prompt version."""
        if name not in self.prompts:
            self.prompts[name] = []

        version = len(self.prompts[name]) + 1
        pv = PromptVersion(
            name=name,
            template=template,
            version=version,
            created_by=created_by,
            active=activate or version == 1,  # First version auto-activates
        )

        if activate:
            # Deactivate all others
            for existing in self.prompts[name]:
                existing.active = False

        self.prompts[name].append(pv)
        self._save()

        logger.info(f"Registered prompt {name} v{version} (by {created_by}, active={pv.active})")
        return pv

    def get_active(self, name: str) -> Optional[PromptVersion]:
        """Get the currently active prompt version."""
        versions = self.prompts.get(name, [])
        for v in reversed(versions):
            if v.active:
                return v
        return versions[-1] if versions else None

    def get_latest(self, name: str) -> Optional[PromptVersion]:
        """Get the most recent version (may not be active)."""
        versions = self.prompts.get(name, [])
        return versions[-1] if versions else None

    def get_version(self, name: str, version: int) -> Optional[PromptVersion]:
        """Get a specific version."""
        versions = self.prompts.get(name, [])
        for v in versions:
            if v.version == version:
                return v
        return None

    def promote(self, name: str, version: int) -> bool:
        """Promote a version to active (demote all others)."""
        versions = self.prompts.get(name, [])
        found = False
        for v in versions:
            if v.version == version:
                v.active = True
                found = True
            else:
                v.active = False
        if found:
            self._save()
            logger.info(f"Promoted {name} v{version} to active")
        return found

    def update_metrics(self, name: str, version: int, metrics: Dict):
        """Update evaluation metrics for a prompt version."""
        v = self.get_version(name, version)
        if v:
            v.metrics.update(metrics)
            self._save()

    def list_versions(self, name: str) -> List[PromptVersion]:
        """List all versions of a prompt."""
        return self.prompts.get(name, [])

    def list_all_names(self) -> List[str]:
        """List all registered prompt names."""
        return list(self.prompts.keys())

    def _save(self):
        """Persist to disk."""
        data = {}
        for name, versions in self.prompts.items():
            data[name] = [asdict(v) for v in versions]
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load from disk."""
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            for name, versions in data.items():
                self.prompts[name] = [PromptVersion(**v) for v in versions]
            logger.info(f"Loaded {sum(len(v) for v in self.prompts.values())} prompt versions")
        except Exception as e:
            logger.warning(f"Failed to load prompt registry: {e}")
