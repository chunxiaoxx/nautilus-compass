"""
Service to dispatch simulation tasks to the CodeExecutor.

Bridges the simulation task API with the agent-engine code generation
and execution pipeline, injecting simulation-specific system prompts
from simulation_templates.py.
"""
import asyncio
import base64
import glob as glob_mod
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional

from services.simulation_templates import get_template

logger = logging.getLogger(__name__)


class SimulationTaskService:
    """Dispatches simulation tasks to the CodeExecutor with physics-aware prompts."""

    def __init__(self) -> None:
        self._executor = None

    @property
    def executor(self):
        """Lazy-load CodeExecutor to avoid import-time side effects."""
        if self._executor is None:
            from agent_engine.executors.code_executor import CodeExecutor
            self._executor = CodeExecutor()
        return self._executor

    async def execute_task(
        self,
        task_id: str,
        task_data: dict,
        on_update: Optional[Callable[[str, dict], None]] = None,
    ) -> dict:
        """
        Execute a simulation task end-to-end.

        Args:
            task_id:   Unique task identifier.
            task_data: Dict with keys: description, simulation_type,
                       parameters, num_episodes, time_steps, output_format.
            on_update: Optional callback for status changes.

        Returns:
            Dict with keys: code, output, plots, error, execution_time.
        """
        start = time.monotonic()

        description = self._build_description(task_data)

        state = _SimulationState(
            task_id=task_id,
            task_type="CODE",
            description=description,
            input_data=None,
            expected_output=(
                f"Output format: {task_data.get('output_format', 'json')}. "
                f"Episodes: {task_data.get('num_episodes', 1)}. "
                f"Time steps: {task_data.get('time_steps', 100)}."
            ),
        )

        try:
            output = await self.executor.execute(state)
            elapsed = time.monotonic() - start

            code = getattr(state, "_generated_code", None)
            plots = self._collect_plots(state)

            return {
                "code": code,
                "output": output,
                "plots": plots if plots else None,
                "error": None,
                "execution_time": round(elapsed, 3),
            }

        except Exception as exc:
            elapsed = time.monotonic() - start
            logger.error("Simulation task %s failed: %s", task_id, exc)
            return {
                "code": None,
                "output": None,
                "plots": None,
                "error": str(exc),
                "execution_time": round(elapsed, 3),
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_description(self, task_data: dict) -> str:
        """Compose a detailed prompt for the LLM code generator."""
        parts: List[str] = []

        sim_type = task_data.get("simulation_type", "physics_simulation")
        template = get_template(sim_type)

        # Inject the simulation-specific system prompt
        parts.append(f"System context: {template['system_prompt']}")
        parts.append(f"Task type: {template['hint']}")
        parts.append("")
        parts.append(task_data["description"])

        # Merge default and user parameters
        merged_params: Dict[str, Any] = dict(
            template.get("default_parameters", {})
        )
        user_params = task_data.get("parameters")
        if user_params:
            merged_params.update(user_params)

        if merged_params:
            formatted = ", ".join(
                f"{k}={v}" for k, v in merged_params.items()
            )
            parts.append(f"Parameters: {formatted}")

        num_episodes = task_data.get("num_episodes", 1)
        time_steps = task_data.get("time_steps", 100)
        output_format = task_data.get("output_format", "json")

        parts.append(f"Number of episodes: {num_episodes}")
        parts.append(f"Time steps per episode: {time_steps}")
        parts.append(f"Output format: {output_format}")

        return "\n".join(parts)

    @staticmethod
    def _collect_plots(state) -> List[str]:
        """Scan for plot images generated during execution."""
        output_dir = getattr(state, "_output_dir", None)
        if not output_dir or not os.path.isdir(output_dir):
            return []

        encoded: List[str] = []
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.pdf"):
            for path in glob_mod.glob(os.path.join(output_dir, pattern)):
                try:
                    with open(path, "rb") as fh:
                        data = base64.b64encode(fh.read()).decode("ascii")
                    ext = os.path.splitext(path)[1].lstrip(".")
                    encoded.append(f"data:image/{ext};base64,{data}")
                except Exception as exc:
                    logger.warning("Failed to read plot %s: %s", path, exc)
        return encoded


class _SimulationState:
    """
    Minimal state object compatible with CodeExecutor.execute(state).

    CodeExecutor accesses: state.task_id, state.description,
    state.input_data, state.expected_output, state.task_type.
    """

    def __init__(
        self,
        task_id: str,
        task_type: str,
        description: str,
        input_data: Optional[str] = None,
        expected_output: Optional[str] = None,
    ) -> None:
        self.task_id = task_id
        self.task_type = task_type
        self.description = description
        self.input_data = input_data
        self.expected_output = expected_output


# Module-level singleton
_service: Optional[SimulationTaskService] = None


def get_simulation_task_service() -> SimulationTaskService:
    """Return the module-level singleton."""
    global _service
    if _service is None:
        _service = SimulationTaskService()
    return _service
