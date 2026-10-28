"""
Agent Engine Core - Main agent orchestration system.

Uses LangGraph for task orchestration with MiniMax M2.7 LLM integration.
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import logging

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AgentState(BaseModel):
    """Agent state for task execution."""
    task_id: int
    task_type: str
    description: str
    input_data: Optional[str] = None
    expected_output: Optional[str] = None

    # Execution state
    current_step: str = "init"
    plan: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    logs: List[str] = []

    # Evaluation
    feasibility_score: float = 0.0
    feasibility_reason: str = ""

    # Metadata
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0


class AgentEngine:
    """
    Core agent engine for task execution.

    Uses LangGraph for orchestration and MiniMax M2.7 for reasoning.
    """

    def __init__(self, agent_id: int, max_concurrent_tasks: int = 3):
        self.agent_id = agent_id
        self.max_concurrent_tasks = max_concurrent_tasks
        self.current_tasks: List[int] = []

        # Lazy-load LLM client to avoid import errors during testing
        self._llm = None

        # Build execution graph
        self.graph = self._build_graph()

        logger.info(f"AgentEngine initialized for agent {agent_id}")

    @property
    def llm(self):
        """Lazy-load LLM client."""
        if self._llm is None:
            from llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    def _build_graph(self) -> StateGraph:
        """Build LangGraph execution graph."""
        workflow = StateGraph(AgentState)

        workflow.add_node("evaluate", self._evaluate_task)
        workflow.add_node("plan", self._plan_execution)
        workflow.add_node("execute", self._execute_task)
        workflow.add_node("verify", self._verify_result)
        workflow.add_node("learn", self._learn_from_execution)

        workflow.set_entry_point("evaluate")
        workflow.add_edge("evaluate", "plan")
        workflow.add_edge("plan", "execute")
        workflow.add_edge("execute", "verify")
        workflow.add_conditional_edges(
            "verify",
            self._should_retry,
            {
                "retry": "plan",
                "success": "learn",
                "failure": END
            }
        )
        workflow.add_edge("learn", END)

        return workflow.compile()

    async def _evaluate_task(self, state: AgentState) -> AgentState:
        """Evaluate task complexity and feasibility using LLM."""
        logger.info(f"Evaluating task {state.task_id}")
        state.logs.append(f"[{datetime.utcnow()}] Evaluating task")
        state.current_step = "evaluate"

        prompt = f"""Evaluate this task for automatic AI execution.

Task Type: {state.task_type}
Description: {state.description}
Input Data: {(state.input_data or '')[:2000]}
Expected Output: {state.expected_output or 'Not specified'}

Respond in JSON format:
{{
  "feasibility_score": <0.0-1.0>,
  "feasibility_reason": "<brief explanation>",
  "estimated_complexity": "<low|medium|high>",
  "can_execute": <true|false>
}}"""

        try:
            response = self.llm.chat(
                prompt=prompt,
                system="You are a task evaluation AI. Respond ONLY with a JSON object, nothing else. No explanations.",
                temperature=0.1,
                max_tokens=512,
            )

            # Parse JSON from response
            eval_result = _extract_json(response)
            state.feasibility_score = eval_result.get("feasibility_score", 0.5)
            state.feasibility_reason = eval_result.get("feasibility_reason", "Evaluation complete")

            if not eval_result.get("can_execute", True):
                state.logs.append(f"Task may be infeasible: {state.feasibility_reason}")
            else:
                state.logs.append(f"Task is feasible (score: {state.feasibility_score:.2f})")

        except Exception as e:
            logger.warning(f"LLM evaluation failed, using fallback: {e}")
            state.feasibility_score = 0.5
            state.feasibility_reason = "Fallback evaluation"
            state.logs.append(f"Fallback evaluation (LLM error: {e})")

        return state

    async def _plan_execution(self, state: AgentState) -> AgentState:
        """Plan task execution strategy using LLM."""
        logger.info(f"Planning execution for task {state.task_id}")
        state.logs.append(f"[{datetime.utcnow()}] Planning execution")
        state.current_step = "plan"

        retry_context = ""
        if state.retry_count > 0:
            retry_context = f"\nPrevious attempt failed with error: {state.error}\nPlease adjust the plan to avoid this error."

        prompt = f"""Create an execution plan for this task.

Task Type: {state.task_type}
Description: {state.description}
Input Data: {(state.input_data or '')[:2000]}
Expected Output: {state.expected_output or 'Not specified'}
{retry_context}

For task type "{state.task_type}", provide a step-by-step execution plan.

If task type is "DATA_LABELING", the plan should include:
1. Parse the input data
2. Classify/label each item according to the task description
3. Format results as JSON

If task type is "CODE", the plan should include:
1. Understand requirements
2. Write Python code to solve the problem
3. The code should print the result to stdout

If task type is "DATA", the plan should include:
1. Parse the input data
2. Process according to requirements
3. Output processed data as JSON

Respond in JSON:
{{
  "steps": ["step1", "step2", ...],
  "approach": "<brief strategy description>",
  "estimated_time_seconds": <number>
}}"""

        try:
            response = self.llm.chat(
                prompt=prompt,
                system="You are a task planning AI. Respond ONLY with a JSON object, nothing else. No explanations.",
                temperature=0.2,
                max_tokens=1024,
            )

            plan_result = _extract_json(response)
            state.plan = json.dumps(plan_result, indent=2)
            steps = plan_result.get("steps", [])
            state.logs.append(f"Plan: {len(steps)} steps - {plan_result.get('approach', 'N/A')}")

        except Exception as e:
            logger.warning(f"LLM planning failed, using fallback: {e}")
            state.plan = json.dumps({
                "steps": ["Parse input", "Execute task", "Format output"],
                "approach": "Fallback generic plan",
            })
            state.logs.append(f"Fallback plan (LLM error: {e})")

        return state

    async def _execute_task(self, state: AgentState) -> AgentState:
        """Execute the task using appropriate executor."""
        logger.info(f"Executing task {state.task_id}")
        state.logs.append(f"[{datetime.utcnow()}] Executing task")
        state.current_step = "execute"
        state.started_at = datetime.utcnow()

        try:
            if state.task_type == "CODE":
                from executors.code_executor import CodeExecutor
                executor = CodeExecutor()
                state.result = await executor.execute(state)
            elif state.task_type == "DATA":
                from executors.data_executor import DataExecutor
                executor = DataExecutor()
                state.result = await executor.execute(state)
            elif state.task_type == "COMPUTE":
                from executors.compute_executor import ComputeExecutor
                executor = ComputeExecutor()
                state.result = await executor.execute(state)
            elif state.task_type == "DATA_LABELING":
                from executors.data_labeling_executor import DataLabelingExecutor
                executor = DataLabelingExecutor()
                state.result = await executor.execute(state)
            else:
                # Generic execution via LLM
                state.result = await self._execute_generic(state)

            state.completed_at = datetime.utcnow()
            state.error = None

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            state.error = str(e)
            state.logs.append(f"[{datetime.utcnow()}] Execution failed: {e}")

        return state

    async def _execute_generic(self, state: AgentState) -> str:
        """Execute generic tasks directly via LLM."""
        prompt = f"""Execute this task and provide the result.

Task Type: {state.task_type}
Description: {state.description}
Input Data: {(state.input_data or '')[:4000]}
Expected Output Format: {state.expected_output or 'Not specified'}
Plan: {state.plan or 'No specific plan'}

Provide your result directly. If the task requires structured output, use JSON."""

        response = self.llm.chat(
            prompt=prompt,
            system="You are a task execution AI. Complete the task accurately and return the result. Be precise and thorough.",
            temperature=0.2,
            max_tokens=4096,
        )
        return response

    async def _verify_result(self, state: AgentState) -> AgentState:
        """Verify task result using LLM."""
        logger.info(f"Verifying result for task {state.task_id}")
        state.logs.append(f"[{datetime.utcnow()}] Verifying result")
        state.current_step = "verify"

        if not state.result or state.error:
            state.logs.append("No result to verify or error present")
            return state

        prompt = f"""Verify this task result for correctness and completeness.

Task Description: {state.description}
Task Type: {state.task_type}
Expected Output: {state.expected_output or 'Not specified'}
Actual Result: {state.result[:3000]}

Respond in JSON:
{{
  "is_valid": <true|false>,
  "confidence": <0.0-1.0>,
  "issues": ["issue1", ...] or [],
  "summary": "<brief verification summary>"
}}"""

        try:
            response = self.llm.chat(
                prompt=prompt,
                system="You are a task verification AI. Respond ONLY with a JSON object, nothing else. No explanations, no markdown.",
                temperature=0.1,
                max_tokens=1024,
            )

            verify_result = _extract_json(response)
            is_valid = verify_result.get("is_valid", True)
            confidence = verify_result.get("confidence", 0.5)

            if is_valid:
                state.logs.append(f"Verification passed (confidence: {confidence:.2f})")
            else:
                issues = verify_result.get("issues", [])
                state.error = f"Verification failed: {'; '.join(issues)}"
                state.logs.append(f"Verification failed: {issues}")

        except Exception as e:
            logger.warning(f"LLM verification failed, accepting result: {e}")
            state.logs.append(f"Verification skipped (LLM error: {e})")

        return state

    async def _learn_from_execution(self, state: AgentState) -> AgentState:
        """Learn from task execution."""
        logger.info(f"Learning from task {state.task_id}")
        state.logs.append(f"[{datetime.utcnow()}] Learning from execution")
        state.current_step = "learn"

        execution_time = 0.0
        if state.completed_at and state.started_at:
            execution_time = (state.completed_at - state.started_at).total_seconds()

        state.logs.append(f"Execution time: {execution_time:.2f}s")

        if state.error:
            state.logs.append(f"Failed with error: {state.error}")
        else:
            state.logs.append("Task completed successfully")

        return state

    def _should_retry(self, state: AgentState) -> str:
        """Decide whether to retry task execution."""
        MAX_RETRIES = 2
        if state.result and not state.error:
            return "success"
        if state.error and state.retry_count < MAX_RETRIES:
            state.retry_count += 1
            state.logs.append(f"Retrying task (attempt {state.retry_count}/{MAX_RETRIES})")
            return "retry"
        return "failure"

    def can_accept_task(self) -> bool:
        """Check if agent can accept more tasks."""
        return len(self.current_tasks) < self.max_concurrent_tasks

    async def execute_task(self, task_data: Dict[str, Any]) -> AgentState:
        """Execute a task end-to-end."""
        if not self.can_accept_task():
            raise RuntimeError("Agent is at maximum capacity")

        state = AgentState(
            task_id=task_data["task_id"],
            task_type=task_data["task_type"],
            description=task_data["description"],
            input_data=task_data.get("input_data"),
            expected_output=task_data.get("expected_output"),
        )

        self.current_tasks.append(state.task_id)

        try:
            final_state = await self.graph.ainvoke(state)
            return final_state
        finally:
            if state.task_id in self.current_tasks:
                self.current_tasks.remove(state.task_id)

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status."""
        return {
            "agent_id": self.agent_id,
            "current_tasks": len(self.current_tasks),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "available_capacity": self.max_concurrent_tasks - len(self.current_tasks),
        }


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response text, handling markdown code blocks and ThinkingBlocks."""
    import re as _re
    text = text.strip()

    # Strip ThinkingBlock artifacts from MiniMax M2.7
    text = _re.sub(r'ThinkingBlock\([^)]*(?:\([^)]*\)[^)]*)*\)', '', text, flags=_re.DOTALL).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from ```json ... ``` block
    if "```json" in text:
        start = text.index("```json") + 7
        end = text.index("```", start)
        return json.loads(text[start:end].strip())

    if "```" in text:
        start = text.index("```") + 3
        end = text.index("```", start)
        return json.loads(text[start:end].strip())

    # Try finding { ... } in text
    brace_start = text.find("{")
    brace_end = text.rfind("}") + 1
    if brace_start >= 0 and brace_end > brace_start:
        candidate = text[brace_start:brace_end]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract JSON from: {text[:200]}")
