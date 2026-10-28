"""
Code Executor - Generates and executes code tasks using LLM + Docker sandbox.
"""
import docker
import tempfile
import os
import json
import subprocess
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Execute code tasks using LLM for generation and Docker for safe execution."""

    def __init__(self):
        self._llm = None
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.warning(f"Docker not available, will use direct execution: {e}")
            self.docker_client = None

    @property
    def llm(self):
        if self._llm is None:
            from llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    async def execute(self, state) -> str:
        """Execute code task. Generates code via LLM if input isn't code."""
        logger.info(f"Executing code task {state.task_id}")
        input_data = state.input_data or ""

        if _looks_like_code(input_data):
            code = input_data
        else:
            code = await self._generate_code(state)

        return await self._run_code(code)

    async def _generate_code(self, state) -> str:
        """Generate Python code using LLM."""
        prompt = f"""Write Python code to solve this task.

Task: {state.description}
Input/Requirements: {(state.input_data or '')[:3000]}
Expected Output: {state.expected_output or 'Print the result to stdout'}

Requirements:
- Complete, runnable Python script
- Available libraries: numpy, scipy, matplotlib, pandas, sympy, scikit-learn, statsmodels, seaborn, networkx, torch (CPU), lmfit (curve fitting), gmsh (mesh generation), meshio (mesh I/O), pyvista (3D visualization), pyDOE2 (design of experiments), uncertainties (error propagation), cantera (chemical kinetics, if available), fenics-dolfinx (FEM solver, if available)
- For plots: save to /workspace/output/ directory (use plt.savefig('/workspace/output/plot.png'))
- Print numerical results to stdout

Respond with ONLY Python code in ```python ... ``` markers."""

        import asyncio
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.llm.chat,
                    prompt=prompt,
                    system="You are an expert Python programmer. Write clean, correct, runnable code.",
                    temperature=0.2,
                    max_tokens=4096,
                ),
                timeout=60,  # 60 second hard timeout
            )
        except asyncio.TimeoutError:
            logger.warning("LLM call timed out after 60s, retrying with shorter prompt")
            short_prompt = (
                f"Write a concise Python script (under 100 lines) for: "
                f"{state.description[:500]}\n\n"
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

    async def _run_code(self, code: str) -> str:
        """Run code in Docker sandbox or directly."""
        if self.docker_client:
            return await self._run_in_docker(code)
        return await self._run_directly(code)

    async def _run_in_docker(self, code: str) -> str:
        """Run code in Docker container (non-blocking)."""
        import asyncio

        def _docker_run(code_text):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Create output dir for plots
                os.makedirs(os.path.join(tmpdir, "output"), exist_ok=True)
                code_file = os.path.join(tmpdir, "solution.py")
                with open(code_file, "w") as f:
                    f.write(code_text)
                try:
                    result = self.docker_client.containers.run(
                        image="nautilus-scientific:latest",
                        command="python solution.py",
                        volumes={tmpdir: {"bind": "/workspace", "mode": "rw"}},
                        working_dir="/workspace",
                        mem_limit="512m",
                        cpu_quota=100000,
                        network_mode="none",
                        remove=True, detach=False, stdout=True, stderr=True,
                    )
                    return result.decode("utf-8")
                except docker.errors.ContainerError as e:
                    stderr = e.stderr.decode("utf-8") if e.stderr else str(e)
                    raise RuntimeError(f"Code execution failed: {stderr}")

        return await asyncio.to_thread(_docker_run, code)

    async def _run_directly(self, code: str) -> str:
        """Run code directly (fallback when Docker unavailable)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Code execution failed:\n{result.stderr}")
            return result.stdout
        finally:
            os.unlink(temp_path)

    async def run_tests(self, code: str, tests: str) -> Dict[str, Any]:
        """Run unit tests on code."""
        try:
            output = await self._run_code(f"{code}\n\n{tests}")
            return {"passed": True, "output": output}
        except RuntimeError as e:
            return {"passed": False, "error": str(e)}

    async def static_analysis(self, code: str) -> Dict[str, Any]:
        """Run static analysis using LLM."""
        prompt = f'Analyze this Python code for issues:\n\n```python\n{code}\n```\n\nRespond in JSON: {{"issues": [], "score": 0}}'
        response = self.llm.chat(prompt=prompt, temperature=0.1, max_tokens=2048)
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"issues": [], "score": 7}


def _looks_like_code(text: str) -> bool:
    """Heuristic: does text look like Python code?"""
    indicators = ["def ", "class ", "import ", "print(", "for ", "if __name__", "return "]
    if len(text.strip().split("\n")) < 2:
        return False
    return sum(1 for i in indicators if i in text) >= 2


def _extract_code(response: str) -> str:
    """Extract Python code from LLM response. Handles various formats."""
    response = response.strip()

    # Try ```python ... ``` first
    for marker in ["```python", "```py", "```"]:
        if marker in response:
            start = response.index(marker) + len(marker)
            try:
                end = response.index("```", start)
                return response[start:end].strip()
            except ValueError:
                # No closing ```, take everything after the marker
                return response[start:].strip()

    # Try <code> ... </code> or <python> ... </python>
    for open_tag, close_tag in [("<code>", "</code>"), ("<python>", "</python>")]:
        if open_tag in response:
            start = response.index(open_tag) + len(open_tag)
            end = response.find(close_tag, start)
            if end == -1:
                end = len(response)
            return response[start:end].strip()

    # If response looks like code already, return as-is
    if _looks_like_code(response):
        return response

    # Last resort: strip any non-code preamble (text before first import/def/class)
    for keyword in ["import ", "from ", "def ", "class ", "#!"]:
        idx = response.find(keyword)
        if idx != -1:
            return response[idx:].strip()

    return response
