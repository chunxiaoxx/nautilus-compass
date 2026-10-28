"""
DeerFlow Deep Research Service — v2 (DeerFlow-faithful architecture).

Pipeline (mirrors DeerFlow v1 node graph):
  Coordinator → Background Investigator → Planner → Research Team
  (Research Team dispatches Researchers in parallel) → Reporter

Key DeerFlow mechanisms applied:
- Coordinator: Pre-classifies topic, sets research strategy
- Background Investigator: Quick context before planning (like DeerFlow's search_before_planning)
- Structured Plan: Planner outputs Plan dataclass (list of Steps with execution_res)
- Observations blackboard: Accumulated findings from all Researchers, passed to Reporter
- Research Team dispatcher: Light routing — picks next unexecuted Step
"""
import asyncio
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# LLM helper
# ──────────────────────────────────────────────────────────────────────────────

def _call_llm_sync(system: str, user: str, max_tokens: int = 2048) -> str:
    """Synchronous LLM call via unified LLMClient (MiniMax/Anthropic)."""
    from agent_engine.llm.client import get_llm_client
    client = get_llm_client()
    return client.chat(prompt=user, system=system, max_tokens=max_tokens)


async def _call_haiku_async(system: str, user: str, max_tokens: int = 2048) -> str:
    """Run LLM call in thread pool (non-blocking)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _call_llm_sync, system, user, max_tokens)


# ──────────────────────────────────────────────────────────────────────────────
# DeerFlow State — shared blackboard across all nodes
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class ResearchStep:
    """Mirrors DeerFlow's Step dataclass."""
    title: str
    description: str          # The sub-question to answer
    execution_res: Optional[str] = None  # Written by Researcher


@dataclass
class ResearchState:
    """Shared state object — nodes read/write this (DeerFlow's State pattern)."""
    topic: str
    depth: str
    job_id: str
    background_context: str = ""        # Written by Background Investigator
    plan_steps: List[ResearchStep] = field(default_factory=list)  # Written by Planner
    observations: List[str] = field(default_factory=list)         # Accumulated by Researchers
    resources: List[str] = field(default_factory=list)            # Source references
    final_report: str = ""
    plan_iterations: int = 0


# ──────────────────────────────────────────────────────────────────────────────
# Web search helpers
# ──────────────────────────────────────────────────────────────────────────────

async def _ddgs_search(query: str, max_results: int = 6, timeout: float = 10.0) -> str:
    """Search the web via DuckDuckGo and return a formatted context string."""
    try:
        from ddgs import DDGS  # type: ignore
        loop = asyncio.get_event_loop()

        def _run_search():
            with DDGS() as d:
                return list(d.text(query, max_results=max_results))

        results = await asyncio.wait_for(
            loop.run_in_executor(None, _run_search),
            timeout=timeout,
        )
        if not results:
            return ""
        lines = [
            f"- {r.get('title', '')}: {r.get('body', '')[:300]}"
            for r in results
        ]
        ctx = f"Web search results for '{query}':\n" + "\n".join(lines)
        logger.info("[DeerFlow] DDGS search returned %d results for: %s", len(results), query[:60])
        return ctx
    except asyncio.TimeoutError:
        logger.warning("[DeerFlow] DDGS search timed out for: %s", query[:60])
        return ""
    except Exception as exc:
        logger.warning("[DeerFlow] DDGS search failed (degrading gracefully): %s", exc)
        return ""


async def _gemini_search(query: str) -> str:
    """Return Gemini-enhanced context for a query, or empty string on failure."""
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return ""
    try:
        from google import genai  # type: ignore
        client = genai.Client(api_key=gemini_key)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"Provide factual, concise information about: {query}",
            ),
        )
        return result.text or ""
    except Exception as exc:
        logger.warning("Gemini search failed (degrading gracefully): %s", exc)
        return ""


# ──────────────────────────────────────────────────────────────────────────────
# Node 1: Coordinator — pre-classify topic and set strategy
# ──────────────────────────────────────────────────────────────────────────────

async def _coordinate(state: ResearchState) -> None:
    """
    DeerFlow Coordinator node.
    Classifies topic and adjusts depth strategy.
    Mutates state in-place (like DeerFlow Command(update={...})).
    """
    system = (
        "You are a research coordinator. Classify the research topic and return JSON:\n"
        '{"domain": "<science|tech|business|policy|general>", '
        '"complexity": "<simple|moderate|complex>", '
        '"needs_data_analysis": true|false}'
    )
    user = f"Topic: {state.topic}"
    try:
        raw = await _call_haiku_async(system, user, max_tokens=128)
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        meta = json.loads(raw)
        # Upgrade depth for complex topics
        if meta.get("complexity") == "complex" and state.depth == "quick":
            state.depth = "standard"
            logger.info("[DeerFlow] Coordinator upgraded depth to 'standard' for complex topic")
        logger.info("[DeerFlow] Coordinator classified: %s", meta)
    except Exception as exc:
        logger.debug("[DeerFlow] Coordinator classification failed (non-critical): %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Node 2: Background Investigator — quick context before planning
# ──────────────────────────────────────────────────────────────────────────────

async def _background_investigate(state: ResearchState) -> None:
    """
    DeerFlow Background Investigator node (search_before_planning).
    Gathers quick context to inform the Planner.
    Priority: Gemini → DDGS → Haiku summary.
    """
    # 1. Try Gemini (if configured)
    gemini_ctx = await _gemini_search(state.topic)
    if gemini_ctx:
        state.background_context = gemini_ctx
        logger.info("[DeerFlow] Background Investigator: Gemini context gathered")
        return

    # 2. Try DuckDuckGo real-time search
    ddgs_ctx = await _ddgs_search(state.topic, max_results=5)
    if ddgs_ctx:
        state.background_context = ddgs_ctx
        logger.info("[DeerFlow] Background Investigator: DDGS context gathered")
        return

    # 3. Fallback: Haiku quick summary
    system = (
        "You are a background researcher. Provide a brief factual overview (3-5 sentences) "
        "of the given topic to inform research planning. Focus on key facts and context."
    )
    try:
        ctx = await _call_haiku_async(system, f"Topic: {state.topic}", max_tokens=256)
        state.background_context = ctx
        logger.info("[DeerFlow] Background Investigator: Haiku context gathered")
    except Exception as exc:
        logger.debug("[DeerFlow] Background Investigator failed (non-critical): %s", exc)


# ──────────────────────────────────────────────────────────────────────────────
# Node 3: Planner — structured Plan with Step objects
# ──────────────────────────────────────────────────────────────────────────────

async def _plan_node(state: ResearchState) -> None:
    """
    DeerFlow Planner node — outputs structured Plan (list of Steps).
    Injects background_context like DeerFlow's observations injection.
    """
    n_steps = {"quick": 3, "standard": 4, "thorough": 5}.get(state.depth, 4)
    bg = f"\n\nBackground context:\n{state.background_context}" if state.background_context else ""
    system = (
        f"You are a research planner. Decompose the topic into exactly {n_steps} focused sub-questions. "
        "Return ONLY valid JSON array: "
        '[{"title": "short title", "description": "the sub-question to investigate"}]'
    )
    user = f"Topic: {state.topic}{bg}"
    state.plan_iterations += 1
    logger.info("[DeerFlow] Planner started (iteration %d)", state.plan_iterations)

    raw = ""
    try:
        raw = await _call_haiku_async(system, user, max_tokens=768)
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        steps_data = json.loads(raw)
        state.plan_steps = [
            ResearchStep(title=s["title"], description=s["description"])
            for s in steps_data[:n_steps]
        ]
    except Exception as exc:
        logger.warning("[DeerFlow] Planner JSON parse failed, falling back: %s", exc)
        # Fallback: plain text parsing
        lines = [l.split(".", 1)[-1].strip() for l in raw.strip().splitlines()
                 if l.strip() and l.strip()[0].isdigit()]
        state.plan_steps = [
            ResearchStep(title=f"Step {i+1}", description=q)
            for i, q in enumerate(lines[:n_steps])
        ]
    if not state.plan_steps:
        state.plan_steps = [ResearchStep(title="Main Research", description=state.topic)]
    logger.info("[DeerFlow] Planner produced %d steps", len(state.plan_steps))


# ──────────────────────────────────────────────────────────────────────────────
# Node 4: Research Team (parallel Researchers) — writes to observations blackboard
# ──────────────────────────────────────────────────────────────────────────────

async def _execute_step(step: ResearchStep, background_ctx: str) -> str:
    """Single Researcher node: investigate one Step with optional real-time web search."""
    # Fetch up-to-date search results for this specific sub-question
    search_ctx = await _ddgs_search(step.description, max_results=4)

    extra_parts = []
    if background_ctx:
        extra_parts.append(f"General background:\n{background_ctx}")
    if search_ctx:
        extra_parts.append(f"Real-time web search results:\n{search_ctx}")

    extra = ("\n\n" + "\n\n".join(extra_parts)) if extra_parts else ""
    system = (
        "You are a thorough research analyst. Provide a detailed, evidence-based analysis. "
        "Use the provided web search results to ground your response in current, factual information. "
        "Structure: 1) Key findings, 2) Supporting details, 3) Limitations or caveats."
    )
    user = f"Sub-question: {step.description}{extra}"
    logger.debug("[DeerFlow] Researcher executing step: %s", step.title)
    return await _call_haiku_async(system, user, max_tokens=1024)


async def _research_team_node(state: ResearchState) -> None:
    """
    DeerFlow Research Team node — dispatches parallel Researchers.
    Writes execution_res into each Step AND accumulates to observations blackboard.
    Limits concurrency to 2 to avoid overloading the LLM API.
    """
    sem = asyncio.Semaphore(2)

    async def _bounded_step(step: ResearchStep) -> str:
        async with sem:
            return await _execute_step(step, state.background_context)

    tasks = [_bounded_step(step) for step in state.plan_steps]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for i, (step, result) in enumerate(zip(state.plan_steps, results)):
        if isinstance(result, Exception):
            logger.error("[DeerFlow] Researcher %d (%s) failed: %s", i, step.title, result)
            step.execution_res = f"Research failed: {result}"
        else:
            step.execution_res = result  # type: ignore[assignment]
            # Accumulate to observations blackboard (DeerFlow pattern)
            observation = f"## {step.title}\n**Question**: {step.description}\n\n{result}"
            state.observations.append(observation)

    logger.info("[DeerFlow] Research Team completed %d steps, %d observations accumulated",
                len(state.plan_steps), len(state.observations))


# ──────────────────────────────────────────────────────────────────────────────
# Node 5: Reporter — synthesises from observations blackboard
# ──────────────────────────────────────────────────────────────────────────────

async def _reporter_node(state: ResearchState) -> None:
    """
    DeerFlow Reporter node — reads from observations blackboard, not individual findings.
    This mirrors DeerFlow's reporter receiving accumulated observations.
    """
    observations_text = "\n\n---\n\n".join(state.observations)
    system = (
        "You are a senior research reporter. Synthesise the research observations "
        "into a professional report with three clearly labelled sections:\n"
        "SUMMARY: (2-3 sentence executive summary)\n"
        "FINDINGS: (bullet-point key insights, use - prefix)\n"
        "RECOMMENDATIONS: (numbered actionable next steps)"
    )
    user = f"Research Topic: {state.topic}\n\nResearch Observations:\n{observations_text}"
    logger.info("[DeerFlow] Reporter synthesising from %d observations", len(state.observations))
    state.final_report = await _call_haiku_async(system, user, max_tokens=2048)


def _parse_sections(report: str) -> Dict[str, str]:
    """Extract SUMMARY/FINDINGS/RECOMMENDATIONS sections — handles plain text and Markdown headers."""
    sections: Dict[str, str] = {"summary": "", "findings": "", "recommendations": ""}
    current: Optional[str] = None
    buffer: List[str] = []

    _SECTION_KEYS = {
        "SUMMARY": "summary",
        "FINDINGS": "findings",
        "RECOMMENDATIONS": "recommendations",
        "KEY FINDINGS": "findings",
        "RECOMMENDATION": "recommendations",
    }

    for line in report.splitlines():
        # Strip markdown heading markers and colon
        cleaned = line.strip().lstrip("#").strip().upper().rstrip(":")
        key = _SECTION_KEYS.get(cleaned)
        if key:
            if current and buffer:
                sections[current] = "\n".join(buffer).strip()
            current = key
            buffer = []
        else:
            buffer.append(line)
    if current and buffer:
        sections[current] = "\n".join(buffer).strip()
    return sections


# ──────────────────────────────────────────────────────────────────────────────
# Google Docs export (optional)
# ──────────────────────────────────────────────────────────────────────────────

async def _save_to_gdoc(topic: str, report_text: str) -> Optional[str]:
    """Write report to Google Docs; return URL or None on failure."""
    try:
        from services.google_ai import get_workspace_client
        loop = asyncio.get_event_loop()
        ws = await loop.run_in_executor(None, get_workspace_client)
        title = f"Deep Research: {topic[:60]}"
        result = await loop.run_in_executor(None, ws.create_doc, title, report_text)
        url = result.get("url") or result.get("webViewLink")
        logger.info("[DeerFlow] Report saved to Google Docs: %s", url)
        return url
    except Exception as exc:
        logger.warning("[DeerFlow] Google Docs export failed (degrading): %s", exc)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────────────────────────────────────

class DeepResearchPipeline:
    """
    Orchestrates the full DeerFlow v1-faithful research pipeline.

    Node graph:
      Coordinator → Background Investigator → Planner → Research Team → Reporter
    """

    async def run(
        self,
        topic: str,
        depth: str = "standard",
        save_to_gdoc: bool = False,
    ) -> Dict:
        """
        Execute the pipeline using shared ResearchState (observations blackboard).

        Returns a dict with:
          - report: full text report
          - sections: {summary, findings, recommendations}
          - sub_questions: list of step descriptions
          - plan_steps: full step objects with execution_res
          - observations: accumulated blackboard entries
          - gdoc_url: Google Doc URL if requested
          - duration_seconds: total elapsed time
        """
        start = time.time()
        job_id = str(uuid.uuid4())
        logger.info("[DeerFlow] Job %s started — topic=%r depth=%s", job_id, topic, depth)

        # Initialise shared state (DeerFlow's State object)
        state = ResearchState(topic=topic, depth=depth, job_id=job_id)

        try:
            # Node 1: Coordinator — classify + strategy
            await _coordinate(state)

            # Node 2: Background Investigator — pre-search context
            await _background_investigate(state)

            # Node 3: Planner — structured Plan with Steps
            await _plan_node(state)

            # Node 4: Research Team — parallel Researchers → observations blackboard
            await _research_team_node(state)

            # Node 5: Reporter — synthesise from observations
            await _reporter_node(state)

        except Exception as exc:
            logger.error("[DeerFlow] Pipeline error for job %s: %s", job_id, exc)
            raise

        gdoc_url: Optional[str] = None
        if save_to_gdoc:
            gdoc_url = await _save_to_gdoc(topic, state.final_report)

        duration = round(time.time() - start, 2)
        sections = _parse_sections(state.final_report)
        logger.info(
            "[DeerFlow] Job %s completed in %.1fs (%d steps, %d observations)",
            job_id, duration, len(state.plan_steps), len(state.observations),
        )

        return {
            "job_id": job_id,
            "topic": topic,
            "depth": state.depth,  # May have been upgraded by Coordinator
            "report": state.final_report,
            "sections": sections,
            "sub_questions": [s.description for s in state.plan_steps],
            "plan_steps": [
                {"title": s.title, "description": s.description, "result_preview": (s.execution_res or "")[:200]}
                for s in state.plan_steps
            ],
            "observations_count": len(state.observations),
            "gdoc_url": gdoc_url,
            "duration_seconds": duration,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Singleton
# ──────────────────────────────────────────────────────────────────────────────

_pipeline: Optional[DeepResearchPipeline] = None


def get_deep_research() -> DeepResearchPipeline:
    """Return the global DeepResearchPipeline singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = DeepResearchPipeline()
    return _pipeline
