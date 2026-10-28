"""
Strategy Optimizer - Analyzes failure patterns and generates improved execution strategies.

Unlike prompt optimization (which changes what the LLM sees), strategy optimization
changes HOW the agent processes tasks: retry logic, preprocessing, error handling.

Strategies are versioned and A/B tested just like prompts.
"""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logger = logging.getLogger(__name__)

STRATEGIES_FILE = os.path.join(os.path.dirname(__file__), "strategies.json")


@dataclass
class ExecutionStrategy:
    """A versioned execution strategy configuration."""
    name: str
    version: int
    config: Dict = field(default_factory=dict)
    created_at: str = ""
    created_by: str = "human"
    active: bool = False
    metrics: Dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


# Default strategies
DEFAULT_STRATEGIES = {
    "retry": {
        "max_retries": 2,
        "backoff_factor": 1.5,
        "retry_on_parse_error": True,
        "retry_on_timeout": True,
        "retry_on_low_confidence": False,
        "low_confidence_threshold": 0.3,
    },
    "preprocessing": {
        "strip_whitespace": True,
        "normalize_unicode": True,
        "truncate_long_items": True,
        "max_item_length": 500,
        "batch_size": 20,
    },
    "postprocessing": {
        "normalize_labels": True,
        "reject_low_confidence": False,
        "confidence_threshold": 0.5,
        "fallback_label": "UNKNOWN",
    },
}


class StrategyRegistry:
    """Manages versioned execution strategies."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or STRATEGIES_FILE
        self.strategies: Dict[str, List[ExecutionStrategy]] = {}
        self._load()

    def register(
        self,
        name: str,
        config: Dict,
        created_by: str = "human",
        activate: bool = False,
    ) -> ExecutionStrategy:
        """Register a new strategy version."""
        if name not in self.strategies:
            self.strategies[name] = []

        version = len(self.strategies[name]) + 1
        strategy = ExecutionStrategy(
            name=name,
            version=version,
            config=config,
            created_by=created_by,
            active=activate or version == 1,
        )

        if activate:
            for existing in self.strategies[name]:
                existing.active = False

        self.strategies[name].append(strategy)
        self._save()
        return strategy

    def get_active(self, name: str) -> Optional[ExecutionStrategy]:
        """Get currently active strategy."""
        versions = self.strategies.get(name, [])
        for v in reversed(versions):
            if v.active:
                return v
        return versions[-1] if versions else None

    def promote(self, name: str, version: int) -> bool:
        """Promote a strategy version to active."""
        versions = self.strategies.get(name, [])
        found = False
        for v in versions:
            v.active = v.version == version
            if v.active:
                found = True
        if found:
            self._save()
        return found

    def update_metrics(self, name: str, version: int, metrics: Dict):
        """Update metrics for a strategy version."""
        versions = self.strategies.get(name, [])
        for v in versions:
            if v.version == version:
                v.metrics.update(metrics)
                self._save()
                return

    def _save(self):
        data = {}
        for name, versions in self.strategies.items():
            data[name] = [asdict(v) for v in versions]
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load(self):
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            for name, versions in data.items():
                self.strategies[name] = [ExecutionStrategy(**v) for v in versions]
        except Exception as e:
            logger.warning(f"Failed to load strategies: {e}")


class StrategyOptimizer:
    """
    Analyzes task execution failures and proposes strategy improvements.

    Flow:
    1. Collect failure data from recent task executions
    2. Classify failure patterns (parse error, timeout, low confidence, etc.)
    3. Ask LLM to propose strategy changes based on patterns
    4. Evaluate new strategy against baseline
    5. Promote if improved
    """

    def __init__(self):
        self.registry = StrategyRegistry()
        self._ensure_defaults()

    def _ensure_defaults(self):
        """Register default strategies if none exist."""
        for name, config in DEFAULT_STRATEGIES.items():
            if not self.registry.get_active(name):
                self.registry.register(name, config, created_by="human", activate=True)

    def analyze_failures(self, failure_logs: List[Dict]) -> Dict:
        """
        Classify failure patterns from execution logs.

        Returns counts of each failure type.
        """
        patterns = {
            "parse_error": 0,
            "timeout": 0,
            "low_confidence": 0,
            "wrong_format": 0,
            "llm_error": 0,
            "unknown": 0,
        }

        for log in failure_logs:
            error = str(log.get("error", "")).lower()
            if "json" in error or "parse" in error:
                patterns["parse_error"] += 1
            elif "timeout" in error or "timed out" in error:
                patterns["timeout"] += 1
            elif "confidence" in error:
                patterns["low_confidence"] += 1
            elif "format" in error:
                patterns["wrong_format"] += 1
            elif "api" in error or "llm" in error or "rate" in error:
                patterns["llm_error"] += 1
            else:
                patterns["unknown"] += 1

        return patterns

    def propose_improvement(
        self, failure_patterns: Dict, current_strategies: Dict[str, Dict]
    ) -> Optional[Dict[str, Dict]]:
        """
        Ask LLM to propose strategy improvements based on failure patterns.

        Returns dict of strategy_name -> new config.
        """
        from llm.client import get_llm_client
        llm = get_llm_client()

        prompt = f"""You are optimizing an AI agent's execution strategy based on failure analysis.

Current strategies:
{json.dumps(current_strategies, indent=2)}

Failure pattern analysis (from recent executions):
{json.dumps(failure_patterns, indent=2)}

Propose improved strategy configurations to reduce failures. Consider:
1. If parse_error is high → adjust preprocessing or add JSON repair steps
2. If timeout is high → reduce batch_size or increase max_retries with backoff
3. If low_confidence is high → enable confidence-based rejection and retry
4. If llm_error is high → increase backoff_factor and max_retries

Respond in JSON with the same structure as current strategies, only including
strategies you want to change:
{{
  "retry": {{ ... }},
  "preprocessing": {{ ... }},
  "postprocessing": {{ ... }},
  "reasoning": "brief explanation"
}}"""

        try:
            response = llm.chat(
                prompt=prompt,
                system="You are an AI systems optimization expert. Respond ONLY with JSON.",
                temperature=0.3,
                max_tokens=2048,
            )

            import re
            response = re.sub(
                r'ThinkingBlock\([^)]*(?:\([^)]*\)[^)]*)*\)', '', response, flags=re.DOTALL
            ).strip()

            try:
                return json.loads(response)
            except json.JSONDecodeError:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(response[start:end])
        except Exception as e:
            logger.error(f"Failed to propose strategy improvement: {e}")

        return None

    def optimize(self, failure_logs: List[Dict], verbose: bool = True) -> Dict:
        """
        Run one round of strategy optimization.

        Returns summary with changes made.
        """
        if verbose:
            print(f"\n{'='*60}")
            print("Strategy Optimizer")
            print(f"{'='*60}")
            print(f"Analyzing {len(failure_logs)} failure logs...")

        # Analyze failures
        patterns = self.analyze_failures(failure_logs)
        total_failures = sum(patterns.values())

        if verbose:
            print(f"Failure patterns: {json.dumps(patterns, indent=2)}")

        if total_failures == 0:
            if verbose:
                print("No failures to optimize for.")
            return {"improved": False, "reason": "no failures"}

        # Get current strategies
        current = {}
        for name in DEFAULT_STRATEGIES:
            active = self.registry.get_active(name)
            if active:
                current[name] = active.config

        # Propose improvements
        proposal = self.propose_improvement(patterns, current)
        if not proposal:
            if verbose:
                print("No improvements proposed.")
            return {"improved": False, "reason": "no proposal"}

        reasoning = proposal.pop("reasoning", "No reasoning provided")
        if verbose:
            print(f"Reasoning: {reasoning}")

        # Register and promote new strategies
        changes = []
        for name, new_config in proposal.items():
            if name in DEFAULT_STRATEGIES and isinstance(new_config, dict):
                new_strategy = self.registry.register(
                    name, new_config, created_by="agent", activate=True
                )
                changes.append({
                    "strategy": name,
                    "version": new_strategy.version,
                    "config": new_config,
                })
                if verbose:
                    print(f"  Updated {name} → v{new_strategy.version}")

        return {
            "improved": len(changes) > 0,
            "changes": changes,
            "failure_patterns": patterns,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_active_strategies(self) -> Dict[str, Dict]:
        """Get all currently active strategy configs."""
        result = {}
        for name in DEFAULT_STRATEGIES:
            active = self.registry.get_active(name)
            if active:
                result[name] = active.config
        return result
