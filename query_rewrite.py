"""Gemini query-rewrite · opt-in recall enhancement (v2.3.0).

Rewrites a recall query before retrieval (expand abbreviations, add synonyms) to
lift recall on terse/ambiguous queries. ALL LLM contact is isolated here.

Activates ONLY when BOTH:
  · COMPASS_PROD_QUERY_REWRITE=1  (the query_rewrite opt-in flag), AND
  · COMPASS_USE_GEMINI_FLASH=1    (the gemini provider)
Default off → daemon recall is byte-identical, zero LLM (black-box-local hot
path preserved · honors judges/gemini_flash.py "NEVER call from default recall").

Robustness invariant: ANY failure (provider off, gemini None/empty/over-long,
exception) → return the ORIGINAL query. Recall is never broken or degraded.
"""
from __future__ import annotations

from typing import Optional

import llm_opt_in
from judges import gemini_flash

# one-line, low-temperature rewrite · the model gets only the transient query
_PROMPT = (
    "Rewrite this memory-search query to maximize retrieval recall: expand "
    "abbreviations, add 2-3 synonyms, keep it to ONE line. Return ONLY the "
    "rewritten query with no preamble or quotes.\n\nQuery: {query}"
)

# sanity cap · a rewrite far longer than the input is almost certainly the model
# rambling (preamble / explanation) → reject and fall back.
_MAX_OUT_CHARS = 600


def rewrite_query(query: str, judge: Optional[object] = None) -> str:
    """Return a rewritten query when opted in + gemini available, else `query`."""
    if not query or not query.strip():
        return query
    if not llm_opt_in.is_enabled(llm_opt_in.QUERY_REWRITE):
        return query
    if not gemini_flash.is_enabled():
        # provider not enabled → never silently require an LLM the user didn't turn on
        return query
    j = judge if judge is not None else gemini_flash.GeminiFlashJudge()
    try:
        out = j.generate(_PROMPT.format(query=query), max_tokens=120, temperature=0.1)
    except Exception:
        return query
    if not out or not out.strip():
        return query
    # take the first non-empty line, strip quotes/space
    first = out.strip().splitlines()[0].strip().strip('"').strip("'").strip()
    if not first or len(first) > _MAX_OUT_CHARS:
        return query
    return first
