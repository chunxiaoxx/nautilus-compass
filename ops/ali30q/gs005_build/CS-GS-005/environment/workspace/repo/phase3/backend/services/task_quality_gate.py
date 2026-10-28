"""
Task Quality Gate — DeerFlow-inspired output quality validation.

Scores task output on a 0-1 scale across three dimensions:
  - completeness: does the output address the task description?
  - coherence: is the output internally consistent and well-structured?
  - usefulness: is the output actionable/informative for the user?

Quality levels:
  >= 0.7  GOOD    — pass, append score to metadata
  0.4-0.7 FAIR   — pass with quality_warning flag
  < 0.4  POOR    — mark needs_review, no auto-retry (too expensive)
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

# Load .env if not already in environment (daemons don't auto-load .env)
if not os.getenv("GEMINI_API_KEY"):
    _env_path = Path(__file__).parent.parent / ".env"
    if _env_path.exists():
        for line in _env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip()
                if k and not os.getenv(k):
                    os.environ[k] = v

_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", os.getenv("GOOGLE_AI_API_KEY", ""))


def _score_output_sync(task_description: str, output: str) -> Dict:
    """Synchronous quality scoring via Gemini Flash — uses sync SDK directly."""
    desc_trunc = task_description[:500]
    out_trunc = output[:1500] if output else "(empty)"

    prompt = (
        "You are evaluating an AI agent's work on a coding/engineering task. "
        "The output is the agent's work log — it may contain tool calls (TOOL:), "
        "code snippets, file operations, search results, and natural language reasoning. "
        "Score based on whether the agent ACTUALLY DID useful engineering work, "
        "not whether the text reads like polished code.\n\n"
        "Scoring guide:\n"
        "- completeness: Did the agent address the task? (tool calls + results = high)\n"
        "- coherence: Is the work logical and well-structured?\n"
        "- usefulness: Did the agent produce real artifacts (files, code, data)?\n"
        "- If agent used tools and got results, score >= 0.6\n"
        "- If agent wrote/edited actual code files, score >= 0.7\n"
        "- If agent only talked without using tools, score <= 0.3\n\n"
        f"Task:\n{desc_trunc}\n\n"
        f"Agent work log:\n{out_trunc}\n\n"
        "Return ONLY valid JSON:\n"
        '{"completeness": 0.0, "coherence": 0.0, "usefulness": 0.0, "overall": 0.0}'
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=_GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=512,
                temperature=0.1,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = response.text or ""
        # Extract JSON if wrapped in markdown
        if "```" in raw:
            raw = raw.split("```")[1].lstrip("json").strip()
        scores = json.loads(raw)
        overall = scores.get("overall")
        if overall is None:
            dims = [scores.get("completeness", 0.5),
                    scores.get("coherence", 0.5),
                    scores.get("usefulness", 0.5)]
            overall = round(sum(dims) / len(dims), 3)
        scores["overall"] = round(float(overall), 3)
        return scores
    except Exception as exc:
        logger.debug("Quality gate scoring failed (non-critical): %s", exc)
        return {"overall": 0.5, "skipped": True, "reason": str(exc)[:100]}


async def score_task_output(task_description: str, output: str) -> Dict:
    """Async wrapper — runs sync Gemini call in thread pool."""
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        return await loop.run_in_executor(
            None, _score_output_sync, task_description, output
        )
    except Exception as exc:
        logger.debug("Quality gate async error: %s", exc)
        return {"overall": 0.5, "skipped": True, "reason": str(exc)[:100]}


# Note: Both sync and async fallbacks return overall=0.5 (FAIR) consistently.
# This means a quality gate failure is treated as "we don't know" rather than
# optimistic (0.7/GOOD) or pessimistic (0.3/POOR).


def interpret_quality(scores: Dict) -> Dict:
    """Convert raw scores into quality_level and flags."""
    overall = scores.get("overall", scores.get("score", 0.5))
    if overall >= 0.7:
        level = "GOOD"
        quality_warning = False
        needs_review = False
    elif overall >= 0.4:
        level = "FAIR"
        quality_warning = True
        needs_review = False
    else:
        level = "POOR"
        quality_warning = True
        needs_review = True

    return {
        "quality_level": level,
        "quality_score": overall,
        "quality_warning": quality_warning,
        "needs_review": needs_review,
        "dimensions": {
            k: scores[k]
            for k in ("completeness", "coherence", "usefulness")
            if k in scores
        },
    }
