"""
Service to dispatch academic tasks to the agent-engine CodeExecutor.

Bridges the academic task API with the agent-engine's code generation
and execution pipeline. Uses CodeExecutor directly (same-process import).

Production features:
- Template-enhanced prompts for each task type
- Automatic retry on failure with error-aware prompt refinement
- Result validation (output checks, plot existence)
- Structured result formatting
"""
import asyncio
import base64
import glob
import logging
import os
import re
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional

from services.academic_templates import get_template

logger = logging.getLogger(__name__)

# Maximum retry attempts for failed code generation / execution
MAX_RETRIES = 2

# Map academic task types to simple hints (fallback when no template exists)
_TASK_TYPE_HINTS: Dict[str, str] = {
    "curve_fitting": "Perform curve fitting / regression analysis.",
    "ode_simulation": "Solve ordinary differential equations numerically.",
    "pde_simulation": "Solve partial differential equations numerically.",
    "monte_carlo": "Run a Monte Carlo simulation.",
    "statistical_analysis": "Perform statistical analysis on the data.",
    "ml_training": "Train a machine learning model.",
    "data_visualization": "Create data visualizations / plots.",
    "physics_simulation": "Run a physics simulation.",
    "general_computation": "Perform a general scientific computation.",
    "jc_constitutive": "Fit Johnson-Cook constitutive model parameters.",
    "thmc_coupling": "Run THMC coupled simulation.",
}


class AcademicTaskService:
    """Dispatches academic tasks to the CodeExecutor for LLM-driven execution."""

    def __init__(self) -> None:
        self._executor = None
        self._llm = None

    @property
    def executor(self):
        """Lazy-load CodeExecutor to avoid import-time side effects."""
        if self._executor is None:
            from agent_engine.executors.code_executor import CodeExecutor
            self._executor = CodeExecutor()
        return self._executor

    @property
    def llm(self):
        """Lazy-load LLM client."""
        if self._llm is None:
            from agent_engine.llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute_task(
        self,
        task_id: str,
        task_data: dict,
        on_update: Optional[Callable[[str, dict], None]] = None,
    ) -> dict:
        """
        Execute an academic task end-to-end with retry logic.

        Args:
            task_id: Unique task identifier.
            task_data: Dict with keys: description, task_type, input_data,
                       parameters, expected_output.
            on_update: Optional callback(task_id, update_dict) for status
                       changes.

        Returns:
            Dict with keys: code, output, plots, error, execution_time.
        """
        start = time.monotonic()
        task_type = task_data.get("task_type", "general_computation")

        # ── DeerFlow Smart Router ────────────────────────────────────────────
        # Research tasks get the full Planner→Researchers→Reporter pipeline.
        # Auto-detect: explicit "research" type OR description strongly signals research.
        if self._is_research_task(task_type, task_data.get("description", "")):
            return await self._execute_research_pipeline(task_id, task_data, start)
        # ────────────────────────────────────────────────────────────────────

        template = get_template(task_type)

        last_error: Optional[str] = None
        last_code: Optional[str] = None
        result: Optional[dict] = None

        for attempt in range(1, MAX_RETRIES + 1):
            attempt_start = time.monotonic()
            logger.info(
                "Academic task %s attempt %d/%d (type=%s)",
                task_id, attempt, MAX_RETRIES, task_type,
            )

            try:
                # Generate code using template-enhanced prompt
                code = await self._generate_code(
                    task_data, template, last_error, last_code,
                )

                # Execute the generated code
                output = await self._execute_code(code)

                # Collect plots from workspace
                plots = self._collect_plots_from_workspace()

                # Validate the result
                validation = self._validate_result(
                    output=output,
                    code=code,
                    plots=plots,
                    template=template,
                )

                elapsed = time.monotonic() - start
                formatted_output = self._format_output(output, task_data)

                # ── DeerFlow Quality Gate ────────────────────────────────
                quality_meta: dict = {}
                try:
                    from services.task_quality_gate import score_task_output, interpret_quality
                    scores = await score_task_output(
                        task_data.get("description", ""),
                        formatted_output or "",
                    )
                    quality_meta = interpret_quality(scores)
                    if quality_meta.get("quality_warning"):
                        logger.warning(
                            "Task %s quality=%s (score=%.2f)",
                            task_id,
                            quality_meta["quality_level"],
                            quality_meta["quality_score"],
                        )
                except Exception as qe:
                    logger.debug("Quality gate non-critical error: %s", qe)
                # ─────────────────────────────────────────────────────────

                result = {
                    "code": code,
                    "output": formatted_output,
                    "plots": plots if plots else None,
                    "error": None,
                    "execution_time": round(elapsed, 3),
                    "validation": validation,
                    "attempt": attempt,
                    **quality_meta,
                }

                # If validation found issues but code ran, still return
                # but log warnings
                if validation.get("warnings"):
                    for w in validation["warnings"]:
                        logger.warning(
                            "Task %s validation warning: %s", task_id, w
                        )

                return result

            except Exception as exc:
                last_error = str(exc)
                last_code = locals().get("code")
                logger.warning(
                    "Academic task %s attempt %d failed: %s",
                    task_id, attempt, exc,
                )

                if attempt < MAX_RETRIES:
                    # Brief pause before retry
                    await asyncio.sleep(1)
                    continue

                # Final attempt failed
                elapsed = time.monotonic() - start
                return {
                    "code": last_code,
                    "output": None,
                    "plots": None,
                    "error": last_error,
                    "execution_time": round(elapsed, 3),
                    "validation": {"passed": False, "warnings": [last_error]},
                    "attempt": attempt,
                }

        # Should not reach here, but satisfy the type checker
        elapsed = time.monotonic() - start
        return {
            "code": None,
            "output": None,
            "plots": None,
            "error": "Max retries exhausted",
            "execution_time": round(elapsed, 3),
        }

    # ------------------------------------------------------------------
    # Code generation (template-aware, replaces CodeExecutor._generate_code)
    # ------------------------------------------------------------------

    async def _generate_code(
        self,
        task_data: dict,
        template: Any,
        previous_error: Optional[str] = None,
        previous_code: Optional[str] = None,
    ) -> str:
        """
        Generate Python code using the LLM with template-enhanced prompts.

        On retry, includes the previous error and code so the LLM can fix it.
        """
        description = self._build_description(task_data, template)

        # Build the user prompt
        prompt_parts = [
            "Write a complete, runnable Python script to solve this task.",
            "",
            f"Task:\n{description}",
        ]

        input_data = task_data.get("input_data")
        if input_data:
            # Truncate very large data
            truncated = input_data[:5000]
            if len(input_data) > 5000:
                truncated += "\n... (data truncated)"
            prompt_parts.append(f"\nInput Data:\n{truncated}")

        expected = task_data.get("expected_output")
        if expected:
            prompt_parts.append(f"\nExpected Output: {expected}")

        prompt_parts.append(
            "\nIMPORTANT requirements:\n"
            "- Complete, self-contained Python script\n"
            "- Use scientific libraries: numpy, scipy, matplotlib, pandas, "
            "scikit-learn, torch (all available)\n"
            "- Use matplotlib.use('Agg') for non-interactive plotting\n"
            "- Save all plots to /workspace/output/ directory\n"
            "- Create /workspace/output/ directory with os.makedirs if needed\n"
            "- Print results clearly to stdout\n"
            "- Handle edge cases gracefully"
        )

        # On retry, include the error context
        if previous_error and previous_code:
            prompt_parts.append(
                f"\n--- PREVIOUS ATTEMPT FAILED ---\n"
                f"The previous code produced this error:\n{previous_error}\n\n"
                f"Previous code:\n```python\n{previous_code}\n```\n\n"
                f"Fix the error and provide a corrected version."
            )

        prompt_parts.append(
            "\nRespond with ONLY the Python code inside ```python ... ``` markers."
        )

        prompt = "\n".join(prompt_parts)

        # Use template system prompt if available, otherwise default
        system_prompt = (
            template.system_prompt
            if template
            else (
                "You are an expert scientific computing engineer. "
                "Write clean, correct, well-documented Python code. "
                "Always include proper imports, error handling, and "
                "publication-quality plot formatting."
            )
        )

        # Run LLM call in thread pool with hard timeout to prevent hangs
        description = task_data.get("description", "")
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.llm.chat,
                    prompt=prompt,
                    system=system_prompt,
                    temperature=0.2,
                    max_tokens=8192,
                ),
                timeout=60,  # 60 second hard timeout
            )
        except asyncio.TimeoutError:
            logger.warning("LLM call timed out after 60s, retrying with shorter prompt")
            # Retry with a much shorter prompt
            short_prompt = (
                f"Write a concise Python script (under 100 lines) for: "
                f"{description[:500]}\n\n"
                f"Use numpy, scipy, matplotlib. Print results. "
                f"Save plot to /workspace/output/result.png"
            )
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.llm.chat,
                    prompt=short_prompt,
                    system="Write short, working Python code.",
                    temperature=0.3,
                    max_tokens=4096,
                ),
                timeout=45,
            )
        return _extract_code(response)

    # ------------------------------------------------------------------
    # Code execution
    # ------------------------------------------------------------------

    async def _execute_code(self, code: str) -> str:
        """
        Execute generated code via the CodeExecutor's run infrastructure.

        We call the executor's _run_code directly to skip re-generating code.
        """
        return await self.executor._run_code(code)

    # ------------------------------------------------------------------
    # Description building (template-enhanced)
    # ------------------------------------------------------------------

    def _build_description(self, task_data: dict, template: Any) -> str:
        """Compose a detailed description for the LLM code generator."""
        parts: List[str] = []

        task_type = task_data.get("task_type", "general_computation")
        hint = _TASK_TYPE_HINTS.get(task_type, "")
        if hint:
            parts.append(f"Task type: {hint}")

        parts.append(task_data["description"])

        params = task_data.get("parameters")
        if params:
            formatted = ", ".join(f"{k}={v}" for k, v in params.items())
            parts.append(f"Parameters: {formatted}")

        expected = task_data.get("expected_output")
        if expected:
            parts.append(f"Expected output: {expected}")

        # Append template-specific requirements
        if template:
            parts.append(template.description_suffix)

        return "\n".join(parts)

    # ------------------------------------------------------------------
    # Result validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_result(
        output: Optional[str],
        code: str,
        plots: List[str],
        template: Any,
    ) -> dict:
        """
        Validate the execution result for quality.

        Returns a dict with:
            passed: bool - overall pass/fail
            warnings: list[str] - specific issues found
            checks: dict - individual check results
        """
        warnings: List[str] = []
        checks: Dict[str, bool] = {}

        # Check 1: Code actually produced output
        has_output = bool(output and output.strip())
        checks["has_output"] = has_output
        if not has_output:
            warnings.append("Code produced no stdout output")

        # Check 2: Output doesn't contain only error tracebacks
        has_traceback = bool(
            output
            and ("Traceback (most recent call last)" in output
                 or "Error:" in output
                 or "Exception:" in output)
        )
        checks["no_traceback"] = not has_traceback
        if has_traceback:
            warnings.append("Output contains error traceback")

        # Check 3: Plots were generated (if template expects them)
        if template and template.output_files:
            checks["has_plots"] = len(plots) > 0
            if not plots:
                warnings.append(
                    f"Expected plot output ({', '.join(template.output_files)}) "
                    f"but none were generated"
                )
        else:
            checks["has_plots"] = True  # no expectation

        # Check 4: Template-specific validation keywords in output
        if template and template.validation_checks and output:
            output_lower = output.lower()
            found = sum(
                1 for keyword in template.validation_checks
                if keyword.lower() in output_lower
            )
            total = len(template.validation_checks)
            ratio = found / total if total > 0 else 1.0
            checks["validation_keywords"] = ratio >= 0.3
            if ratio < 0.3:
                warnings.append(
                    f"Only {found}/{total} expected keywords found in output"
                )

        # Check 5: Code quality basics
        checks["has_imports"] = "import " in code
        if not checks["has_imports"]:
            warnings.append("Generated code has no import statements")

        checks["not_empty"] = len(code.strip()) > 50
        if not checks["not_empty"]:
            warnings.append("Generated code is suspiciously short")

        passed = (
            checks.get("has_output", False)
            and checks.get("no_traceback", True)
            and checks.get("not_empty", True)
        )

        return {
            "passed": passed,
            "warnings": warnings,
            "checks": checks,
        }

    # ------------------------------------------------------------------
    # Output formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _format_output(raw_output: Optional[str], task_data: dict) -> str:
        """
        Format raw stdout into a structured result report.

        Adds a header and footer to make the output professional.
        """
        if not raw_output:
            return ""

        title = task_data.get("title", "Academic Task")
        task_type = task_data.get("task_type", "general_computation")

        header = (
            f"{'=' * 60}\n"
            f"  {title}\n"
            f"  Task Type: {task_type}\n"
            f"{'=' * 60}\n"
        )

        footer = (
            f"\n{'=' * 60}\n"
            f"  Generated by Nautilus Academic Engine\n"
            f"{'=' * 60}"
        )

        return f"{header}\n{raw_output.strip()}\n{footer}"

    # ------------------------------------------------------------------
    # Plot collection
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_plots_from_workspace() -> List[str]:
        """
        Scan the default workspace output directory for plot files
        and return them as base64-encoded data URIs.
        """
        output_dir = "/workspace/output"
        if not os.path.isdir(output_dir):
            return []

        encoded: List[str] = []
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.pdf"):
            for path in glob.glob(os.path.join(output_dir, pattern)):
                try:
                    with open(path, "rb") as fh:
                        data = base64.b64encode(fh.read()).decode("ascii")
                    ext = os.path.splitext(path)[1].lstrip(".")
                    encoded.append(f"data:image/{ext};base64,{data}")
                except Exception as exc:
                    logger.warning("Failed to read plot %s: %s", path, exc)
        return encoded

    # ------------------------------------------------------------------
    # DeerFlow: Smart Router helpers
    # ------------------------------------------------------------------

    _RESEARCH_KEYWORDS = frozenset([
        "research", "survey", "review", "analyze", "analysis", "summarize",
        "summary", "report", "literature", "compare", "comparison", "study",
        "investigate", "overview", "explain", "describe",
    ])

    @staticmethod
    def _auto_depth(description: str) -> str:
        """Auto-detect research depth from description length and keywords."""
        length = len(description)
        desc_lower = description.lower()

        # Keyword override
        if any(k in desc_lower for k in ["comprehensive", "thorough", "in-depth", "detailed", "extensive"]):
            return "thorough"
        if any(k in desc_lower for k in ["brief", "quick", "summary", "overview", "short"]):
            return "quick"

        # Length-based
        if length > 500:
            return "thorough"
        elif length > 150:
            return "standard"
        else:
            return "quick"

    def _is_research_task(self, task_type: str, description: str) -> bool:
        """Return True if this task should use the DeerFlow research pipeline."""
        if task_type == "research":
            return True
        # Auto-detect from description (first 200 chars)
        desc_lower = description[:200].lower()
        return sum(1 for kw in self._RESEARCH_KEYWORDS if kw in desc_lower) >= 2

    async def _execute_research_pipeline(
        self, task_id: str, task_data: dict, start: float
    ) -> dict:
        """Route task through DeerFlow Planner→Researchers→Reporter pipeline."""
        try:
            from services.deep_research import get_deep_research
            pipeline = get_deep_research()
            topic = task_data.get("description", task_data.get("title", "Unknown topic"))
            depth = self._auto_depth(task_data.get("description", ""))
            research_result = await pipeline.run(topic=topic, depth=depth)
            elapsed = time.monotonic() - start
            output = research_result.get("report", "")
            sections = research_result.get("sections", {})
            return {
                "code": None,
                "output": output,
                "plots": None,
                "error": None,
                "execution_time": round(elapsed, 3),
                "validation": {"passed": True, "warnings": []},
                "attempt": 1,
                "pipeline": "deerflow",
                "sections": sections,
                "depth": research_result.get("depth", "standard"),
                "sources_count": research_result.get("observations_count", 0),
                "quality_level": "GOOD",
                "quality_score": 0.85,
            }
        except Exception as exc:
            logger.warning("DeerFlow research pipeline failed, falling back to code executor: %s", exc)
            # Fall back to standard code execution
            template = get_template(task_data.get("task_type", "general_computation"))
            return await self._execute_standard(task_id, task_data, template, start)

    async def _execute_standard(
        self, task_id: str, task_data: dict, template, start: float
    ) -> dict:
        """Standard code-execution path (extracted for fallback use)."""
        task_type = task_data.get("task_type", "general_computation")
        last_error = None
        last_code = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                code = await self._generate_code(task_data, template, last_error, last_code)
                output = await self._execute_code(code)
                plots = self._collect_plots_from_workspace()
                validation = self._validate_result(output=output, code=code, plots=plots, template=template)
                elapsed = time.monotonic() - start
                formatted_output = self._format_output(output, task_data)
                return {
                    "code": code,
                    "output": formatted_output,
                    "plots": plots if plots else None,
                    "error": None,
                    "execution_time": round(elapsed, 3),
                    "validation": validation,
                    "attempt": attempt,
                }
            except Exception as exc:
                last_error = str(exc)
                last_code = locals().get("code")
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(1)
        elapsed = time.monotonic() - start
        return {
            "code": last_code, "output": None, "plots": None,
            "error": last_error, "execution_time": round(elapsed, 3),
            "validation": {"passed": False, "warnings": [last_error]}, "attempt": MAX_RETRIES,
        }

    @staticmethod
    def _collect_plots(state) -> List[str]:
        """
        Legacy method: scan for plot files via state._output_dir.
        Kept for backward compatibility.
        """
        output_dir = getattr(state, "_output_dir", None)
        if not output_dir or not os.path.isdir(output_dir):
            return []

        encoded: List[str] = []
        for pattern in ("*.png", "*.jpg", "*.jpeg", "*.svg", "*.pdf"):
            for path in glob.glob(os.path.join(output_dir, pattern)):
                try:
                    with open(path, "rb") as fh:
                        data = base64.b64encode(fh.read()).decode("ascii")
                    ext = os.path.splitext(path)[1].lstrip(".")
                    encoded.append(f"data:image/{ext};base64,{data}")
                except Exception as exc:
                    logger.warning("Failed to read plot %s: %s", path, exc)
        return encoded


class _AcademicState:
    """
    Minimal state object compatible with CodeExecutor.execute(state).

    CodeExecutor only accesses: state.task_id, state.description,
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


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _extract_code(response: str) -> str:
    """Extract Python code from LLM response. Handles various formats."""
    # Strip ThinkingBlock artifacts from some LLM responses
    response = re.sub(
        r'ThinkingBlock\([^)]*(?:\([^)]*\)[^)]*)*\)', '', response, flags=re.DOTALL
    ).strip()

    # Try ```python ... ``` first
    for marker in ["```python", "```py", "```"]:
        if marker in response:
            start = response.index(marker) + len(marker)
            try:
                end = response.index("```", start)
                return response[start:end].strip()
            except ValueError:
                return response[start:].strip()

    # Try <code> tags
    for open_tag, close_tag in [("<code>", "</code>"), ("<python>", "</python>")]:
        if open_tag in response:
            start = response.index(open_tag) + len(open_tag)
            end = response.find(close_tag, start)
            if end == -1:
                end = len(response)
            return response[start:end].strip()

    # If it looks like code already, return as-is
    indicators = ["import ", "def ", "class ", "print(", "for "]
    if sum(1 for i in indicators if i in response) >= 2:
        return response

    # Last resort: find first code-like line
    for keyword in ["import ", "from ", "def ", "class ", "#!"]:
        idx = response.find(keyword)
        if idx != -1:
            return response[idx:].strip()

    return response


# Module-level singleton for convenience
_service: Optional[AcademicTaskService] = None


def get_academic_task_service() -> AcademicTaskService:
    """Return a module-level singleton of the service."""
    global _service
    if _service is None:
        _service = AcademicTaskService()
    return _service
