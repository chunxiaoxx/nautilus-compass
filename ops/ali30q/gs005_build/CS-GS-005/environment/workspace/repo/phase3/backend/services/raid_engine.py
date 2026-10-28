"""Multi-level Raid consensus engine.

Raid 1: Single execution + self-review
Raid 2: Execute -> Review -> Improve (max 3 rounds)
Raid 3: 3 parallel executions + majority vote
Raid 5: 5 expert reviews + 4/5 consensus threshold
"""
import asyncio
import json
import logging
import re
import time
import uuid
from datetime import datetime
from enum import IntEnum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.raid import RaidExecution, RaidVote

from services.checkpoint import save_checkpoint, load_checkpoint, clear_checkpoint
from services.raid_config import get_engine_params, get_raid_level_config

logger = logging.getLogger(__name__)

# Pulled from YAML config at runtime via get_engine_params(level).
# Module-level constants kept as fallbacks only for import compatibility.
_L2 = get_engine_params(2)
_L3 = get_engine_params(3)
_L5 = get_engine_params(5)
MAX_ROUNDS_RAID2 = _L2["max_rounds"]
QUALITY_THRESHOLD = _L2["quality_threshold"]
CONSENSUS_THRESHOLD = _L5["consensus_threshold"]
EXPERT_COUNT = _L5["expert_count"]
PARALLEL_COUNT = _L3["parallel_count"]


class RaidLevel(IntEnum):
    RAID_1 = 1
    RAID_2 = 2
    RAID_3 = 3
    RAID_5 = 5


class VoteInfo(BaseModel):
    role: str
    round_number: int
    output: Optional[str] = None
    approved: Optional[bool] = None
    quality_score: Optional[float] = None
    feedback: Optional[str] = None


class RaidResult(BaseModel):
    execution_id: str
    raid_level: int
    status: str
    output: str
    consensus_score: float
    rounds: int
    votes: List[VoteInfo]


class RaidEngine:
    """Orchestrates multi-level Raid consensus executions."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from agent_engine.llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    async def execute(
        self, task_description: str,
        level: RaidLevel = RaidLevel.RAID_2,
        context: Optional[Dict[str, Any]] = None,
        task_id: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> RaidResult:
        """Entry point: dispatch to appropriate raid level handler."""
        execution_id = str(uuid.uuid4())[:12]
        self._save_execution(execution_id, int(level), "executing", "", 0.0, 0)
        logger.info("Raid %d started: exec_id=%s", int(level), execution_id)
        dispatch = {
            RaidLevel.RAID_1: self._raid_1, RaidLevel.RAID_2: self._raid_2,
            RaidLevel.RAID_3: self._raid_3, RaidLevel.RAID_5: self._raid_5,
        }
        handler = dispatch.get(level)
        if handler is None:
            raise ValueError(f"Unsupported raid level: {level}")
        t0 = time.monotonic()
        success = False
        result: Optional[RaidResult] = None
        try:
            result = await handler(execution_id, task_description, context or {})
            self._update_execution(execution_id, result.status, result.output, result.consensus_score, result.rounds)
            # Clear checkpoint on successful completion
            clear_checkpoint(self._db, f"raid-{execution_id}")
            success = result.status == "completed"
            return result
        except Exception:
            self._update_execution(execution_id, "failed", "", 0.0, 0)
            logger.exception("Raid %d failed: exec_id=%s", int(level), execution_id)
            raise
        finally:
            # Log execution for Meta-Harness optimization
            try:
                from services.raid_logger import log_raid_execution
                config = get_raid_level_config(level)
                elapsed_ms = int((time.monotonic() - t0) * 1000)
                log_raid_execution(
                    db=self._db,
                    task_id=task_id or execution_id,
                    task_type=task_type or "unknown",
                    raid_level=int(level),
                    config=config,
                    success=success,
                    quality_score=result.consensus_score if result else None,
                    consensus_score=result.consensus_score if result else None,
                    execution_time_ms=elapsed_ms,
                    cost_nau=None,
                )
            except Exception:
                pass  # Never block main flow

            # Bridge E.4: RAID result → Evolution Ledger (direct SQL, no proposal needed)
            if success and result:
                try:
                    from sqlalchemy import text as _sql
                    self._db.execute(_sql(
                        "INSERT INTO platform_evolution_log "
                        "(version_str, change_type, change_description, metric_delta, status, created_at) "
                        "VALUES (:ver, :ctype, :desc, :delta, 'active', NOW())"
                    ), {
                        "ver": f"raid-{execution_id[:8]}",
                        "ctype": f"raid_{int(level)}_verification",
                        "desc": f"RAID-{int(level)} consensus={result.consensus_score:.2f} rounds={result.rounds} task={task_id or 'unknown'}",
                        "delta": result.consensus_score,
                    })
                    self._db.commit()
                except Exception:
                    pass  # Never block main flow

    async def _raid_1(self, exec_id: str, description: str, ctx: Dict[str, Any]) -> RaidResult:
        """Execute + self-review."""
        ctx_str = self._format_context(ctx)
        solution = await self._llm_call(f"Task:\n{description}\n\n{ctx_str}\nProvide a complete solution.")
        self._save_vote(exec_id, "executor", 1, solution, None, None, None)
        review = await self._llm_call(
            f"Review the following solution and rate quality 0.0-1.0.\n\n"
            f"Task: {description}\n\nSolution:\n{solution}\n\n"
            "Respond ONLY with JSON: {\"score\": <float>, \"feedback\": \"<text>\"}"
        )
        score, feedback = self._parse_review(review)
        self._save_vote(exec_id, "reviewer", 1, review, score >= QUALITY_THRESHOLD, score, feedback)
        return RaidResult(
            execution_id=exec_id, raid_level=1, status="completed",
            output=solution, consensus_score=score, rounds=1,
            votes=[
                VoteInfo(role="executor", round_number=1, output=solution),
                VoteInfo(role="reviewer", round_number=1, quality_score=score, feedback=feedback),
            ],
        )

    async def _raid_2(self, exec_id: str, description: str, ctx: Dict[str, Any]) -> RaidResult:
        """Execute -> Review -> Improve, max 3 rounds.  Checkpoint after each round."""
        cp_key = f"raid-{exec_id}"
        cp = load_checkpoint(self._db, cp_key)
        cp_state = cp["state"] if cp else {}

        ctx_str = self._format_context(ctx)
        votes: List[VoteInfo] = [VoteInfo(**v) for v in cp_state.get("votes", [])]
        solution = cp_state.get("solution", "")
        score: float = cp_state.get("score", 0.0)
        feedback: str = cp_state.get("feedback", "")
        start_round: int = cp_state.get("next_round", 1)

        if start_round > 1:
            logger.info("Raid 2 %s resuming from round %d", exec_id, start_round)

        for rnd in range(start_round, MAX_ROUNDS_RAID2 + 1):
            if rnd == 1 and not solution:
                prompt = f"Task:\n{description}\n\n{ctx_str}\nProvide a complete solution."
            else:
                prompt = (
                    f"Task:\n{description}\n\n{ctx_str}\nPrevious solution:\n{solution}\n\n"
                    f"Reviewer feedback:\n{feedback}\n\nProvide an improved solution addressing all feedback."
                )
            solution = await self._llm_call(prompt)
            self._save_vote(exec_id, "executor", rnd, solution, None, None, None)
            votes.append(VoteInfo(role="executor", round_number=rnd, output=solution))
            review = await self._llm_call(
                f"Review the following solution and rate quality 0.0-1.0.\n\n"
                f"Task: {description}\n\nSolution:\n{solution}\n\n"
                "Respond ONLY with JSON: {\"score\": <float>, \"feedback\": \"<text>\"}"
            )
            score, feedback = self._parse_review(review)
            approved = score >= QUALITY_THRESHOLD
            self._save_vote(exec_id, "reviewer", rnd, review, approved, score, feedback)
            votes.append(VoteInfo(role="reviewer", round_number=rnd, approved=approved, quality_score=score, feedback=feedback))

            # Checkpoint after each completed round
            save_checkpoint(self._db, cp_key, f"raid2_round_{rnd}", {
                "solution": solution,
                "score": score,
                "feedback": feedback,
                "next_round": rnd + 1,
                "votes": [v.model_dump() for v in votes],
            }, execution_type="raid")

            if approved:
                logger.info("Raid 2 approved at round %d (score=%.2f)", rnd, score)
                break
        return RaidResult(
            execution_id=exec_id, raid_level=2, status="completed",
            output=solution, consensus_score=score, rounds=rnd, votes=votes,
        )

    async def _raid_3(self, exec_id: str, description: str, ctx: Dict[str, Any]) -> RaidResult:
        """3 sequential executions + judge picks best.  Checkpoint after each solution."""
        cp_key = f"raid-{exec_id}"
        cp = load_checkpoint(self._db, cp_key)
        cp_state = cp["state"] if cp else {}

        ctx_str = self._format_context(ctx)
        solutions: List[str] = cp_state.get("solutions", [])
        start_idx = len(solutions)

        if start_idx > 0:
            logger.info("Raid 3 %s resuming with %d/%d solutions", exec_id, start_idx, PARALLEL_COUNT)

        prompts = [
            f"Task:\n{description}\n\n{ctx_str}\nProvide a complete solution. (Attempt {i+1})"
            for i in range(PARALLEL_COUNT)
        ]
        for i in range(start_idx, PARALLEL_COUNT):
            sol = await self._llm_call(prompts[i])
            solutions.append(sol)
            # Checkpoint after each solution so we don't redo it on crash
            save_checkpoint(self._db, cp_key, f"raid3_solution_{i+1}", {
                "solutions": solutions,
            }, execution_type="raid")

        votes: List[VoteInfo] = []
        for i, sol in enumerate(solutions):
            self._save_vote(exec_id, "executor", i + 1, sol, None, None, None)
            votes.append(VoteInfo(role="executor", round_number=i + 1, output=sol))

        judge_prompt = (
            f"You are a judge. Given the task and 3 candidate solutions, pick the BEST one "
            f"and rate overall consensus 0.0-1.0.\n\nTask: {description}\n\n"
            + "\n\n".join(f"--- Solution {i+1} ---\n{s}" for i, s in enumerate(solutions))
            + "\n\nRespond ONLY with JSON: {\"best\": <1|2|3>, \"score\": <float>, \"reason\": \"<text>\"}"
        )
        judge_raw = await self._llm_call(judge_prompt)
        best_idx, consensus_score, reason = self._parse_judge(judge_raw, len(solutions))
        self._save_vote(exec_id, "voter", 1, judge_raw, True, consensus_score, reason)
        votes.append(VoteInfo(role="voter", round_number=1, quality_score=consensus_score, feedback=reason))
        return RaidResult(
            execution_id=exec_id, raid_level=3, status="completed",
            output=solutions[best_idx], consensus_score=consensus_score, rounds=1, votes=votes,
        )

    async def _raid_5(self, exec_id: str, description: str, ctx: Dict[str, Any]) -> RaidResult:
        """5 expert reviews + 4/5 consensus threshold."""
        ctx_str = self._format_context(ctx)
        solution = await self._llm_call(f"Task:\n{description}\n\n{ctx_str}\nProvide a complete, expert-level solution.")
        self._save_vote(exec_id, "executor", 1, solution, None, None, None)
        result = await self._run_expert_panel(exec_id, description, solution, 1)
        votes = [VoteInfo(role="executor", round_number=1, output=solution)] + result["votes"]
        if result["approved"]:
            return RaidResult(
                execution_id=exec_id, raid_level=5, status="completed",
                output=solution, consensus_score=result["avg_score"], rounds=1, votes=votes,
            )
        # One retry with merged feedback
        merged = "\n".join(f"Expert {i+1}: {v.feedback}" for i, v in enumerate(result["votes"]) if v.feedback)
        improved = await self._llm_call(
            f"Task:\n{description}\n\n{ctx_str}\nPrevious solution:\n{solution}\n\n"
            f"Expert feedback:\n{merged}\n\nProvide an improved solution addressing ALL expert concerns."
        )
        self._save_vote(exec_id, "executor", 2, improved, None, None, None)
        retry = await self._run_expert_panel(exec_id, description, improved, 2)
        votes.append(VoteInfo(role="executor", round_number=2, output=improved))
        votes.extend(retry["votes"])
        return RaidResult(
            execution_id=exec_id, raid_level=5, status="completed",
            output=improved, consensus_score=retry["avg_score"], rounds=2, votes=votes,
        )

    async def _run_expert_panel(self, exec_id: str, description: str, solution: str, rnd: int) -> Dict[str, Any]:
        """Run 5 expert reviews in parallel, return approval info."""
        perspectives = [
            "correctness and accuracy", "completeness and thoroughness",
            "clarity and readability", "efficiency and performance",
            "robustness and edge-case handling",
        ]
        coros = [
            self._llm_call(
                f"You are an expert reviewer focusing on {p}.\n\n"
                f"Task: {description}\n\nSolution:\n{solution}\n\n"
                "Rate quality 0.0-1.0 and decide approve/reject.\n"
                "Respond ONLY with JSON: {\"approved\": <bool>, \"score\": <float>, \"feedback\": \"<text>\"}"
            )
            for p in perspectives
        ]
        reviews = await asyncio.gather(*coros)
        votes: List[VoteInfo] = []
        approve_count, total_score = 0, 0.0
        for raw in reviews:
            approved, score, feedback = self._parse_expert(raw)
            self._save_vote(exec_id, "expert", rnd, raw, approved, score, feedback)
            votes.append(VoteInfo(role="expert", round_number=rnd, approved=approved, quality_score=score, feedback=feedback))
            approve_count += int(approved)
            total_score += score
        avg_score = total_score / EXPERT_COUNT
        logger.info("Expert panel round %d: %d/%d approved, avg=%.2f", rnd, approve_count, EXPERT_COUNT, avg_score)
        return {"approved": approve_count >= CONSENSUS_THRESHOLD, "avg_score": avg_score, "votes": votes}

    async def _llm_call(self, prompt: str, system: Optional[str] = None) -> str:
        """Non-blocking LLM call via thread pool, with retry on empty response."""
        for attempt in range(3):
            try:
                result = await asyncio.to_thread(
                    self.llm.chat, prompt=prompt,
                    system=system or "You are an expert AI assistant.",
                    temperature=0.3, max_tokens=4096,
                )
                if result and result.strip():
                    return result
                logger.warning("RAID LLM returned empty, retry %d/3", attempt + 1)
            except (ValueError, TypeError) as e:
                logger.warning("RAID LLM error on attempt %d/3: %s", attempt + 1, e)
            if attempt < 2:
                await asyncio.sleep(2 * (attempt + 1))  # backoff: 2s, 4s
        return "Analysis unavailable — LLM returned empty response after retries."

    # -- Parsing helpers --------------------------------------------------

    @staticmethod
    def _parse_review(raw: str) -> tuple[float, str]:
        try:
            data = json.loads(_extract_json(raw))
            return max(0.0, min(1.0, float(data.get("score", 0.5)))), str(data.get("feedback", ""))
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("Failed to parse review: %s", raw[:200])
            return 0.5, raw[:500]

    @staticmethod
    def _parse_judge(raw: str, count: int) -> tuple[int, float, str]:
        try:
            data = json.loads(_extract_json(raw))
            best = max(0, min(int(data.get("best", 1)) - 1, count - 1))
            return best, max(0.0, min(1.0, float(data.get("score", 0.5)))), str(data.get("reason", ""))
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("Failed to parse judge: %s", raw[:200])
            return 0, 0.5, raw[:500]

    @staticmethod
    def _parse_expert(raw: str) -> tuple[bool, float, str]:
        try:
            data = json.loads(_extract_json(raw))
            return bool(data.get("approved", False)), max(0.0, min(1.0, float(data.get("score", 0.5)))), str(data.get("feedback", ""))
        except (json.JSONDecodeError, ValueError, TypeError):
            logger.warning("Failed to parse expert review: %s", raw[:200])
            return False, 0.5, raw[:500]

    @staticmethod
    def _format_context(context: Dict[str, Any]) -> str:
        if not context:
            return ""
        return "Context:\n" + "\n".join(f"{k}: {v}" for k, v in context.items())

    # -- Database persistence ---------------------------------------------

    def _save_execution(self, exec_id: str, level: int, status: str, output: str, score: float, rounds: int) -> None:
        self._db.add(RaidExecution(
            execution_id=exec_id, task_id=exec_id, raid_level=level, status=status,
            num_agents=_agent_count_for_level(level), rounds_completed=rounds,
            final_output=output or None, consensus_score=score, created_at=datetime.utcnow(),
        ))
        self._db.commit()

    def _update_execution(self, exec_id: str, status: str, output: str, score: float, rounds: int) -> None:
        record = self._db.query(RaidExecution).filter(RaidExecution.execution_id == exec_id).first()
        if record:
            record.status = status
            record.final_output = output or None
            record.consensus_score = score
            record.rounds_completed = rounds
            record.completed_at = datetime.utcnow() if status in ("completed", "failed") else None
            self._db.commit()

    def _save_vote(self, exec_id: str, role: str, rnd: int, output: Optional[str],
                   approved: Optional[bool], score: Optional[float], feedback: Optional[str]) -> None:
        self._db.add(RaidVote(
            execution_id=exec_id, agent_role=role, round_number=rnd,
            output=output, approved=approved, quality_score=score,
            feedback=feedback, created_at=datetime.utcnow(),
        ))
        self._db.commit()


def _agent_count_for_level(level: int) -> int:
    params = get_engine_params(level)
    return params["agent_count"]


def _extract_json(text: str) -> str:
    """Extract the first JSON object from text that may contain markdown fences."""
    match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    return match.group(0) if match else text.strip()
