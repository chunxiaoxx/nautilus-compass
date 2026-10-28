"""soul.council — multi-persona diverge + chairman converge.

The council operates at the proposal-description level: each persona produces
a NATURAL-LANGUAGE improvement description (what to change + why).  The
chairman picks the best one.  No code is emitted here.

generate_fn: Callable[[str, str], str]
    Injected LLM abstraction: generate_fn(prompt, system) -> str.
    Trivially mockable in tests; the daemon wires the real LLM client later.
"""

import re

PERSONAS = ("performance", "robustness", "readability", "correctness")

# ---------------------------------------------------------------------------
# Persona system prompts
# ---------------------------------------------------------------------------

_PERSONA_SYSTEMS: dict[str, str] = {
    "performance": (
        "You are a performance-focused code reviewer. "
        "Your lens: computational efficiency, algorithmic complexity, memory "
        "allocations, and unnecessary work. "
        "Given a module/task, output ONE concrete, safe, MINIMAL-CHANGE improvement "
        "description explaining what to change and why it improves performance. "
        "If nothing in your lens needs improvement, output exactly: NONE"
    ),
    "robustness": (
        "You are a robustness-focused code reviewer. "
        "Your lens: edge cases, error handling, input validation, and fault tolerance. "
        "Given a module/task, output ONE concrete, safe, MINIMAL-CHANGE improvement "
        "description explaining what to change and why it improves robustness. "
        "If nothing in your lens needs improvement, output exactly: NONE"
    ),
    "readability": (
        "You are a readability-focused code reviewer. "
        "Your lens: naming clarity, code structure, comments, and documentation. "
        "Given a module/task, output ONE concrete, safe, MINIMAL-CHANGE improvement "
        "description explaining what to change and why it improves readability. "
        "If nothing in your lens needs improvement, output exactly: NONE"
    ),
    "correctness": (
        "You are a correctness-focused code reviewer. "
        "Your lens: logical bugs, off-by-one errors, contract violations, and "
        "incorrect assumptions. "
        "Given a module/task, output ONE concrete, safe, MINIMAL-CHANGE improvement "
        "description explaining what to change and why it improves correctness. "
        "If nothing in your lens needs improvement, output exactly: NONE"
    ),
}

_CHAIRMAN_SYSTEM = (
    "You are the chairman of a code-improvement council. "
    "You receive an improvement task and a numbered list of proposals from "
    "different reviewers. Your job: select the single best proposal that is "
    "the most impactful, safe, and minimal change. "
    "Respond in EXACTLY this format (no extra text):\n"
    "INDEX: <0-based integer>\n"
    "SCORE: <integer 0-10>\n"
    "REASON: <one line explaining your choice>"
)


# ---------------------------------------------------------------------------
# propose
# ---------------------------------------------------------------------------

def propose(
    generate_fn,
    task: str,
    context: str,
    personas: tuple[str, ...] = PERSONAS,
) -> list[dict]:
    """Each persona calls generate_fn to produce a concrete improvement proposal.

    Returns [{"persona": str, "proposal": str, "raw": str}] — one per persona.
    Personas returning "NONE" are kept (not filtered); proposal field = "NONE".
    """
    prompt = (
        f"Task: {task}\n\n"
        f"Module context:\n{context}\n\n"
        "Provide ONE concrete improvement description from your reviewer perspective."
    )

    results = []
    for persona in personas:
        system = _PERSONA_SYSTEMS.get(
            persona,
            f"You are a {persona}-focused code reviewer. "
            "Output ONE concrete, safe, MINIMAL-CHANGE improvement description, "
            "or exactly NONE if nothing needs improvement.",
        )
        raw = generate_fn(prompt, system=system)
        if raw and raw.strip().upper() == "NONE":
            proposal = "NONE"
        else:
            proposal = raw.strip() if raw else "NONE"
        results.append({"persona": persona, "proposal": proposal, "raw": raw})
    return results


# ---------------------------------------------------------------------------
# converge
# ---------------------------------------------------------------------------

def converge(generate_fn, proposals: list[dict], task: str) -> dict:
    """Chairman scores and picks the best proposal.

    Returns the winning proposal dict augmented with {"score": float|int, "reason": str}.
    Fail-safe: if chairman output can't be parsed or index is out of range,
    returns proposals[0] augmented with score=0, reason="parse fallback: <raw>".
    Raises ValueError if proposals is empty.
    """
    if not proposals:
        raise ValueError("proposals list must not be empty")

    proposals = [p for p in proposals if p.get("proposal") != "NONE"]
    if not proposals:
        raise ValueError(
            "no actionable proposals to converge on: every persona returned NONE"
        )

    numbered = "\n".join(
        f"[{i}] ({p['persona']}) {p['proposal']}"
        for i, p in enumerate(proposals)
    )
    prompt = (
        f"Improvement task: {task}\n\n"
        f"Proposals:\n{numbered}\n\n"
        "Select the single best proposal using the required format."
    )

    raw = generate_fn(prompt, system=_CHAIRMAN_SYSTEM)
    index, score, reason = _parse_chairman(raw, len(proposals))

    winner = dict(proposals[index])
    winner["score"] = score
    winner["reason"] = reason
    return winner


# ---------------------------------------------------------------------------
# Internal parser
# ---------------------------------------------------------------------------

def _parse_chairman(raw: str, n_proposals: int) -> tuple:
    """Parse INDEX / SCORE / REASON from chairman output.

    Returns (index: int, score: float, reason: str).
    On any parse failure or out-of-range index, returns (0, 0, "parse fallback: <raw>").
    """
    fallback_reason = f"parse fallback: {raw[:120]}"

    idx_match = re.search(r"INDEX\s*:\s*(\d+)", raw, re.IGNORECASE)
    score_match = re.search(r"SCORE\s*:\s*([0-9]+(?:\.[0-9]+)?)", raw, re.IGNORECASE)
    reason_match = re.search(r"REASON\s*:\s*(.+)", raw, re.IGNORECASE)

    if not (idx_match and score_match and reason_match):
        return 0, 0, fallback_reason

    try:
        index = int(idx_match.group(1))
        score = float(score_match.group(1))
        reason = reason_match.group(1).strip()
    except (ValueError, AttributeError):
        return 0, 0, fallback_reason

    if index < 0 or index >= n_proposals:
        return 0, 0, fallback_reason

    return index, score, reason